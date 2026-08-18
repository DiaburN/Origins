using System.Collections;
using System.Reflection;
using System.Security.Cryptography;
using System.Text.Json;
using Library.SystemModels;
using MirDB;
using Origins.Database.Runtime;
using Origins.Database.Snapshots;
using Server.DBModels;

if (args.Length < 2)
{
    Console.Error.WriteLine("Usage: Origins.Database.Export <database-root> <output-root> [backup-root]");
    return 64;
}

var databaseRoot = Path.GetFullPath(args[0]);
var outputRoot = Path.GetFullPath(args[1]);
var backupRoot = args.Length > 2 ? Path.GetFullPath(args[2]) : Path.Combine(databaseRoot, "Backup");
var systemDbPath = Path.Combine(databaseRoot, "System.db");
var jsonOptions = new JsonSerializerOptions { WriteIndented = true };

if (!File.Exists(systemDbPath))
{
    Console.Error.WriteLine($"System.db not found: {systemDbPath}");
    return 66;
}

Directory.CreateDirectory(outputRoot);

try
{
    var session = ZirconDatabaseRuntime.OpenSystemWriter(databaseRoot, backupRoot);
    var preflight = ZirconDatabasePreflight.Validate(session);
    if (!preflight.Ready)
    {
        Console.Error.WriteLine("Refusing export because System.db failed preflight.");
        foreach (var error in preflight.Errors)
            Console.Error.WriteLine($"- {error}");
        return 2;
    }

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

    var manifestCollections = new List<SystemSnapshotCollection>();

    foreach (var type in systemTypes)
    {
        var collection = session.GetCollection(type);
        var collectionType = collection.GetType();
        var bindingField = collectionType.GetField("Binding", BindingFlags.Public | BindingFlags.Instance)
            ?? throw new InvalidOperationException($"Binding field not found for {type.FullName}.");
        var collectionIndexProperty = collectionType.GetProperty("Index", BindingFlags.Public | BindingFlags.Instance)
            ?? throw new InvalidOperationException($"Index property not found for {type.FullName} collection.");

        var objects = ((IEnumerable)(bindingField.GetValue(collection)
            ?? throw new InvalidOperationException($"Binding is null for {type.FullName}.")))
            .Cast<DBObject>()
            .OrderBy(x => x.Index)
            .Select(Flatten)
            .ToList();

        var fileName = FileNameFor(type);
        File.WriteAllText(
            Path.Combine(outputRoot, fileName),
            JsonSerializer.Serialize(objects, jsonOptions));

        manifestCollections.Add(new SystemSnapshotCollection
        {
            AssemblyName = type.Assembly.GetName().Name ?? string.Empty,
            TypeName = type.FullName ?? type.Name,
            FileName = fileName,
            Count = objects.Count,
            CollectionIndex = (int)(collectionIndexProperty.GetValue(collection) ?? 0)
        });
    }

    var manifest = new SystemSnapshotManifest
    {
        SchemaVersion = 1,
        SourceSystemDbSha256 = Sha256(systemDbPath),
        SourceSystemVersion = session.SystemDatabaseVersion,
        ExportedUtc = DateTime.UtcNow,
        Collections = manifestCollections
    };

    File.WriteAllText(
        Path.Combine(outputRoot, "manifest.json"),
        JsonSerializer.Serialize(manifest, jsonOptions));

    Console.WriteLine($"ORIGINS SYSTEM.DB EXPORT: PASS ({manifestCollections.Count} collections)");
    foreach (var entry in manifestCollections)
        Console.WriteLine($"{entry.TypeName}: {entry.Count} (collection index {entry.CollectionIndex})");

    return 0;
}
catch (Exception ex)
{
    Console.Error.WriteLine("ORIGINS SYSTEM.DB EXPORT: ERROR");
    Console.Error.WriteLine(ex);
    return 1;
}

Dictionary<string, object?> Flatten(DBObject value)
{
    var result = new SortedDictionary<string, object?>(StringComparer.Ordinal)
    {
        ["Index"] = value.Index,
        ["$assembly"] = value.GetType().Assembly.GetName().Name,
        ["$type"] = value.GetType().FullName
    };

    var properties = value.GetType().GetProperties(BindingFlags.Public | BindingFlags.Instance);
    foreach (var property in properties.OrderBy(x => x.Name, StringComparer.Ordinal))
    {
        if (!property.CanRead || property.GetIndexParameters().Length != 0)
            continue;

        if (property.Name is "Index" or "ThisType" or "IsDeleted")
            continue;

        if (property.GetCustomAttribute<IgnorePropertyAttribute>() != null)
            continue;

        object? propertyValue;
        try
        {
            propertyValue = property.GetValue(value);
        }
        catch
        {
            continue;
        }

        if (propertyValue is null)
        {
            result[property.Name] = null;
            continue;
        }

        if (propertyValue is DBObject reference)
        {
            result[property.Name] = new Dictionary<string, object?>
            {
                ["$refAssembly"] = reference.GetType().Assembly.GetName().Name,
                ["$refType"] = reference.GetType().FullName,
                ["Index"] = reference.Index
            };
            continue;
        }

        if (propertyValue is IEnumerable && propertyValue is not string)
        {
            // Reverse/child association collections are recreated by assigning
            // the referenced DBObject properties during import.
            continue;
        }

        var propertyType = propertyValue.GetType();
        if (propertyType.IsEnum)
        {
            result[property.Name] = propertyValue.ToString();
            continue;
        }

        try
        {
            result[property.Name] = JsonSerializer.SerializeToElement(propertyValue, propertyType, jsonOptions);
        }
        catch
        {
            result[property.Name] = propertyValue.ToString();
        }
    }

    return new Dictionary<string, object?>(result);
}

string FileNameFor(Type type)
{
    var assembly = type.Assembly.GetName().Name ?? "Assembly";
    var fullName = type.FullName ?? type.Name;
    var safeName = fullName
        .Replace('.', '_')
        .Replace('+', '_')
        .Replace('`', '_');

    return $"{assembly}__{safeName}.json";
}

string Sha256(string path)
{
    using var stream = File.OpenRead(path);
    using var sha = SHA256.Create();
    return Convert.ToHexString(sha.ComputeHash(stream));
}
