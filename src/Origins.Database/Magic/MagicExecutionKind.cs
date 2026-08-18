namespace Origins.Database.Magic;

/// <summary>
/// Describes only HOW a spell executes. Power, cost, levels, icon and class
/// remain authoritative in Zircon MagicInfo.
/// </summary>
public enum MagicExecutionKind
{
    ZirconNative = 0,
    Projectile = 1,
    MultiProjectile = 2,
    TargetStrike = 3,
    GroundArea = 4,
    TargetArea = 5,
    Line = 6,
    Cone = 7,
    SelfBuff = 8,
    TargetBuff = 9,
    Debuff = 10,
    Heal = 11,
    Revive = 12,
    Summon = 13,
    Teleport = 14,
    PersistentArea = 15,
    Chain = 16,
    MeleeSkill = 17,
    SpecialHandler = 100
}
