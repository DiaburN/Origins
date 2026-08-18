using Library.SystemModels;
using MirDB;
using Server.DBModels;

namespace Origins.Database.Runtime;

/// <summary>
/// Opens the exact Zircon database engine with the same two model assemblies
/// used by SEnvir.LoadDatabase().
/// </summary>
public static class ZirconDatabaseRuntime
{
    public const string DefaultDatabaseRoot = @".\Database\";
    public const string DefaultBackupRoot = @".\Backup\";

    /// <summary>
    /// Game-server mode. Loads System.db and Users.db, but only Users.db is
    /// writable through Session.Commit(), matching Zircon server behaviour.
    /// </summary>
    public static Session OpenServer(
        string databaseRoot = DefaultDatabaseRoot,
        string backupRoot = DefaultBackupRoot,
        int backupDelayMinutes = 60)
    {
        return Open(SessionMode.Users, databaseRoot, backupRoot, backupDelayMinutes);
    }

    /// <summary>
    /// Admin/editor mode. Allows ORIGINS tooling to load and save both
    /// System.db (game definitions) and Users.db (persistent state).
    /// </summary>
    public static Session OpenEditor(
        string databaseRoot = DefaultDatabaseRoot,
        string backupRoot = DefaultBackupRoot,
        int backupDelayMinutes = 60)
    {
        return Open(SessionMode.Both, databaseRoot, backupRoot, backupDelayMinutes);
    }

    /// <summary>
    /// Static-content-only mode. Intended for build/seed tools that generate
    /// System.db without touching Users.db.
    /// </summary>
    public static Session OpenSystemWriter(
        string databaseRoot = DefaultDatabaseRoot,
        string backupRoot = DefaultBackupRoot,
        int backupDelayMinutes = 60)
    {
        return Open(SessionMode.System, databaseRoot, backupRoot, backupDelayMinutes);
    }

    private static Session Open(
        SessionMode mode,
        string databaseRoot,
        string backupRoot,
        int backupDelayMinutes)
    {
        var session = new Session(mode, databaseRoot, backupRoot)
        {
            BackUpDelay = backupDelayMinutes,
        };

        // These are the same two assemblies initialized by Zircon SEnvir.
        session.Initialize(
            typeof(ItemInfo).Assembly,
            typeof(AccountInfo).Assembly);

        return session;
    }
}
