using System.Collections.Generic;

namespace Origins.Database.Magic;

/// <summary>
/// Runtime lookup keyed by Zircon MagicInfo.Index.
/// A missing profile means: execute the spell using Zircon native behaviour.
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

    public MagicExecutionKind ResolveKind(int magicInfoIndex)
    {
        return _profiles.TryGetValue(magicInfoIndex, out var profile)
            ? profile.ExecutionKind
            : MagicExecutionKind.ZirconNative;
    }
}
