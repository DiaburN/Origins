using Library;
using Server.DBModels;
using System;
using System.Drawing;

namespace Server.Models.Magics
{
    [MagicType(MagicType.Fury)]
    public sealed class Fury : MagicObject
    {
        protected override Element Element => Element.None;
        public override bool UpdateCombatTime => false;

        public Fury(PlayerObject player, UserMagic magic) : base(player, magic)
        {
        }

        public override MagicCast MagicCast(MapObject target, Point location, MirDirection direction)
        {
            Player.BuffAdd(
                BuffType.Fury,
                TimeSpan.FromSeconds(60 + Magic.Level * 10),
                new Stats
                {
                    [Stat.AttackSpeed] = 4,
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
