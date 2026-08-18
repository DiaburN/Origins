namespace Origins.Database.Runtime;

public static class ZirconDatabaseFiles
{
    public const string SystemDatabase = "System.db";
    public const string UsersDatabase = "Users.db";

    public static string SystemPath(string root) => Path.Combine(root, SystemDatabase);
    public static string UsersPath(string root) => Path.Combine(root, UsersDatabase);
}
