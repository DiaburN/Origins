using Library;
using Server.DBModels;
using Server.Envir;
using System;
using System.Drawing;

namespace Server.Models.Magics
{
    [MagicType(MagicType.Haste)]
    public sealed class Haste : MagicObject
    {
        protected override Element Element => Element.None;
        public override bool UpdateCombatTime => false;

        public Haste(PlayerObject player, UserMagic magic) : base(player, magic) { }

        public override MagicCast MagicCast(MapObject target, Point location, MirDirection direction)
        {
            var response = new MagicCast { Ob = Player };
            response.Targets.Add(Player.ObjectID);
            ActionList.Add(new DelayedAction(SEnvir.Now.AddMilliseconds(500), ActionType.DelayMagic, Type));
            return response;
        }

        public override void MagicComplete(params object[] data)
        {
            Player.BuffAdd(
                BuffType.Haste,
                TimeSpan.FromSeconds(25 + Magic.Level * 15),
                new Stats { [Stat.AttackSpeed] = Magic.Level * 2 + 2 },
                true,
                false,
                TimeSpan.Zero);

            Player.LevelMagic(Magic);
        }
    }
}
