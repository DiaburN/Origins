using Library;
using Server.DBModels;
using Server.Envir;
using System;
using System.Collections.Generic;
using System.Drawing;

namespace Server.Models.Magics
{
    [MagicType(MagicType.TrapHexagon)]
    public sealed class TrapHexagon : MagicObject
    {
        protected override Element Element => Element.None;
        public override bool UpdateCombatTime => false;

        public TrapHexagon(PlayerObject player, UserMagic magic) : base(player, magic) { }

        public override MagicCast MagicCast(MapObject target, Point location, MirDirection direction)
        {
            var response = new MagicCast { Ob = null };
            if (!Functions.InRange(CurrentLocation, location, Globals.MagicRange))
            {
                response.Cast = false;
                return response;
            }

            List<MonsterObject> candidates = GetCrystalTargets(CurrentMap, location);
            if (candidates.Count == 0 || !Player.UseAmulet(1, 0))
            {
                response.Cast = false;
                return response;
            }

            // Crystal levels the skill as soon as a valid trap cast is accepted.
            Player.LevelMagic(Magic);

            int durationMilliseconds = (Magic.Level * 5 + 10) * 1000;
            ActionList.Add(new DelayedAction(
                SEnvir.Now.AddMilliseconds(500),
                ActionType.DelayMagic,
                Type,
                CurrentMap,
                location,
                durationMilliseconds));

            return response;
        }

        public override void MagicComplete(params object[] data)
        {
            Map map = (Map)data[1];
            Point location = (Point)data[2];
            int durationMilliseconds = (int)data[3];
            if (map != CurrentMap) return;

            DateTime shockUntil = SEnvir.Now.AddMilliseconds(durationMilliseconds);
            foreach (MonsterObject monster in GetCrystalTargets(map, location))
            {
                if (shockUntil > monster.ShockTime)
                    monster.ShockTime = shockUntil;
                monster.Target = null;
            }

            // The six-point Crystal trap artwork is intentionally left to the
            // client/effect overlay pass; runtime control is carried by ShockTime.
        }

        private List<MonsterObject> GetCrystalTargets(Map map, Point location)
        {
            var result = new List<MonsterObject>();
            foreach (Cell cell in map.GetCells(location, 0, 1))
            {
                if (cell?.Objects == null) continue;
                for (int i = cell.Objects.Count - 1; i >= 0; i--)
                {
                    if (cell.Objects[i] is not MonsterObject monster) continue;
                    if (!Player.CanAttackTarget(monster)) continue;
                    if (monster.Level > Player.Level + 2) continue;
                    result.Add(monster);
                }
            }
            return result;
        }
    }
}
