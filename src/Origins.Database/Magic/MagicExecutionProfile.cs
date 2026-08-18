namespace Origins.Database.Magic;

/// <summary>
/// Optional execution metadata attached to a Zircon MagicInfo row.
/// It deliberately does not duplicate Zircon combat/database fields.
/// </summary>
public sealed class MagicExecutionProfile
{
    public int MagicInfoIndex { get; init; }
    public string CrystalSpellKey { get; init; } = string.Empty;
    public MagicExecutionKind ExecutionKind { get; init; } = MagicExecutionKind.ZirconNative;

    // Used only when ExecutionKind == SpecialHandler.
    public string? HandlerKey { get; init; }

    // Animation/effect choreography. Values are filled only after verification.
    public string? CastProfile { get; init; }
    public int? ReleaseFrame { get; init; }
    public int? ReleaseDelayMs { get; init; }
    public string? ProjectileProfile { get; init; }
    public string? ImpactProfile { get; init; }

    // Execution geometry/timing not already represented by MagicInfo.
    public string? TargetMode { get; init; }
    public int? Radius { get; init; }
    public int? TickCount { get; init; }
    public int? TickIntervalMs { get; init; }

    // If true, damage/power calculation stays entirely in Zircon.
    public bool UseZirconDamage { get; init; } = true;
}
