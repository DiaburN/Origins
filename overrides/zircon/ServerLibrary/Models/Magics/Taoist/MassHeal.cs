using Library;
using Server.DBModels;
using Server.Envir;
using System;
using System.Drawing;
using System.Linq;

namespace Server.Models.Magics
{
    [MagicType(MagicType.MassHeal)]
    public class MassHeal : MagicObject
    {
        protected override Element Element => Element.None;
        public override bool UpdateCombatTime => false;

        public MassHeal(PlayerObject player, UserMagic magic) : base(player, magic) { }

        public override MagicCast MagicCast(MapObject target, Point location, MirDirection direction)
        {
            var response = new MagicCast { Ob = null };

            if (!Functions.InRange(CurrentLocation, location, Globals.MagicRange))
            {
                response.Cast = false;
                return response;
            }

            response.Locations.Add(location);

            // Crystal: magic.GetDamage(GetAttackPower(MinSC, MaxSC)).
            int healingPool = Magic.GetPower() + Player.GetSC();
            var delay = SEnvir.Now.AddMilliseconds(500);

            foreach (Cell cell in CurrentMap.GetCells(location, 0, 1))
                ActionList.Add(new DelayedAction(delay, ActionType.DelayMagic, Type, cell, healingPool));

            return response;
        }

        public override void MagicComplete(params object[] data)
        {
            Cell cell = (Cell)data[1];
            int healingPool = (int)data[2];

            if (cell?.Objects == null || healingPool <= 0) return;

            bool trained = false;

            for (int i = cell.Objects.Count - 1; i >= 0; i--)
            {
                MapObject ob = cell.Objects[i];
                if (ob?.Node == null || !Player.CanHelpTarget(ob) || ob.CurrentHP >= ob.Stats[Stat.Health]) continue;

                BuffInfo existing = ob.Buffs.FirstOrDefault(x => x.Type == BuffType.CrystalHealing);
                if (existing == null)
                {
                    ob.BuffAdd(
                        BuffType.CrystalHealing,
                        TimeSpan.MaxValue,
                        new Stats { [Stat.Healing] = healingPool },
                        false,
                        false,
                        TimeSpan.FromMilliseconds(600));
                }
                else
                {
                    existing.Stats[Stat.Healing] += healingPool;
                }

                trained = true;
            }

            if (trained)
                Player.LevelMagic(Magic);
        }
    }
}
