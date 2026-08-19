using Library;
using Server.DBModels;
using Server.Envir;
using System;
using System.Drawing;

namespace Server.Models.Magics
{
    [MagicType(MagicType.MagicBooster)]
    public sealed class MagicBooster : MagicObject
    {
        protected override Element Element => Element.None;
        public override bool UpdateCombatTime => false;

        public MagicBooster(PlayerObject player, UserMagic magic) : base(player, magic)
        {
        }

        public override MagicCast MagicCast(MapObject target, Point location, MirDirection direction)
        {
            var response = new MagicCast
            {
                Ob = null
            };

            int bonus = 6 + Magic.Level * 6;

            ActionList.Add(new DelayedAction(
                SEnvir.Now.AddMilliseconds(500),
                ActionType.DelayMagic,
                Type,
                bonus));

            return response;
        }

        public override void MagicComplete(params object[] data)
        {
            int bonus = (int)data[1];

            var stats = new Stats
            {
                [Stat.MinMC] = bonus,
                [Stat.MaxMC] = bonus,
                [Stat.ManaPenaltyPercent] = 6 + Magic.Level
            };

            Player.BuffAdd(
                BuffType.MagicBooster,
                TimeSpan.FromSeconds(60),
                stats,
                true,
                false,
                TimeSpan.Zero);

            Player.LevelMagic(Magic);
        }
    }
}
