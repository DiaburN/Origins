using Library;
using Server.DBModels;

namespace Server.Models.Magics
{
    // Crystal routes FireBurst through the exact same Repulsion helper.
    [MagicType(MagicType.FireBurst)]
    public sealed class FireBurst : Repulsion
    {
        public FireBurst(PlayerObject player, UserMagic magic) : base(player, magic) { }
    }
}
