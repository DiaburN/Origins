using Library;
using Server.DBModels;
using Server.Envir;
using System;
using System.Drawing;
using System.Linq;

namespace Server.Models.Magics
{
    [MagicType(MagicType.HealingCircle)]
    public sealed class HealingCircle : MagicObject
    {
        protected override Element Element => Element.None;
        public override bool UpdateCombatTime => false;

        public HealingCircle(PlayerObject player, UserMagic magic) : base(player, magic) { }

        public override MagicCast MagicCast(MapObject target, Point location, MirDirection direction)
        {
            var response = new MagicCast { Ob = null };

            if (!Functions.InRange(CurrentLocation, location, Globals.MagicRange))
            {
                response.Cast = false;
                return response;
            }

            response.Locations.Add(location);

            // Crystal schedules HealingCircle after its 500 ms cast completion plus 1200 ms field delay.
            int power = Magic.GetPower() + Player.GetSC();
            ActionList.Add(new DelayedAction(
                SEnvir.Now.AddMilliseconds(1700),
                ActionType.DelayMagic,
                Type,
                CurrentMap,
                location,
                power));

            return response;
        }

        public override void MagicComplete(params object[] data)
        {
            Map map = (Map)data[1];
            Point location = (Point)data[2];
            int power = (int)data[3];
            if (map != CurrentMap) return;

            int durationMs = 10000 + 5000 * Magic.Level;
            int ticks = Math.Max(1, durationMs / 400);
            bool spawned = false;

            foreach (Cell cell in map.GetCells(location, 0, 1))
            {
                if (cell == null) continue;
                if (cell.Objects != null && cell.Objects.OfType<SpellObject>().Any(x => x.Effect == SpellEffect.CrystalHealingCircle))
                    continue;

                SpellObject ob = new SpellObject
                {
                    DisplayLocation = cell.Location,
                    Effect = SpellEffect.CrystalHealingCircle,
                    TickCount = ticks,
                    TickFrequency = TimeSpan.FromMilliseconds(400),
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
            // Field creation trains the spell once; hostile ticks must not award extra training.
        }
    }
}
