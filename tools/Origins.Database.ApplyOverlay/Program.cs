using System.Text.Json;
using System.Text.Json.Nodes;
using Origins.Database.Snapshots;

if (args.Length < 3)
{
    Console.Error.WriteLine("Usage: Origins.Database.ApplyOverlay <snapshot-root> <overlay-root> <output-root> [index-policy]");
    return 64;
}

var snapshotRoot = Path.GetFullPath(args[0]);
var overlayRoot = Path.GetFullPath(args[1]);
var outputRoot = Path.GetFullPath(args[2]);
var policyPath = args.Length > 3
    ? Path.GetFullPath(args[3])
    : Path.Combine(Directory.GetParent(overlayRoot)?.FullName ?? overlayRoot, "index-policy.json");
var sourceManifestPath = Path.Combine(snapshotRoot, "manifest.json");

var jsonOptions = new JsonSerializerOptions
{
    PropertyNameCaseInsensitive = true,
    WriteIndented = true
};

if (!File.Exists(sourceManifestPath))
{
    Console.Error.WriteLine($"Snapshot manifest not found: {sourceManifestPath}");
    return 66;
}

if (!Directory.Exists(overlayRoot))
{
    Console.Error.WriteLine($"Overlay directory not found: {overlayRoot}");
    return 66;
}

if (!File.Exists(policyPath))
{
    Console.Error.WriteLine($"ORIGINS index policy not found: {policyPath}");
    return 66;
}

if (Directory.Exists(outputRoot) && Directory.EnumerateFileSystemEntries(outputRoot).Any())
{
    Console.Error.WriteLine($"Refusing to overwrite non-empty output directory: {outputRoot}");
    return 65;
}

Directory.CreateDirectory(outputRoot);
CopyDirectory(snapshotRoot, outputRoot);

