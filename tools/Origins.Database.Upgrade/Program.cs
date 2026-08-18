using System.Security.Cryptography;
using System.Text.Json;
using Origins.Database.Runtime;

if (args.Length < 2)
{
    Console.Error.WriteLine("Usage: Origins.Database.Upgrade <source-System.db> <output-database-root> [backup-root]");
    return 64;
}

var sourceSystemDb = Path.GetFullPath(args[0]);
var outputRoot = Path.GetFullPath(args[1]);
var backupRoot = args.Length > 2
    ? Path.GetFullPath(args[2])
    : Path.Combine(outputRoot, "Backup");

if (!File.Exists(sourceSystemDb))
{
    Console.Error.WriteLine($"Source System.db not found: {sourceSystemDb}");
    return 66;
}

Directory.CreateDirectory(outputRoot);
Directory.CreateDirectory(backupRoot);

var targetSystemDb = Path.Combine(outputRoot, "System.db");
if (Path.GetFullPath(sourceSystemDb).Equals(Path.GetFullPath(targetSystemDb), StringComparison.OrdinalIgnoreCase))
{
    Console.Error.WriteLine("Refusing in-place upgrade. Source and target System.db must be different files.");
    return 65;
}

File.Copy(sourceSystemDb, targetSystemDb, overwrite: true);

var report = new UpgradeReport
{
    SourcePath = sourceSystemDb,
    TargetPath = targetSystemDb,
    SourceSha256 = Sha256(sourceSystemDb),
    StartedUtc = DateTime.UtcNow
};

try
{
    var session = ZirconDatabaseRuntime.OpenSystemWriter(outputRoot, backupRoot);
    var before = ZirconDatabasePreflight.Validate(session);

    report.Before = Snapshot(before);

    if (!before.Ready)
    {
        report.Success = false;
        report.Error = "Source database failed preflight before rewrite.";
        WriteReport(outputRoot, report);
        Print(before);
        return 2;
    }

    // Rewrites the copied candidate using the pinned current Zircon mappings.
    // The original source file is never modified.
    session.Save(commit: true);

    var verifySession = ZirconDatabaseRuntime.OpenSystemWriter(outputRoot, backupRoot);
    var after = ZirconDatabasePreflight.Validate(verifySession);

    report.After = Snapshot(after);
    report.TargetSha256 = Sha256(targetSystemDb);
    report.CompletedUtc = DateTime.UtcNow;
    report.Success = after.Ready && CountsMatch(before.Counts, after.Counts);

    if (!CountsMatch(before.Counts, after.Counts))
        report.Error = "Core collection counts changed during migration.";
    else if (!after.Ready)
        report.Error = "Upgraded database failed post-migration preflight.";

    WriteReport(outputRoot, report);

    Console.WriteLine($"Source SHA-256: {report.SourceSha256}");
    Console.WriteLine($"Target SHA-256: {report.TargetSha256}");
    Console.WriteLine($"System version before: {before.SystemVersion ?? "<none>"}");
    Console.WriteLine($"System version after:  {after.SystemVersion ?? "<none>"}");
    Print(after);

    if (!report.Success)
        return 3;

    Console.WriteLine("ORIGINS SYSTEM.DB UPGRADE: PASS");
    return 0;
}
catch (Exception ex)
{
    report.Success = false;
    report.CompletedUtc = DateTime.UtcNow;
    report.Error = ex.ToString();
    WriteReport(outputRoot, report);
    Console.Error.WriteLine(ex);
    return 1;
}

static bool CountsMatch(IReadOnlyDictionary<string, int> before, IReadOnlyDictionary<string, int> after)
{
    foreach (var pair in before)
    {
        if (!after.TryGetValue(pair.Key, out var count) || count != pair.Value)
            return false;
    }

    return true;
}

static string Sha256(string path)
{
    using var stream = File.OpenRead(path);
    using var sha = SHA256.Create();
    return Convert.ToHexString(sha.ComputeHash(stream));
}

static PreflightSnapshot Snapshot(ZirconDatabasePreflightResult result) => new()
{
    Ready = result.Ready,
    SystemVersion = result.SystemVersion,
    Counts = new Dictionary<string, int>(result.Counts),
    Errors = result.Errors.ToList()
};

static void Print(ZirconDatabasePreflightResult result)
{
    foreach (var pair in result.Counts.OrderBy(x => x.Key))
        Console.WriteLine($"{pair.Key}: {pair.Value}");

    foreach (var error in result.Errors)
        Console.Error.WriteLine($"- {error}");
}

static void WriteReport(string outputRoot, UpgradeReport report)
{
    var path = Path.Combine(outputRoot, "migration-report.json");
    var json = JsonSerializer.Serialize(report, new JsonSerializerOptions { WriteIndented = true });
    File.WriteAllText(path, json);
}

sealed class UpgradeReport
{
    public string SourcePath { get; set; } = string.Empty;
    public string TargetPath { get; set; } = string.Empty;
    public string SourceSha256 { get; set; } = string.Empty;
    public string? TargetSha256 { get; set; }
    public DateTime StartedUtc { get; set; }
    public DateTime? CompletedUtc { get; set; }
    public bool Success { get; set; }
    public string? Error { get; set; }
    public PreflightSnapshot? Before { get; set; }
    public PreflightSnapshot? After { get; set; }
}

sealed class PreflightSnapshot
{
    public bool Ready { get; set; }
    public string? SystemVersion { get; set; }
    public Dictionary<string, int> Counts { get; set; } = new();
    public List<string> Errors { get; set; } = new();
}
