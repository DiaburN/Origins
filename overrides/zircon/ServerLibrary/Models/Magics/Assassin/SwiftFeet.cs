using Library;
using Server.DBModels;
using System;
using System.Drawing;

namespace Server.Models.Magics
{
    [MagicType(MagicType.SwiftFeet)]
    public sealed class SwiftFeet : MagicObject
    {
        protected override Element Element => Element.None;
        public override bool UpdateCombatTime => false;

        public SwiftFeet(PlayerObject player, UserMagic magic) : base(player, magic) { }

        public override MagicCast MagicCast(MapObject target, Point location, MirDirection direction)
        {
            var response = new MagicCast { Ob = Player };
            response.Targets.Add(Player.ObjectID);

            // Crystal applies SwiftFeet immediately from the magic switch.
            Player.BuffAdd(
                BuffType.SwiftFeet,
                TimeSpan.FromSeconds(25 + Magic.Level * 5),
                new Stats(),
                true,
                false,
                TimeSpan.Zero);

            Player.LevelMagic(Magic);
            return response;
        }
    }
}
