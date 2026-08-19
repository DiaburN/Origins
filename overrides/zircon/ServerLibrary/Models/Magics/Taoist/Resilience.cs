using Library;
using Server.DBModels;
using Server.Envir;
using System;
using System.Drawing;

namespace Server.Models.Magics
{
    [MagicType(MagicType.Resilience)]
    public class Resilience : MagicObject
    {
        protected override Element Element => Element.None;
        public override bool UpdateCombatTime => false;

        public Resilience(PlayerObject player, UserMagic magic) : base(player, magic) { }

        public override MagicCast MagicCast(MapObject target, Point location, MirDirection direction)
        {
            var response = new MagicCast { Ob = null };

            if (!Functions.InRange(CurrentLocation, location, Globals.MagicRange) || !Player.UseAmulet(1, 0))
            {
                response.Cast = false;
                return response;
            }

            response.Locations.Add(location);

            int durationSeconds = Player.GetSC() * 4 + (Magic.Level + 1) * 50;
            var delay = SEnvir.Now.AddMilliseconds(500 + Functions.Distance(CurrentLocation, location) * 50);

            foreach (Cell cell in CurrentMap.GetCells(location, 0, 3))
                ActionList.Add(new DelayedAction(delay, ActionType.DelayMagic, Type, cell, durationSeconds));

            return response;
        }

        public override void MagicComplete(params object[] data)
        {
            Cell cell = (Cell)data[1];
            int durationSeconds = (int)data[2];

            if (cell?.Objects == null) return;

            bool trained = false;

            for (int i = cell.Objects.Count - 1; i >= 0; i--)
            {
                MapObject ob = cell.Objects[i];
                if (ob?.Node == null || !Player.CanHelpTarget(ob)) continue;

                Stats stats = new Stats
                {
                    [Stat.MaxAC] = ob.Level / 7 + 4
                };

                ob.BuffAdd(BuffType.Resilience, TimeSpan.FromSeconds(durationSeconds), stats, true, false, TimeSpan.Zero);
                trained = true;
            }

            if (trained)
                Player.LevelMagic(Magic);
        }
    }
}
