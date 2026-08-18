using Library;
using Library.SystemModels;
using MirDB;

namespace Origins.Database.Runtime;

public sealed record ZirconDatabasePreflightResult(
    bool Ready,
    IReadOnlyList<string> Errors,
    IReadOnlyDictionary<string, int> Counts,
    string? SystemVersion);

/// <summary>
/// Checks the minimum static content needed before ORIGINS treats a Zircon
/// System.db as usable. This catches an empty/schema-only DB before SEnvir
/// reaches assumptions such as CurrencyType.Gold being present.
/// </summary>
public static class ZirconDatabasePreflight
{
    public static ZirconDatabasePreflightResult Validate(Session session)
    {
        ArgumentNullException.ThrowIfNull(session);

        var errors = new List<string>();
        var counts = new Dictionary<string, int>();

        if (!session.SystemDatabaseExists)
            errors.Add("System.db does not exist.");

        CountAndRequire(session.GetCollection<ItemInfo>(), "Items", counts, errors);
        CountAndRequire(session.GetCollection<MapInfo>(), "Maps", counts, errors);
        CountAndRequire(session.GetCollection<MonsterInfo>(), "Monsters", counts, errors);
        CountAndRequire(session.GetCollection<MagicInfo>(), "Magics", counts, errors);
        CountAndRequire(session.GetCollection<BaseStat>(), "BaseStats", counts, errors);
        CountAndRequire(session.GetCollection<CurrencyInfo>(), "Currencies", counts, errors);

        var currencies = session.GetCollection<CurrencyInfo>();
        var gold = currencies.Binding.FirstOrDefault(x => x.Type == CurrencyType.Gold);
        if (gold == null)
            errors.Add("CurrencyType.Gold is missing; current Zircon server startup expects it.");
        else if (gold.DropItem == null)
            errors.Add("CurrencyType.Gold exists but has no DropItem; current Zircon server startup expects it.");

        return new ZirconDatabasePreflightResult(
            errors.Count == 0,
            errors,
            counts,
            session.SystemDatabaseVersion);
    }

    private static void CountAndRequire<T>(
        DBCollection<T> collection,
        string name,
        IDictionary<string, int> counts,
        ICollection<string> errors)
        where T : DBObject, new()
    {
        counts[name] = collection.Count;
        if (collection.Count == 0)
            errors.Add($"{name} collection is empty.");
    }
}
