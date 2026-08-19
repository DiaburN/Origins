using Library;
using Server.DBModels;
using Server.Envir;
using System;
using System.Drawing;

namespace Server.Models.Magics
{
    [MagicType(MagicType.Bisul)]
    public sealed class Bisul : MagicObject
    {
        protected override Element Element => Element.None;
        public override bool UpdateCombatTime => false;

        public Bisul(PlayerObject player, UserMagic magic) : base(player, magic)
        {
        }

        public override MagicCast MagicCast(MapObject target, Point location, MirDirection direction)
        {
            var response = new MagicCast { Ob = Player };

            ActionList.Add(new DelayedAction(
                SEnvir.Now.AddMilliseconds(500),
                ActionType.DelayMagic,
                Type));

            return response;
        }

        public override void MagicComplete(params object[] data)
        {
            int durationSeconds = 10 + 5 * Magic.Level + Player.Stats[Stat.MaxMC] / 10;

            Player.BuffAdd(
                BuffType.Bisul,
                TimeSpan.FromSeconds(durationSeconds),
                new Stats(),
                true,
                false,
                TimeSpan.Zero);

            if (Magic.Level >= 4)
                MagicCooldown(Magic, 300000);

            Player.LevelMagic(Magic);
        }
    }
}
