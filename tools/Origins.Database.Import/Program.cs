using System.Collections;
using System.Reflection;
using System.Text.Json;
using Library.SystemModels;
using MirDB;
using Origins.Database.Runtime;
using Origins.Database.Snapshots;
using Server.DBModels;

if (args.Length < 2)
{
    Console.Error.WriteLine("Usage: Origins.Database.Import <snapshot-root> <output-database-root> [backup-root]");
    return 64;
}

var snapshotRoot = Path.GetFullPath(args[0]);
var outputRoot = Path.GetFullPath(args[1]);
var backupRoot = args.Length > 2 ? Path.GetFullPath(args[2]) : Path.Combine(outputRoot, "Backup");
var manifestPath = Path.Combine(snapshotRoot, "manifest.json");
var targetSystemDb = Path.Combine(outputRoot, "System.db");

var jsonOptions = new JsonSerializerOptions
{
    PropertyNameCaseInsensitive = true,
    WriteIndented = true
};

if (!File.Exists(manifestPath))
{
    Console.Error.WriteLine($"Snapshot manifest not found: {manifestPath}");
    return 66;
}

if (File.Exists(targetSystemDb))
{
    Console.Error.WriteLine($"Refusing to overwrite existing System.db: {targetSystemDb}");
    return 65;
}

Directory.CreateDirectory(outputRoot);
Directory.CreateDirectory(backupRoot);

