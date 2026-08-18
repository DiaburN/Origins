namespace Origins.Database.Magic;

/// <summary>
/// Integration decision for one Crystal spell. This does NOT select a second
/// runtime spell engine; execution remains a Zircon MagicObject.
/// </summary>
public enum MagicExecutionKind
{
    /// <summary>Existing Zircon MagicObject can be used as-is.</summary>
    ZirconNative = 0,

    /// <summary>An existing Zircon MagicObject is subclassed/adapted for the Crystal behaviour.</summary>
    ZirconAdapted = 1,

    /// <summary>A small Crystal behaviour is ported into a new Zircon MagicObject implementation.</summary>
    CrystalAdapted = 2
}
