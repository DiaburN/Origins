using Library;
using Server.DBModels;
using System;
using System.Drawing;

namespace Server.Models.Magics
{
    [MagicType(MagicType.MoonLight)]
    public sealed class MoonLight : MagicObject
    {
        protected override Element Element => Element.None;
        public override bool UpdateCombatTime => false;

        public MoonLight(PlayerObject player, UserMagic magic) : base(player, magic) { }

        public override MagicCast MagicCast(MapObject target, Point location, MirDirection direction)
        {
            var response = new MagicCast { Ob = Player };
            response.Targets.Add(Player.ObjectID);

            // Crystal: (GetAttackPower(MinAC, MaxAC) + 5 * (level + 1)) * 500 ms.
            double seconds = (Player.GetAC() + (Magic.Level + 1) * 5) * 0.5D;

            Player.BuffAdd(
                BuffType.MoonLight,
                TimeSpan.FromSeconds(seconds),
                new Stats(),
                true,
                false,
                TimeSpan.Zero);

            Player.LevelMagic(Magic);
            return response;
        }
    }
}
