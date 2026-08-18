using Origins.Database.Runtime;

var databaseRoot = args.Length > 0 ? args[0] : @".\Database\";
var backupRoot = args.Length > 1 ? args[1] : @".\Backup\";

try
{
    var session = ZirconDatabaseRuntime.OpenSystemWriter(databaseRoot, backupRoot);
    var result = ZirconDatabasePreflight.Validate(session);

    Console.WriteLine($"System.db version: {result.SystemVersion ?? "<none>"}");
    foreach (var pair in result.Counts.OrderBy(x => x.Key))
        Console.WriteLine($"{pair.Key}: {pair.Value}");

    if (result.Ready)
    {
        Console.WriteLine("ORIGINS DB PREFLIGHT: PASS");
        return 0;
    }

    Console.Error.WriteLine("ORIGINS DB PREFLIGHT: FAIL");
    foreach (var error in result.Errors)
        Console.Error.WriteLine($"- {error}");

    return 2;
}
catch (Exception ex)
{
    Console.Error.WriteLine("ORIGINS DB PREFLIGHT: ERROR");
    Console.Error.WriteLine(ex);
    return 1;
}
