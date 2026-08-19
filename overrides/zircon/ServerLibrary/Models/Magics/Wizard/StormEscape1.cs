using Library;
using Server.DBModels;
using Server.Envir;
using System;
using System.Collections.Generic;
using System.Drawing;

namespace Server.Models.Magics
{
    [MagicType(MagicType.StormEscape1)]
    public sealed class StormEscape1 : MagicObject
    {
        protected override Element Element => Element.Lightning;

        public StormEscape1(PlayerObject player, UserMagic magic) : base(player, magic)
        {
        }

        public override MagicCast MagicCast(MapObject target, Point location, MirDirection direction)
        {
            var response = new MagicCast { Ob = null };

            Map castMap = CurrentMap;
            Point center = CurrentLocation;
            int castPower = Magic.GetPower() + Player.GetMC();

            foreach (Cell cell in castMap.GetCells(center, 0, 2))
            {
                if (cell == null) continue;
                response.Locations.Add(cell.Location);
            }

            response.Locations.Add(location);

            ActionList.Add(new DelayedAction(
                SEnvir.Now.AddMilliseconds(500),
                ActionType.DelayMagic,
                Type,
                castMap,
                center,
                castPower,
                0));

            ActionList.Add(new DelayedAction(
                SEnvir.Now.AddMilliseconds(750),
                ActionType.DelayMagic,
                Type,
                castMap,
                location,
                0,
                1));

            return response;
        }

        public override void MagicComplete(params object[] data)
        {
            Map castMap = (Map)data[1];
            Point location = (Point)data[2];
            int castPower = (int)data[3];
            int phase = (int)data[4];

            if (castMap == null) return;

            if (phase == 0)
            {
                bool train = false;

                foreach (Cell cell in castMap.GetCells(location, 0, 2))
                {
                    if (cell?.Objects == null) continue;

                    for (int i = cell.Objects.Count - 1; i >= 0; i--)
                    {
                        if (i >= cell.Objects.Count) continue;

                        MapObject ob = cell.Objects[i];
                        if (ob.Race != ObjectType.Player && ob.Race != ObjectType.Monster) continue;
                        if (!Player.CanAttackTarget(ob)) continue;

                        if (Player.MagicAttack(new List<MagicType> { Type }, ob, true, null, castPower) > 0)
                            train = true;
                    }
                }

                if (train)
                    Player.LevelMagic(Magic);

                return;
            }

            if (Player.CurrentMap != castMap) return;
            if (castMap.Info.NoTeleport) return;
            if (castMap.GetCell(location) == null) return;
            if (SEnvir.Random.Next(2) >= Magic.Level + 1) return;
            if (!Player.Teleport(castMap, location, false)) return;

            Player.BuffAdd(
                BuffType.TemporalFlux,
                TimeSpan.FromSeconds(30),
                new Stats { [Stat.TeleportManaPenaltyPercent] = 30 },
                true,
                false,
                TimeSpan.Zero);

            Player.BuffAdd(
                BuffType.StormEscape,
                TimeSpan.FromSeconds(20),
                new Stats { [Stat.AttackPowerPercent] = 10 },
                true,
                false,
                TimeSpan.Zero);

            Player.LevelMagic(Magic);
        }

        public override void MagicAttackSuccess(MapObject ob, int damageDealt)
        {
            // Crystal-Monk trains the area phase once; teleport success has its own LevelMagic call.
        }

        public override int ModifyPowerAdditionner(bool primary, int power, MapObject ob, Stats stats = null, int extra = 0)
        {
            power += extra != 0 ? extra : Magic.GetPower() + Player.GetMC();
            return power;
        }
    }
}