try
{
    var manifest = JsonSerializer.Deserialize<SystemSnapshotManifest>(File.ReadAllText(manifestPath), jsonOptions)
        ?? throw new InvalidOperationException("Could not deserialize snapshot manifest.");

    if (manifest.SchemaVersion != 1)
        throw new InvalidOperationException($"Unsupported snapshot schema version {manifest.SchemaVersion}.");

    var assemblies = new[] { typeof(ItemInfo).Assembly, typeof(AccountInfo).Assembly };
    var typeMap = assemblies
        .SelectMany(x => x.GetTypes())
        .Where(x => x.IsSubclassOf(typeof(DBObject)))
        .Where(x => !x.IsAbstract)
        .ToDictionary(TypeKeyFromType, StringComparer.Ordinal);

    var session = ZirconDatabaseRuntime.OpenSystemWriter(outputRoot, backupRoot);
    var objectMap = new Dictionary<ObjectKey, DBObject>();
    var loadedCollections = new List<LoadedCollection>();

    // Pass 1: create every object with its exact original Index. No references
    // are assigned yet, so creation order between collections does not matter.
    foreach (var entry in manifest.Collections)
    {
        var typeKey = BuildTypeKey(entry.AssemblyName, entry.TypeName);
        if (!typeMap.TryGetValue(typeKey, out var type))
            throw new InvalidOperationException($"Snapshot type is not present in pinned Zircon assemblies: {typeKey}");

        var filePath = Path.Combine(snapshotRoot, entry.FileName);
        if (!File.Exists(filePath))
            throw new FileNotFoundException($"Snapshot collection file is missing: {entry.FileName}", filePath);

        var rows = JsonSerializer.Deserialize<List<Dictionary<string, JsonElement>>>(File.ReadAllText(filePath), jsonOptions)
            ?? new List<Dictionary<string, JsonElement>>();

        if (rows.Count != entry.Count)
            throw new InvalidOperationException($"{entry.TypeName}: manifest count {entry.Count} != file count {rows.Count}.");

        rows.Sort((a, b) => GetIndex(a).CompareTo(GetIndex(b)));

        var collection = session.GetCollection(type);
        var collectionType = collection.GetType();
        var indexProperty = collectionType.GetProperty("Index", BindingFlags.Public | BindingFlags.Instance)
            ?? throw new InvalidOperationException($"Collection Index property not found for {entry.TypeName}.");
        var createMethod = collectionType.GetMethod("CreateNewObject", BindingFlags.Public | BindingFlags.Instance)
            ?? throw new InvalidOperationException($"CreateNewObject method not found for {entry.TypeName}.");

        var expectedIndices = new List<int>(rows.Count);
        foreach (var row in rows)
        {
            var desiredIndex = GetIndex(row);
            if (desiredIndex <= 0)
                throw new InvalidOperationException($"{entry.TypeName}: invalid object index {desiredIndex}.");

            indexProperty.SetValue(collection, desiredIndex - 1);
            var created = (DBObject)(createMethod.Invoke(collection, null)
                ?? throw new InvalidOperationException($"Could not create {entry.TypeName} index {desiredIndex}."));

            if (created.Index != desiredIndex)
                throw new InvalidOperationException($"{entry.TypeName}: expected index {desiredIndex}, created {created.Index}.");

            var key = new ObjectKey(entry.AssemblyName, entry.TypeName, desiredIndex);
            if (!objectMap.TryAdd(key, created))
                throw new InvalidOperationException($"Duplicate snapshot object {key}.");

            expectedIndices.Add(desiredIndex);
        }

        var currentIndex = (int)(indexProperty.GetValue(collection) ?? 0);
        indexProperty.SetValue(collection, Math.Max(currentIndex, entry.CollectionIndex));

        loadedCollections.Add(new LoadedCollection(entry, type, rows, expectedIndices));
    }

    // Pass 2: apply scalar values and DBObject references. Zircon's own
    // OnChanged/CreateLink machinery rebuilds reverse DBBindingList associations.
    foreach (var loaded in loadedCollections)
    {
        foreach (var row in loaded.Rows)
        {
            var index = GetIndex(row);
            var key = new ObjectKey(loaded.Entry.AssemblyName, loaded.Entry.TypeName, index);
            var target = objectMap[key];

            foreach (var pair in row)
            {
                if (pair.Key is "Index" or "$assembly" or "$type")
                    continue;

                var property = loaded.Type.GetProperty(pair.Key, BindingFlags.Public | BindingFlags.Instance);
                if (property == null)
                    throw new InvalidOperationException($"{loaded.Entry.TypeName}.{pair.Key}: property not found in pinned Zircon model.");

                if (!property.CanWrite || property.GetIndexParameters().Length != 0)
                    continue;

                if (property.GetCustomAttribute<IgnorePropertyAttribute>() != null)
                    continue;

                if (IsBindingList(property.PropertyType))
                    continue;

                var element = pair.Value;

                if (element.ValueKind == JsonValueKind.Null)
                {
                    if (!property.PropertyType.IsValueType || Nullable.GetUnderlyingType(property.PropertyType) != null)
                        property.SetValue(target, null);
                    continue;
                }

                if (typeof(DBObject).IsAssignableFrom(property.PropertyType))
                {
                    if (element.ValueKind != JsonValueKind.Object ||
                        !element.TryGetProperty("$refAssembly", out var refAssemblyElement) ||
                        !element.TryGetProperty("$refType", out var refTypeElement) ||
                        !element.TryGetProperty("Index", out var refIndexElement))
                    {
                        throw new InvalidOperationException($"{loaded.Entry.TypeName}[{index}].{pair.Key}: invalid DBObject reference.");
                    }

                    var refKey = new ObjectKey(
                        refAssemblyElement.GetString() ?? string.Empty,
                        refTypeElement.GetString() ?? string.Empty,
                        refIndexElement.GetInt32());

                    if (!objectMap.TryGetValue(refKey, out var referenced))
                        throw new InvalidOperationException($"{loaded.Entry.TypeName}[{index}].{pair.Key}: unresolved reference {refKey}.");

                    property.SetValue(target, referenced);
                    continue;
                }

                object? value;
                try
                {
                    value = ZirconValueCodec.Decode(element, property.PropertyType);
                }
                catch (Exception ex)
                {
                    throw new InvalidOperationException(
                        $"{loaded.Entry.TypeName}[{index}].{pair.Key}: cannot decode {property.PropertyType.FullName}.", ex);
                }

                property.SetValue(target, value);
            }
        }
    }

    session.Save(commit: true);

    // Reopen the written database to prove the file itself can be consumed by
    // the pinned Zircon mapping and that no indices/collection counts drifted.
    var verifySession = ZirconDatabaseRuntime.OpenSystemWriter(outputRoot, backupRoot);
    var preflight = ZirconDatabasePreflight.Validate(verifySession);
    var validationErrors = new List<string>(preflight.Errors);

    foreach (var loaded in loadedCollections)
    {
        var collection = verifySession.GetCollection(loaded.Type);
        var collectionType = collection.GetType();
        var bindingField = collectionType.GetField("Binding", BindingFlags.Public | BindingFlags.Instance)
            ?? throw new InvalidOperationException($"Binding field not found for {loaded.Entry.TypeName}.");
        var indexProperty = collectionType.GetProperty("Index", BindingFlags.Public | BindingFlags.Instance)
            ?? throw new InvalidOperationException($"Collection Index property not found for {loaded.Entry.TypeName}.");

        var actualIndices = ((IEnumerable)(bindingField.GetValue(collection)
            ?? throw new InvalidOperationException($"Binding is null for {loaded.Entry.TypeName}.")))
            .Cast<DBObject>()
            .Select(x => x.Index)
            .OrderBy(x => x)
            .ToList();

        if (!loaded.ExpectedIndices.SequenceEqual(actualIndices))
            validationErrors.Add($"{loaded.Entry.TypeName}: object indices changed during round-trip.");

        var actualCollectionIndex = (int)(indexProperty.GetValue(collection) ?? 0);
        if (actualCollectionIndex != loaded.Entry.CollectionIndex)
            validationErrors.Add($"{loaded.Entry.TypeName}: collection index {actualCollectionIndex} != expected {loaded.Entry.CollectionIndex}.");
    }

    var report = new
    {
        schemaVersion = 1,
        success = validationErrors.Count == 0,
        sourceSnapshotSha256 = manifest.SourceSystemDbSha256,
        sourceSystemVersion = manifest.SourceSystemVersion,
        outputSystemVersion = verifySession.SystemDatabaseVersion,
        collectionCount = loadedCollections.Count,
        objectCount = loadedCollections.Sum(x => x.Rows.Count),
        errors = validationErrors,
        completedUtc = DateTime.UtcNow
    };

    File.WriteAllText(
        Path.Combine(outputRoot, "import-report.json"),
        JsonSerializer.Serialize(report, jsonOptions));

    if (validationErrors.Count > 0)
    {
        Console.Error.WriteLine("ORIGINS SYSTEM.DB IMPORT: FAIL");
        foreach (var error in validationErrors)
            Console.Error.WriteLine($"- {error}");
        return 3;
    }

    Console.WriteLine($"ORIGINS SYSTEM.DB IMPORT: PASS ({loadedCollections.Count} collections, {loadedCollections.Sum(x => x.Rows.Count)} objects)");
    Console.WriteLine($"System version: {verifySession.SystemDatabaseVersion ?? "<none>"}");
    return 0;
}
catch (Exception ex)
{
    Console.Error.WriteLine("ORIGINS SYSTEM.DB IMPORT: ERROR");
    Console.Error.WriteLine(ex);
    return 1;
}

