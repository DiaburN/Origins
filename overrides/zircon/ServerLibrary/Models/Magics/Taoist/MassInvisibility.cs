using Library;
using Server.DBModels;
using Server.Envir;
using System;
using System.Drawing;

namespace Server.Models.Magics
{
    // Crystal MassHiding mapped to Zircon MassInvisibility.
    [MagicType(MagicType.MassInvisibility)]
    public sealed class MassInvisibility : MagicObject
    {
        protected override Element Element => Element.None;
        public override bool UpdateCombatTime => false;

        public MassInvisibility(PlayerObject player, UserMagic magic) : base(player, magic) { }

        public override MagicCast MagicCast(MapObject target, Point location, MirDirection direction)
        {
            var response = new MagicCast { Ob = null };

            // Crystal checks for one amulet here but, unlike Hiding/SoulShield, does not consume it.
            if (!Functions.InRange(CurrentLocation, location, Globals.MagicRange) || !Player.HasAmulet(1, 0))
            {
                response.Cast = false;
                return response;
            }

            response.Locations.Add(location);
            int durationSeconds = Player.GetSC() / 2 + (Magic.Level + 1) * 2;
            int delay = 500 + Functions.Distance(CurrentLocation, location) * 50;
            ActionList.Add(new DelayedAction(SEnvir.Now.AddMilliseconds(delay), ActionType.DelayMagic, Type, CurrentMap, location, durationSeconds));
            return response;
        }

        public override void MagicComplete(params object[] data)
        {
            Map map = (Map)data[1];
            Point location = (Point)data[2];
            int durationSeconds = (int)data[3];
            if (map != CurrentMap) return;

            bool trained = false;
            foreach (Cell cell in map.GetCells(location, 0, 1))
            {
                if (cell?.Objects == null) continue;
                for (int i = cell.Objects.Count - 1; i >= 0; i--)
                {
                    MapObject ob = cell.Objects[i];
                    if (ob?.Node == null || !Player.CanHelpTarget(ob)) continue;

                    ob.BuffAdd(BuffType.Invisibility, TimeSpan.FromSeconds(durationSeconds), new Stats { [Stat.Invisibility] = 1 }, true, false, TimeSpan.Zero);
                    trained = true;
                }
            }

            if (trained) Player.LevelMagic(Magic);
        }
    }
}
