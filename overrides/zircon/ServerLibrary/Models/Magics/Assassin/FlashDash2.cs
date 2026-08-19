using Library;
using Server.DBModels;

namespace Server.Models.Magics
{
    [MagicType(MagicType.FlashDash2)]
    public sealed class FlashDash2 : CrystalFlashDashBase
    {
        protected override bool ForceStun => true;

        public FlashDash2(PlayerObject player, UserMagic magic) : base(player, magic) { }
    }
}
