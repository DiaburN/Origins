using System.Security.Cryptography;
using System.Text.Json;
using Server.MirEnvir;

if (args.Length < 2)
{
    Console.Error.WriteLine("Usage: Origins.CrystalJevMagic.Export <Jev-Server.MirDB> <output-json>");
    return 64;
}

var sourceDb = Path.GetFullPath(args[0]);
var outputJson = Path.GetFullPath(args[1]);

if (!File.Exists(sourceDb))
{
    Console.Error.WriteLine($"Crystal Jev Server.MirDB not found: {sourceDb}");
    return 66;
}

var previousDirectory = Directory.GetCurrentDirectory();
var workRoot = Path.Combine(Path.GetTempPath(), "origins-crystal-jev-" + Guid.NewGuid().ToString("N"));
Directory.CreateDirectory(workRoot);

try
{
    File.Copy(sourceDb, Path.Combine(workRoot, "Server.MirDB"), overwrite: true);
    Directory.SetCurrentDirectory(workRoot);

    var environment = Envir.Edit;
    if (!environment.LoadDB())
    {
        Console.Error.WriteLine("Crystal Envir.LoadDB() rejected Jev/Server.MirDB.");
        return 2;
    }

    var rows = environment.MagicInfoList
        .OrderBy(x => (byte)x.Spell)
        .Select(x => new
        {
            Name = x.Name,
            Spell = x.Spell.ToString(),
            SpellId = (byte)x.Spell,
            x.BaseCost,
            x.LevelCost,
            x.Icon,
            x.Level1,
            x.Level2,
            x.Level3,
            x.Need1,
            x.Need2,
            x.Need3,
            x.DelayBase,
            x.DelayReduction,
            x.PowerBase,
            x.PowerBonus,
            x.MPowerBase,
            x.MPowerBonus,
            x.MultiplierBase,
            x.MultiplierBonus,
            x.Range
        })
        .ToList();

    Directory.CreateDirectory(Path.GetDirectoryName(outputJson)!);
    var payload = new
    {
        schemaVersion = 1,
        source = new
        {
            repository = "Suprcode/Crystal.Database",
            commit = "a19f6dca8f5e238d4ed79801820777abbf0a9ca4",
            variant = "Jev",
            file = "Jev/Server.MirDB",
            sha256 = Sha256(sourceDb)
        },
        reader = new
        {
            repository = "Suprcode/Crystal",
            commit = "0e315fe327192afe52c3d7357ddd1f5b7e26c5b8",
            loadVersion = Envir.LoadVersion,
            loadCustomVersion = Envir.LoadCustomVersion,
            method = "Server.MirEnvir.Envir.LoadDB()",
            note = "Rows are the effective MagicInfoList after Crystal LoadDB(), including FillMagicInfoList defaults for any missing records."
        },
        count = rows.Count,
        magics = rows
    };

    File.WriteAllText(
        outputJson,
        JsonSerializer.Serialize(payload, new JsonSerializerOptions { WriteIndented = true }));

    Console.WriteLine($"CRYSTAL JEV MAGIC EXPORT: PASS ({rows.Count} effective spells, DB version {Envir.LoadVersion})");
    return 0;
}
catch (Exception ex)
{
    Console.Error.WriteLine("CRYSTAL JEV MAGIC EXPORT: ERROR");
    Console.Error.WriteLine(ex);
    return 1;
}
finally
{
    Directory.SetCurrentDirectory(previousDirectory);
    try { Directory.Delete(workRoot, recursive: true); } catch { }
}

static string Sha256(string path)
{
    using var stream = File.OpenRead(path);
    using var sha = SHA256.Create();
    return Convert.ToHexString(sha.ComputeHash(stream));
}
