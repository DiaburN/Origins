using Library;
using Server.DBModels;
using System;
using System.Drawing;

namespace Server.Models.Magics
{
    [MagicType(MagicType.ProtectionField1)]
    public sealed class ProtectionField1 : MagicObject
    {
        protected override Element Element => Element.None;
        public override bool UpdateCombatTime => false;

        public ProtectionField1(PlayerObject player, UserMagic magic) : base(player, magic)
        {
        }

        public override MagicCast MagicCast(MapObject target, Point location, MirDirection direction)
        {
            int durationSeconds = 45 + 15 * Magic.Level;
            int addValue = (int)Math.Round(Player.Stats[Stat.MaxAC] * (0.20D + 0.03D * Magic.Level));

            Player.BuffAdd(
                BuffType.ProtectionField1,
                TimeSpan.FromSeconds(durationSeconds),
                new Stats
                {
                    [Stat.MaxAC] = addValue,
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