try
{
    var manifestPath = Path.Combine(outputRoot, "manifest.json");
    var manifest = JsonSerializer.Deserialize<SystemSnapshotManifest>(File.ReadAllText(manifestPath), jsonOptions)
        ?? throw new InvalidOperationException("Could not deserialize snapshot manifest.");

    if (manifest.SchemaVersion != 1)
        throw new InvalidOperationException($"Unsupported snapshot schema version {manifest.SchemaVersion}.");

    var policy = JsonSerializer.Deserialize<OriginsIndexPolicy>(File.ReadAllText(policyPath), jsonOptions)
        ?? throw new InvalidOperationException("Could not deserialize ORIGINS index policy.");

    if (policy.SchemaVersion != 1)
        throw new InvalidOperationException($"Unsupported index policy schema version {policy.SchemaVersion}.");

    var entries = manifest.Collections.ToDictionary(
        x => TypeKey(x.AssemblyName, x.TypeName),
        StringComparer.Ordinal);

    var ranges = policy.Ranges.ToDictionary(
        x => TypeKey(x.AssemblyName, x.TypeName),
        StringComparer.Ordinal);

    foreach (var range in policy.Ranges)
    {
        var key = TypeKey(range.AssemblyName, range.TypeName);
        if (!entries.TryGetValue(key, out var entry))
            throw new InvalidOperationException($"Index policy targets unknown snapshot type {key}.");

        if (entry.CollectionIndex != range.LegacyCollectionIndex)
            throw new InvalidOperationException(
                $"Index policy drift for {range.TypeName}: snapshot collection index {entry.CollectionIndex} != locked legacy index {range.LegacyCollectionIndex}. Review the new upstream database before allocating ORIGINS rows.");

        if (range.OriginsStart <= range.LegacyCollectionIndex)
            throw new InvalidOperationException(
                $"Invalid ORIGINS start for {range.TypeName}: {range.OriginsStart} must be above legacy index {range.LegacyCollectionIndex}.");
    }

    var states = new Dictionary<string, CollectionState>(StringComparer.Ordinal);
    var appliedFiles = new List<string>();
    var operationCount = 0;
    var createdCount = 0;
    var updatedCount = 0;
    var deletedCount = 0;

    foreach (var overlayFile in Directory.EnumerateFiles(overlayRoot, "*.json", SearchOption.TopDirectoryOnly)
                 .OrderBy(x => Path.GetFileName(x), StringComparer.Ordinal))
    {
        var overlay = JsonSerializer.Deserialize<SystemSnapshotOverlay>(File.ReadAllText(overlayFile), jsonOptions)
            ?? throw new InvalidOperationException($"Could not deserialize overlay {overlayFile}.");

        if (overlay.SchemaVersion != 1)
            throw new InvalidOperationException($"Overlay {Path.GetFileName(overlayFile)} uses unsupported schema version {overlay.SchemaVersion}.");

        foreach (var operation in overlay.Operations)
        {
            Apply(operation, Path.GetFileName(overlayFile));
            operationCount++;
        }

        appliedFiles.Add(Path.GetFileName(overlayFile));
    }

    foreach (var state in states.Values)
    {
        var orderedRows = state.Rows
            .Select(node => node as JsonObject ?? throw new InvalidOperationException($"{state.Entry.TypeName}: row is not an object."))
            .OrderBy(GetIndex)
            .Select(node => node.DeepClone())
            .ToArray();

        var sorted = new JsonArray(orderedRows);
        File.WriteAllText(
            Path.Combine(outputRoot, state.Entry.FileName),
            sorted.ToJsonString(jsonOptions));
    }

    File.WriteAllText(manifestPath, JsonSerializer.Serialize(manifest, jsonOptions));

    var report = new
    {
        schemaVersion = 1,
        baseSystemDbSha256 = manifest.SourceSystemDbSha256,
        baseSystemVersion = manifest.SourceSystemVersion,
        indexPolicy = policyPath,
        overlays = appliedFiles,
        operationCount,
        createdCount,
        updatedCount,
        deletedCount,
        completedUtc = DateTime.UtcNow
    };

    File.WriteAllText(
        Path.Combine(outputRoot, "overlay-report.json"),
        JsonSerializer.Serialize(report, jsonOptions));

    Console.WriteLine($"ORIGINS SNAPSHOT OVERLAY: PASS ({appliedFiles.Count} files, {operationCount} operations; {createdCount} created, {updatedCount} updated, {deletedCount} deleted)");
    return 0;

    void Apply(SystemSnapshotOperation operation, string overlayName)
    {
        if (operation.Index <= 0)
            throw new InvalidOperationException($"{operation.TypeName}: overlay index must be greater than zero.");

        var key = TypeKey(operation.AssemblyName, operation.TypeName);
        if (!entries.TryGetValue(key, out var entry))
            throw new InvalidOperationException($"Overlay targets unknown snapshot type {key}.");

        var state = GetState(key, entry);
        var row = state.Rows
            .Select(node => node as JsonObject)
            .FirstOrDefault(node => node != null && GetIndex(node) == operation.Index);

        switch (operation.Action.Trim().ToLowerInvariant())
        {
            case "delete":
                if (row == null)
                    throw new InvalidOperationException($"Cannot delete missing {operation.TypeName} index {operation.Index}.");

                state.Rows.Remove(row);
                entry.Count--;
                deletedCount++;
                return;

            case "upsert":
                if (row == null)
                {
                    if (!ranges.TryGetValue(key, out var range))
                        throw new InvalidOperationException(
                            $"{overlayName}: cannot create {operation.TypeName} index {operation.Index}; no ORIGINS index range is reserved for this collection.");

                    if (operation.Index < range.OriginsStart)
                        throw new InvalidOperationException(
                            $"{overlayName}: refusing to fill legacy gap {operation.TypeName}#{operation.Index}. New ORIGINS rows must start at {range.OriginsStart}.");

                    row = new JsonObject
                    {
                        ["Index"] = operation.Index,
                        ["$assembly"] = operation.AssemblyName,
                        ["$type"] = operation.TypeName
                    };
                    state.Rows.Add(row);
                    entry.Count++;
                    entry.CollectionIndex = Math.Max(entry.CollectionIndex, operation.Index);
                    createdCount++;
                }
                else
                {
                    updatedCount++;
                }

                foreach (var pair in operation.Set)
                {
                    if (pair.Key is "Index" or "$assembly" or "$type")
                        throw new InvalidOperationException($"Overlay cannot replace reserved field {pair.Key}.");

                    row[pair.Key] = JsonNode.Parse(pair.Value.GetRawText());
                }
                return;

            default:
                throw new InvalidOperationException($"Unsupported overlay action '{operation.Action}'. Use upsert or delete.");
        }
    }

    CollectionState GetState(string key, SystemSnapshotCollection entry)
    {
        if (states.TryGetValue(key, out var existing))
            return existing;

        var path = Path.Combine(outputRoot, entry.FileName);
        var rows = JsonNode.Parse(File.ReadAllText(path)) as JsonArray
            ?? throw new InvalidOperationException($"Snapshot collection {entry.FileName} is not a JSON array.");

        var state = new CollectionState(entry, rows);
        states[key] = state;
        return state;
    }
}
catch (Exception ex)
{
    Console.Error.WriteLine("ORIGINS SNAPSHOT OVERLAY: ERROR");
    Console.Error.WriteLine(ex);
    return 1;
}

string TypeKey(string assemblyName, string typeName) => $"{assemblyName}|{typeName}";

int GetIndex(JsonObject row)
{
    if (row["Index"] == null)
        throw new InvalidOperationException("Snapshot row is missing Index.");

    return row["Index"]!.GetValue<int>();
}

void CopyDirectory(string sourceRoot, string destinationRoot)
{
    foreach (var directory in Directory.EnumerateDirectories(sourceRoot, "*", SearchOption.AllDirectories))
    {
        var relative = Path.GetRelativePath(sourceRoot, directory);
        Directory.CreateDirectory(Path.Combine(destinationRoot, relative));
    }

    foreach (var file in Directory.EnumerateFiles(sourceRoot, "*", SearchOption.AllDirectories))
    {
        var relative = Path.GetRelativePath(sourceRoot, file);
        var destination = Path.Combine(destinationRoot, relative);
        Directory.CreateDirectory(Path.GetDirectoryName(destination)!);
        File.Copy(file, destination, overwrite: true);
    }
}

sealed class CollectionState
{
    public SystemSnapshotCollection Entry { get; }
    public JsonArray Rows { get; }

    public CollectionState(SystemSnapshotCollection entry, JsonArray rows)
    {
        Entry = entry;
        Rows = rows;
    }
}
