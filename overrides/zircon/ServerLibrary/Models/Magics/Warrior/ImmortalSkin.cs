using Library;
using Server.DBModels;
using System;
using System.Drawing;

namespace Server.Models.Magics
{
    [MagicType(MagicType.ImmortalSkin)]
    public sealed class ImmortalSkin : MagicObject
    {
        protected override Element Element => Element.None;
        public override bool UpdateCombatTime => false;

        public ImmortalSkin(PlayerObject player, UserMagic magic) : base(player, magic)
        {
        }

        public override MagicCast MagicCast(MapObject target, Point location, MirDirection direction)
        {
            int dcPenalty = (int)Math.Round(Player.Stats[Stat.MaxDC] * (0.05D + 0.01D * Magic.Level)) * -1;
            int acBonus = (int)Math.Round(Player.Stats[Stat.MaxAC] * (0.10D + 0.07D * Magic.Level));

            Player.BuffAdd(
                BuffType.ImmortalSkin,
                TimeSpan.FromSeconds(60 + Magic.Level),
                new Stats
                {
                    [Stat.MaxDC] = dcPenalty,
                    [Stat.MaxAC] = acBonus,
                },
                false,
                false,
                TimeSpan.Zero);

            Player.LevelMagic(Magic);

            return new MagicCast
            {
                Ob = null,
                Direction = MirDirection.Down,
            };
        }
    }
}
