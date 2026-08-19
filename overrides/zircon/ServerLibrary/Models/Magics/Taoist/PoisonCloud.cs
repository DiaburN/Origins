using Library;
using Server.DBModels;
using Server.Envir;
using System;
using System.Drawing;
using System.Linq;

namespace Server.Models.Magics
{
    [MagicType(MagicType.PoisonCloud)]
    public class PoisonCloud : MagicObject
    {
        protected override Element Element => Element.None;
        public override bool UpdateCombatTime => false;

        public PoisonCloud(PlayerObject player, UserMagic magic) : base(player, magic) { }

        public override MagicCast MagicCast(MapObject target, Point location, MirDirection direction)
        {
            var response = new MagicCast { Ob = null };

            if (!Functions.InRange(CurrentLocation, location, Globals.MagicRange) || !Player.UseAmulet(5, 0))
            {
                response.Cast = false;
                return response;
            }

            // Crystal PoisonCloud additionally requires five green-poison charges.
            if (!Player.UsePoison(5, out _, 0))
            {
                response.Cast = false;
                return response;
            }

            response.Locations.Add(location);

            int power = Magic.GetPower() + Player.GetSC();
            int bonus = Player.Stats[Stat.PoisonAttack] > 0
                ? SEnvir.Random.Next(Player.Stats[Stat.PoisonAttack])
                : 0;

            ActionList.Add(new DelayedAction(
                SEnvir.Now.AddMilliseconds(500 + Functions.Distance(CurrentLocation, location) * 50),
                ActionType.DelayMagic,
                Type,
                CurrentMap,
                location,
                power,
                bonus));

            return response;
        }

        public override void MagicComplete(params object[] data)
        {
            Map map = (Map)data[1];
            Point location = (Point)data[2];
            int power = (int)data[3];
            int bonus = (int)data[4];

            if (map != CurrentMap) return;

            bool spawned = false;
            foreach (Cell cell in map.GetCells(location, 0, 1))
            {
                if (cell == null) continue;
                if (cell.Objects != null && cell.Objects.OfType<SpellObject>().Any(x => x.Effect == SpellEffect.CrystalPoisonCloud))
                    continue;

                SpellObject ob = new SpellObject
                {
                    DisplayLocation = cell.Location,
                    Effect = SpellEffect.CrystalPoisonCloud,
                    TickCount = 6,
                    TickFrequency = TimeSpan.FromSeconds(1),
                    TickTime = SEnvir.Now,
                    Owner = Player,
                    Magic = Magic,
                    Power = power,
                    CrystalBonusPower = bonus,
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
            // Crystal trains once when the cloud field is created, not once per tick/target.
        }
    }
}
