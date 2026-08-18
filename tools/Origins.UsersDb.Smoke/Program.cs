using System.Security.Cryptography;
using System.Text.Json;
using Library;
using Library.SystemModels;
using Origins.Database.Runtime;
using Server.DBModels;
using Server.Envir;

if (args.Length < 2)
{
    Console.Error.WriteLine("Usage: Origins.UsersDb.Smoke <source-System.db> <report-json>");
    return 64;
}

var sourceSystemDb = Path.GetFullPath(args[0]);
var reportPath = Path.GetFullPath(args[1]);
if (!File.Exists(sourceSystemDb))
{
    Console.Error.WriteLine($"System.db not found: {sourceSystemDb}");
    return 66;
}

var root = Path.Combine(Path.GetTempPath(), "origins-usersdb-smoke-" + Guid.NewGuid().ToString("N"));
var databaseRoot = Path.Combine(root, "Database");
var backupRoot = Path.Combine(root, "Backup");
Directory.CreateDirectory(databaseRoot);
Directory.CreateDirectory(backupRoot);
File.Copy(sourceSystemDb, Path.Combine(databaseRoot, "System.db"));

try
{
    var session = ZirconDatabaseRuntime.OpenServer(databaseRoot, backupRoot);

    // AccountInfo.OnCreated() uses this server collection when it creates the
    // permanent HuntGold buff. The currency rows are created through Session.
    SEnvir.BuffInfoList = session.GetCollection<BuffInfo>();

    var accounts = session.GetCollection<AccountInfo>();
    var currencies = session.GetCollection<CurrencyInfo>();
    var userCurrencies = session.GetCollection<UserCurrency>();
    var buffs = session.GetCollection<BuffInfo>();

    if (accounts.Count != 0)
        throw new InvalidOperationException("Fresh smoke Users.db unexpectedly contains accounts.");

    var account = accounts.CreateNewObject();
    account.EMailAddress = "origins-db-smoke@invalid.local";
    account.Password = SHA256.HashData(System.Text.Encoding.UTF8.GetBytes("ORIGINS-SMOKE-ONLY"));
    account.RealName = "ORIGINS DB Smoke";
    account.BirthDate = new DateTime(2000, 1, 1);
    account.CreationIP = "127.0.0.1";
    account.LastIP = "127.0.0.1";
    account.CreationDate = DateTime.UtcNow;
    account.LastLogin = DateTime.UtcNow;
    account.Activated = true;
    account.AllowGroup = true;
    account.AllowTrade = true;
    account.AllowGuild = true;

    var expectedCurrencyCount = currencies.Count;
    if (account.Currencies.Count != expectedCurrencyCount)
        throw new InvalidOperationException($"Account default currencies {account.Currencies.Count} != System.db currencies {expectedCurrencyCount}.");

    if (account.Buffs.Count(x => x.Type == BuffType.HuntGold) != 1)
        throw new InvalidOperationException("Account creation did not create exactly one HuntGold buff.");

    session.Save(commit: true);

    var usersDb = Path.Combine(databaseRoot, "Users.db");
    if (!File.Exists(usersDb))
        throw new InvalidOperationException("Session commit did not create Users.db.");

    var usersDbSha = Convert.ToHexString(SHA256.HashData(File.ReadAllBytes(usersDb)));

    // Reopen the physical Users.db through the same current Zircon mappings.
    var reopened = ZirconDatabaseRuntime.OpenServer(databaseRoot, backupRoot);
    SEnvir.BuffInfoList = reopened.GetCollection<BuffInfo>();

    var reopenedAccounts = reopened.GetCollection<AccountInfo>();
    var persisted = reopenedAccounts.Binding.SingleOrDefault(x => x.EMailAddress == "origins-db-smoke@invalid.local")
        ?? throw new InvalidOperationException("Smoke account was not found after reopening Users.db.");

    if (persisted.Currencies.Count != expectedCurrencyCount)
        throw new InvalidOperationException($"Persisted account currencies {persisted.Currencies.Count} != expected {expectedCurrencyCount}.");

    if (persisted.Buffs.Count(x => x.Type == BuffType.HuntGold) != 1)
        throw new InvalidOperationException("Persisted account does not have exactly one HuntGold buff.");

    var report = new
    {
        schemaVersion = 1,
        success = true,
        systemDb = new
        {
            source = sourceSystemDb,
            systemVersion = reopened.SystemDatabaseVersion,
            currencyCount = expectedCurrencyCount
        },
        usersDb = new
        {
            sha256 = usersDbSha,
            accountCount = reopenedAccounts.Count,
            userCurrencyCount = reopened.GetCollection<UserCurrency>().Count,
            buffCount = reopened.GetCollection<BuffInfo>().Count,
            characterCount = reopened.GetCollection<CharacterInfo>().Count,
            userItemCount = reopened.GetCollection<UserItem>().Count,
            userMagicCount = reopened.GetCollection<UserMagic>().Count,
            userQuestCount = reopened.GetCollection<UserQuest>().Count,
            guildCount = reopened.GetCollection<GuildInfo>().Count
        },
        checks = new
        {
            accountRoundTrip = true,
            defaultCurrencies = persisted.Currencies.Count,
            huntGoldBuff = 1
        },
        completedUtc = DateTime.UtcNow
    };

    Directory.CreateDirectory(Path.GetDirectoryName(reportPath)!);
    File.WriteAllText(reportPath, JsonSerializer.Serialize(report, new JsonSerializerOptions { WriteIndented = true }));
    Console.WriteLine($"ORIGINS USERS.DB SMOKE: PASS (1 account, {expectedCurrencyCount} currencies, HuntGold buff persisted)");
    return 0;
}
catch (Exception ex)
{
    Directory.CreateDirectory(Path.GetDirectoryName(reportPath)!);
    File.WriteAllText(reportPath, JsonSerializer.Serialize(new
    {
        schemaVersion = 1,
        success = false,
        error = ex.ToString(),
        completedUtc = DateTime.UtcNow
    }, new JsonSerializerOptions { WriteIndented = true }));
    Console.Error.WriteLine("ORIGINS USERS.DB SMOKE: ERROR");
    Console.Error.WriteLine(ex);
    return 1;
}
finally
{
    try { Directory.Delete(root, recursive: true); } catch { }
}
