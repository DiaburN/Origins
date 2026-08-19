using Library;
using Server.DBModels;
using Server.Envir;
using System;
using System.Drawing;

namespace Server.Models.Magics
{
    [MagicType(MagicType.EnergyShield)]
    public sealed class EnergyShield : MagicObject
    {
        protected override Element Element => Element.None;
        public override bool UpdateCombatTime => false;

        public EnergyShield(PlayerObject player, UserMagic magic) : base(player, magic) { }

        public override MagicCast MagicCast(MapObject target, Point location, MirDirection direction)
        {
            if (target == null || target.Node == null || !Player.CanHelpTarget(target))
                target = Player;

            var response = new MagicCast { Ob = target };

            // Crystal applies EnergyShield only to player targets.
            if (target.Race != ObjectType.Player)
            {
                response.Cast = false;
                response.Ob = null;
                return response;
            }

            response.Targets.Add(target.ObjectID);

            int durationSeconds = 30 + 50 * Magic.Level;
            int hpGain = Magic.GetPower() + Player.GetSC();
            int divisor = 10 - (Player.Stats[Stat.Luck] / 3 + Magic.Level + 1);
            if (divisor < 2) divisor = 2;
            int procPercent = (int)Math.Round((1M / divisor) * 100M);

            ActionList.Add(new DelayedAction(
                SEnvir.Now.AddMilliseconds(500),
                ActionType.DelayMagic,
                Type,
                target,
                durationSeconds,
                hpGain,
                procPercent));

            return response;
        }

        public override void MagicComplete(params object[] data)
        {
            MapObject target = (MapObject)data[1];
            int durationSeconds = (int)data[2];
            int hpGain = (int)data[3];
            int procPercent = (int)data[4];

            if (target?.Node == null || target.Race != ObjectType.Player || !Player.CanHelpTarget(target)) return;

            Stats stats = new Stats
            {
                [Stat.EnergyShieldPercent] = procPercent,
                [Stat.EnergyShieldHPGain] = hpGain,
            };

            target.BuffAdd(BuffType.EnergyShield, TimeSpan.FromSeconds(durationSeconds), stats, true, false, TimeSpan.Zero);
            Player.LevelMagic(Magic);
        }
    }
}
