using Library;
using Server.DBModels;

namespace Server.Models.Magics
{
    // Crystal Fencing is mapped to Zircon's Swordsmanship runtime identity.
    [MagicType(MagicType.Swordsmanship)]
    public sealed class Swordsmanship : MagicObject
    {
        protected override Element Element => Element.None;
        public override bool AttackSkill => true;

        public Swordsmanship(PlayerObject player, UserMagic magic) : base(player, magic)
        {
        }

        public override AttackCast AttackCast(MagicType attackType)
        {
            var response = new AttackCast();
            response.Magics.Add(Type);
            return response;
        }

        public override Stats GetPassiveStats()
        {
            return new Stats
            {
                // Crystal: Fencing adds exactly magic.Level * 3 Accuracy.
                [Stat.Accuracy] = Magic.Level * 3,
            };
        }
    }
}
