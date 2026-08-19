using Library;
using Server.DBModels;

namespace Server.Models.Magics
{
    [MagicType(MagicType.SpiritSword)]
    public sealed class SpiritSword : MagicObject
    {
        protected override Element Element => Element.None;
        public override bool AttackSkill => true;

        public SpiritSword(PlayerObject player, UserMagic magic) : base(player, magic)
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
            // Crystal: spiritSwordLvPlus = { 0, 3, 5, 8 }.
            int[] accuracyByLevel = { 0, 3, 5, 8 };
            int level = Magic.Level;
            if (level < 0) level = 0;
            if (level >= accuracyByLevel.Length) level = accuracyByLevel.Length - 1;

            return new Stats
            {
                [Stat.Accuracy] = accuracyByLevel[level]
            };
        }
    }
}
