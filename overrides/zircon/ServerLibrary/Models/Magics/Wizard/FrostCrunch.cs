using Library;
using Server.DBModels;

namespace Server.Models.Magics
{
    [MagicType(MagicType.FrostCrunch)]
    public class FrostCrunch : FireBall
    {
        protected override Element Element => Element.Ice;

        public FrostCrunch(PlayerObject player, UserMagic magic) : base(player, magic)
        {
        }
    }
}
