using Library;
using Server.DBModels;
using System;
using System.Drawing;

namespace Server.Models.Magics
{
    [MagicType(MagicType.Rage)]
    public sealed class Rage : MagicObject
    {
        protected override Element Element => Element.None;
        public override bool UpdateCombatTime => false;

        public Rage(PlayerObject player, UserMagic magic) : base(player, magic)
        {
        }

        public override MagicCast MagicCast(MapObject target, Point location, MirDirection direction)
        {
            int durationSeconds = 18 + 6 * Magic.Level;
            int addValue = (int)Math.Round(Player.Stats[Stat.MaxDC] * (0.12D + 0.03D * Magic.Level));

            Player.BuffAdd(
                BuffType.Rage,
                TimeSpan.FromSeconds(durationSeconds),
                new Stats
                {
                    [Stat.MinDC] = addValue,
                    [Stat.MaxDC] = addValue,
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
