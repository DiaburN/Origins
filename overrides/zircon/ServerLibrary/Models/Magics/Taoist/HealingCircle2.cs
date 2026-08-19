using Library;
using Server.DBModels;
using Server.Envir;
using System;
using System.Drawing;

namespace Server.Models.Magics
{
    [MagicType(MagicType.HealingCircle2)]
    public sealed class HealingCircle2 : MagicObject
    {
        protected override Element Element => Element.None;
        public override bool UpdateCombatTime => false;

        public HealingCircle2(PlayerObject player, UserMagic magic) : base(player, magic) { }

        public override MagicCast MagicCast(MapObject target, Point location, MirDirection direction)
        {
            var response = new MagicCast { Ob = null };

            if (!Functions.InRange(CurrentLocation, location, Globals.MagicRange) ||
                Player.Buffs.Exists(x => x.Type == BuffType.CrystalHealingCircle2) ||
                !Player.UseAmulet(10, 0))
            {
                response.Cast = false;
                return response;
            }

            response.Locations.Add(location);

            int power = Magic.GetPower() + Player.GetSC() + 40 * (Magic.Level + 1);
            int durationMilliseconds = (Magic.Level + 1) * 5000;
            int reductionPercent = Magic.Level * 10 + 20;

            Player.BuffAdd(
                BuffType.CrystalHealingCircle2,
                TimeSpan.FromMilliseconds(durationMilliseconds),
                new Stats { [Stat.HealingCircle2ReductionPercent] = reductionPercent },
                true,
                false,
                TimeSpan.Zero);

            ActionList.Add(new DelayedAction(
                SEnvir.Now.AddMilliseconds(500),
                ActionType.DelayMagic,
                Type,
                CurrentMap,
                location,
                power,
                durationMilliseconds));

            return response;
        }

        public override void MagicComplete(params object[] data)
        {
            Map map = (Map)data[1];
            Point location = (Point)data[2];
            int power = (int)data[3];
            int durationMilliseconds = (int)data[4];
            if (map != CurrentMap) return;

            // Zircon SpellObject processes immediately at TickTime, then every 3 s.
            // Ceil(duration / 3s) therefore reproduces Jev ticks at 0,3,6,... before expiry.
            int ticks = Math.Max(1, (durationMilliseconds + 2999) / 3000);
            bool spawned = false;

            foreach (Cell cell in map.GetCells(location, 0, 2))
            {
                if (cell == null || cell.Movements != null) continue;

                SpellObject ob = new SpellObject
                {
                    DisplayLocation = cell.Location,
                    Effect = SpellEffect.CrystalHealingCircle2,
                    TickCount = ticks,
                    TickFrequency = TimeSpan.FromSeconds(3),
                    TickTime = SEnvir.Now,
                    Owner = Player,
                    Magic = Magic,
                    Power = power,
                };

                if (ob.Spawn(map, cell.Location))
                    spawned = true;
            }

            if (spawned)
                Player.LevelMagic(Magic);
        }

        public override int ModifyPowerAdditionner(bool primary, int power, MapObject ob, Stats stats = null, int extra = 0)
        {
            return extra;
        }

        public override void MagicAttackSuccess(MapObject ob, int damageDealt)
        {
            // Jev trains on field creation, not on every 3-second tick.
        }
    }
}
