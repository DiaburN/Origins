using Library;
using Server.DBModels;
using Server.Envir;
using System;
using System.Drawing;
using System.Linq;

namespace Server.Models.Magics
{
    [MagicType(MagicType.MagicShield)]
    public class MagicShield : MagicObject
    {
        protected override Element Element => Element.None;
        public override bool UpdateCombatTime => false;

        public MagicShield(PlayerObject player, UserMagic magic) : base(player, magic)
        {
        }

        public override MagicCast MagicCast(MapObject target, Point location, MirDirection direction)
        {
            var response = new MagicCast
            {
                Ob = null
            };

            int durationSeconds = (int)Math.Round((Player.GetMC() + 15) / 4F * (Magic.Level + 1));

            ActionList.Add(new DelayedAction(
                SEnvir.Now.AddMilliseconds(500),
                ActionType.DelayMagic,
                Type,
                durationSeconds));

            return response;
        }

        public override void MagicComplete(params object[] data)
        {
            if (Player.Buffs.Any(x => x.Type == BuffType.MagicShield) ||
                Player.Buffs.Any(x => x.Type == BuffType.SuperiorMagicShield))
                return;

            int durationSeconds = (int)data[1];
            int reductionPercent = (Magic.Level + 2) * 10;

            Stats buffStats = new Stats
            {
                [Stat.MagicShield] = reductionPercent
            };

            Player.BuffAdd(
                BuffType.MagicShield,
                TimeSpan.FromSeconds(durationSeconds),
                buffStats,
                true,
                false,
                TimeSpan.Zero);

            Player.LevelMagic(Magic);
        }
    }
}