int GetIndex(Dictionary<string, JsonElement> row)
{
    if (!row.TryGetValue("Index", out var indexElement))
        throw new InvalidOperationException("Snapshot row is missing Index.");

    return indexElement.GetInt32();
}

bool IsBindingList(Type type)
{
    return type.IsGenericType && type.GetGenericTypeDefinition() == typeof(DBBindingList<>);
}

string TypeKeyFromType(Type type) => BuildTypeKey(type.Assembly.GetName().Name ?? string.Empty, type.FullName ?? type.Name);
string BuildTypeKey(string assemblyName, string typeName) => $"{assemblyName}|{typeName}";

readonly record struct ObjectKey(string AssemblyName, string TypeName, int Index)
{
    public override string ToString() => $"{AssemblyName}:{TypeName}#{Index}";
}

sealed class LoadedCollection
{
    public SystemSnapshotCollection Entry { get; }
    public Type Type { get; }
    public List<Dictionary<string, JsonElement>> Rows { get; }
    public List<int> ExpectedIndices { get; }

    public LoadedCollection(
        SystemSnapshotCollection entry,
        Type type,
        List<Dictionary<string, JsonElement>> rows,
        List<int> expectedIndices)
    {
        Entry = entry;
        Type = type;
        Rows = rows;
        ExpectedIndices = expectedIndices;
    }
}
