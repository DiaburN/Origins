namespace Origins.Database.Magic;

/// <summary>
/// Audit metadata describing how a Crystal spell maps to Zircon.
/// It is intentionally not a combat dispatcher and does not duplicate MagicInfo.
/// </summary>
public sealed class MagicExecutionProfile
{
    public int MagicInfoIndex { get; init; }
    public string CrystalSpellKey { get; init; } = string.Empty;
    public MagicExecutionKind ExecutionKind { get; init; } = MagicExecutionKind.ZirconNative;

    /// <summary>Zircon MagicType used by MagicInfo.</summary>
    public string? ZirconMagicType { get; init; }

    /// <summary>Concrete MagicObject class used by the server.</summary>
    public string? HandlerClass { get; init; }

    /// <summary>Crystal method/class inspected when validating behaviour.</summary>
    public string? CrystalSourceReference { get; init; }

    /// <summary>True only after Crystal call path and Zircon handler have been compared.</summary>
    public bool Verified { get; init; }

    public string? Notes { get; init; }
}
