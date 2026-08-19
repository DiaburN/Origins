using Library;
using Server.DBModels;

namespace Server.Models.Magics
{
    [MagicType(MagicType.GreatFireBall)]
    public class GreatFireBall : FireBall
    {
        public GreatFireBall(PlayerObject player, UserMagic magic) : base(player, magic)
        {
        }
    }
}
