using System.Collections;
using System.Reflection;
using System.Security.Cryptography;
using System.Text.Json;
using Library.SystemModels;
using MirDB;
using Origins.Database.Runtime;

if (args.Length < 2)
{
    Console.Error.WriteLine("Usage: Origins.Database.Export <database-root> <output-root> [backup-root]");
    return 64;
}

var databaseRoot = Path.GetFullPath(args[0]);
var outputRoot = Path.GetFullPath(args[1]);
var backupRoot = args.Length > 2 ? Path.GetFullPath(args[2]) : Path.Combine(databaseRoot, "Backup");
var systemDbPath = Path.Combine(databaseRoot, "System.db");

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

    var files = new SortedDictionary<string, int>(StringComparer.OrdinalIgnoreCase);

    Export(session.GetCollection<CurrencyInfo>(), outputRoot, "currencies.json", files);
    Export(session.GetCollection<ItemInfo>(), outputRoot, "items.json", files);
    Export(session.GetCollection<ItemInfoStat>(), outputRoot, "item-stats.json", files);
    Export(session.GetCollection<SetInfo>(), outputRoot, "sets.json", files);
    Export(session.GetCollection<SetInfoStat>(), outputRoot, "set-stats.json", files);

    Export(session.GetCollection<BaseStat>(), outputRoot, "base-stats.json", files);
    Export(session.GetCollection<MovementInfo>(), outputRoot, "movements.json", files);

    Export(session.GetCollection<MapInfo>(), outputRoot, "maps.json", files);
    Export(session.GetCollection<MapRegion>(), outputRoot, "map-regions.json", files);
    Export(session.GetCollection<SafeZoneInfo>(), outputRoot, "safe-zones.json", files);
    Export(session.GetCollection<InstanceInfo>(), outputRoot, "instances.json", files);
    Export(session.GetCollection<DungeonInfo>(), outputRoot, "dungeons.json", files);

    Export(session.GetCollection<MonsterInfo>(), outputRoot, "monsters.json", files);
    Export(session.GetCollection<MonsterInfoStat>(), outputRoot, "monster-stats.json", files);
    Export(session.GetCollection<DropInfo>(), outputRoot, "drops.json", files);
    Export(session.GetCollection<RespawnInfo>(), outputRoot, "respawns.json", files);

    Export(session.GetCollection<NPCInfo>(), outputRoot, "npcs.json", files);
    Export(session.GetCollection<StoreInfo>(), outputRoot, "stores.json", files);
    Export(session.GetCollection<QuestInfo>(), outputRoot, "quests.json", files);
    Export(session.GetCollection<MagicInfo>(), outputRoot, "magics.json", files);

    var manifest = new
    {
        schemaVersion = 1,
        source = new
        {
            systemDb = systemDbPath,
            sha256 = Sha256(systemDbPath),
            systemVersion = session.SystemDatabaseVersion
        },
        exportedUtc = DateTime.UtcNow,
        collections = files
    };

    File.WriteAllText(
        Path.Combine(outputRoot, "manifest.json"),
        JsonSerializer.Serialize(manifest, JsonOptions));

    Console.WriteLine($"ORIGINS SYSTEM.DB EXPORT: PASS ({files.Count} collections)");
    foreach (var pair in files)
        Console.WriteLine($"{pair.Key}: {pair.Value}");

    return 0;
}
catch (Exception ex)
{
    Console.Error.WriteLine("ORIGINS SYSTEM.DB EXPORT: ERROR");
    Console.Error.WriteLine(ex);
    return 1;
}

static void Export<T>(DBCollection<T> collection, string outputRoot, string fileName, IDictionary<string, int> files)
    where T : DBObject, new()
{
    var rows = collection.Binding
        .OrderBy(x => x.Index)
        .Select(Flatten)
        .ToList();

    File.WriteAllText(
        Path.Combine(outputRoot, fileName),
        JsonSerializer.Serialize(rows, JsonOptions));

    files[fileName] = rows.Count;
}

static Dictionary<string, object?> Flatten<T>(T value) where T : DBObject
{
    var result = new SortedDictionary<string, object?>(StringComparer.Ordinal)
    {
        ["Index"] = value.Index,
        ["$type"] = value.GetType().Name
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
                ["$ref"] = reference.GetType().Name,
                ["Index"] = reference.Index
            };
            continue;
        }

        if (propertyValue is IEnumerable && propertyValue is not string)
        {
            // Child/association collections have their own exported collection.
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
            result[property.Name] = JsonSerializer.SerializeToElement(propertyValue, propertyType, JsonOptions);
        }
        catch
        {
            result[property.Name] = propertyValue.ToString();
        }
    }

    return new Dictionary<string, object?>(result);
}

static string Sha256(string path)
{
    using var stream = File.OpenRead(path);
    using var sha = SHA256.Create();
    return Convert.ToHexString(sha.ComputeHash(stream));
}

static readonly JsonSerializerOptions JsonOptions = new()
{
    WriteIndented = true
};
