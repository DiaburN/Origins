using Library;
using Server.DBModels;
using Server.Envir;
using System;
using System.Drawing;

namespace Server.Models.Magics
{
    [MagicType(MagicType.LightBody)]
    public sealed class LightBody : MagicObject
    {
        protected override Element Element => Element.None;
        public override bool UpdateCombatTime => false;

        public LightBody(PlayerObject player, UserMagic magic) : base(player, magic) { }

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
                BuffType.LightBody,
                TimeSpan.FromSeconds((Magic.Level + 1) * 30),
                new Stats { [Stat.Agility] = (Magic.Level + 1) * 2 },
                true,
                false,
                TimeSpan.Zero);

            Player.LevelMagic(Magic);
        }
    }
}
