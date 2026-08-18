using System.Collections;
using System.Reflection;
using System.Text.Json;
using Library.SystemModels;
using MirDB;
using Origins.Database.Runtime;
using Server.DBModels;

if (args.Length < 2)
{
    Console.Error.WriteLine("Usage: Origins.Database.Audit <database-root> <report-file> [backup-root]");
    return 64;
}

var databaseRoot = Path.GetFullPath(args[0]);
var reportFile = Path.GetFullPath(args[1]);
var backupRoot = args.Length > 2 ? Path.GetFullPath(args[2]) : Path.Combine(databaseRoot, "Backup");

try
{
    var session = ZirconDatabaseRuntime.OpenSystemWriter(databaseRoot, backupRoot);
    var assemblies = new[] { typeof(ItemInfo).Assembly, typeof(AccountInfo).Assembly };

    var systemTypes = assemblies
        .SelectMany(x => x.GetTypes())
        .Where(x => x.IsSubclassOf(typeof(DBObject)))
        .Where(x => !x.IsAbstract)
        .Where(x => x.GetCustomAttribute<UserObjectAttribute>() == null)
        .Distinct()
        .OrderBy(x => x.Assembly.GetName().Name, StringComparer.Ordinal)
        .ThenBy(x => x.FullName, StringComparer.Ordinal)
        .ToList();

    var collections = new List<CollectionAudit>();

    foreach (var type in systemTypes)
    {
        var collection = session.GetCollection(type);
        var collectionType = collection.GetType();
        var bindingField = collectionType.GetField("Binding", BindingFlags.Public | BindingFlags.Instance)
            ?? throw new InvalidOperationException($"Binding field not found for {type.FullName}.");
        var collectionIndexProperty = collectionType.GetProperty("Index", BindingFlags.Public | BindingFlags.Instance)
            ?? throw new InvalidOperationException($"Index property not found for {type.FullName}.");

        var indices = ((IEnumerable)(bindingField.GetValue(collection)
            ?? throw new InvalidOperationException($"Binding is null for {type.FullName}.")))
            .Cast<DBObject>()
            .Select(x => x.Index)
            .OrderBy(x => x)
            .ToList();

        var collectionIndex = (int)(collectionIndexProperty.GetValue(collection) ?? 0);
        var holes = FindHoles(indices, collectionIndex, 200);

        collections.Add(new CollectionAudit
        {
            Assembly = type.Assembly.GetName().Name ?? string.Empty,
            Type = type.FullName ?? type.Name,
            Count = indices.Count,
            CollectionIndex = collectionIndex,
            HighestExistingIndex = indices.Count == 0 ? 0 : indices[^1],
            MissingIndexCount = Math.Max(0, collectionIndex - indices.Count),
            FirstMissingIndices = holes
        });
    }

    var preflight = ZirconDatabasePreflight.Validate(session);
    var report = new DatabaseAudit
    {
        SchemaVersion = 1,
        DatabaseRoot = databaseRoot,
        SystemDatabaseExists = session.SystemDatabaseExists,
        SystemVersion = session.SystemDatabaseVersion,
        PreflightReady = preflight.Ready,
        PreflightErrors = preflight.Errors.ToList(),
        CollectionCount = collections.Count,
        NonEmptyCollectionCount = collections.Count(x => x.Count > 0),
        EmptyCollectionCount = collections.Count(x => x.Count == 0),
        TotalObjects = collections.Sum(x => x.Count),
        Collections = collections,
        EmptyCollections = collections.Where(x => x.Count == 0).Select(x => x.Type).ToList(),
        AuditedUtc = DateTime.UtcNow
    };

    Directory.CreateDirectory(Path.GetDirectoryName(reportFile)!);
    File.WriteAllText(
        reportFile,
        JsonSerializer.Serialize(report, new JsonSerializerOptions { WriteIndented = true }));

    Console.WriteLine($"ORIGINS DATABASE AUDIT: {(preflight.Ready ? "PASS" : "INCOMPLETE")}");
    Console.WriteLine($"System version: {session.SystemDatabaseVersion ?? "<none>"}");
    Console.WriteLine($"System collections: {report.CollectionCount} ({report.NonEmptyCollectionCount} non-empty / {report.EmptyCollectionCount} empty)");
    Console.WriteLine($"Total system objects: {report.TotalObjects}");

    foreach (var entry in collections.Where(x => x.Count > 0).OrderByDescending(x => x.Count).Take(25))
        Console.WriteLine($"{entry.Type}: {entry.Count} objects, collection index {entry.CollectionIndex}, gaps {entry.MissingIndexCount}");

    if (!preflight.Ready)
    {
        foreach (var error in preflight.Errors)
            Console.Error.WriteLine($"- {error}");
    }

    return preflight.Ready ? 0 : 2;
}
catch (Exception ex)
{
    Console.Error.WriteLine("ORIGINS DATABASE AUDIT: ERROR");
    Console.Error.WriteLine(ex);
    return 1;
}

List<int> FindHoles(IReadOnlyList<int> existing, int collectionIndex, int limit)
{
    if (collectionIndex <= 0 || limit <= 0)
        return new List<int>();

    var present = existing.ToHashSet();
    var result = new List<int>(Math.Min(limit, Math.Max(0, collectionIndex - existing.Count)));

    for (var index = 1; index <= collectionIndex && result.Count < limit; index++)
    {
        if (!present.Contains(index))
            result.Add(index);
    }

    return result;
}

sealed class DatabaseAudit
{
    public int SchemaVersion { get; set; }
    public string DatabaseRoot { get; set; } = string.Empty;
    public bool SystemDatabaseExists { get; set; }
    public string? SystemVersion { get; set; }
    public bool PreflightReady { get; set; }
    public List<string> PreflightErrors { get; set; } = new();
    public int CollectionCount { get; set; }
    public int NonEmptyCollectionCount { get; set; }
    public int EmptyCollectionCount { get; set; }
    public int TotalObjects { get; set; }
    public List<CollectionAudit> Collections { get; set; } = new();
    public List<string> EmptyCollections { get; set; } = new();
    public DateTime AuditedUtc { get; set; }
}

sealed class CollectionAudit
{
    public string Assembly { get; set; } = string.Empty;
    public string Type { get; set; } = string.Empty;
    public int Count { get; set; }
    public int CollectionIndex { get; set; }
    public int HighestExistingIndex { get; set; }
    public int MissingIndexCount { get; set; }
    public List<int> FirstMissingIndices { get; set; } = new();
}
