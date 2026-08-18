using System.Collections.Generic;

namespace Origins.Database.Magic;

/// <summary>
/// Lookup for migration/audit metadata only. The game server still resolves
/// and executes spells through Zircon MagicObject + MagicTypeAttribute.
/// </summary>
public sealed class MagicExecutionProfileRegistry
{
    private readonly Dictionary<int, MagicExecutionProfile> _profiles = new();

    public void Register(MagicExecutionProfile profile)
    {
        _profiles[profile.MagicInfoIndex] = profile;
    }

    public bool TryGet(int magicInfoIndex, out MagicExecutionProfile? profile)
    {
        return _profiles.TryGetValue(magicInfoIndex, out profile);
    }
}
