using Library;
using Server.DBModels;
using System;
using System.Drawing;

namespace Server.Models.Magics
{
    [MagicType(MagicType.ProtectionField)]
    public sealed class ProtectionField : MagicObject
    {
        protected override Element Element => Element.None;
        public override bool UpdateCombatTime => false;

        public ProtectionField(PlayerObject player, UserMagic magic) : base(player, magic)
        {
        }

        public override MagicCast MagicCast(MapObject target, Point location, MirDirection direction)
        {
            int durationSeconds = 45 + 15 * Magic.Level;
            int addValue = (int)Math.Round(Player.Stats[Stat.MaxAC] * (0.20D + 0.03D * Magic.Level));

            Player.BuffAdd(
                BuffType.ProtectionField,
                TimeSpan.FromSeconds(durationSeconds),
                new Stats
                {
                    [Stat.MinAC] = addValue,
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
