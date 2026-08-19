using Library;
using Server.DBModels;
using Server.Envir;
using System;
using System.Collections.Generic;
using System.Drawing;
using System.Linq;

namespace Server.Models.Magics
{
    [MagicType(MagicType.FireWall)]
    public class FireWall : MagicObject
    {
        private int _castSequence;

        protected override Element Element => Element.Fire;
        public override bool CanStruck => false;

        public FireWall(PlayerObject player, UserMagic magic) : base(player, magic)
        {
        }

        public override MagicCast MagicCast(MapObject target, Point location, MirDirection direction)
        {
            var response = new MagicCast
            {
                Ob = null
            };

            if (!Functions.InRange(Player.CurrentLocation, location, Globals.MagicRange))
            {
                response.Cast = false;
                return response;
            }

            if (CurrentMap.Info.FireWallLimit && CurrentMap.Info.FireWallCount > 0)
            {
                List<SpellObject> activeFireWalls = Player.SpellList
                    .Where(x => x.Effect == SpellEffect.FireWall && x.CurrentMap == CurrentMap)
                    .ToList();

                int activeCasts = activeFireWalls.Count == 0
                    ? 0
                    : activeFireWalls.Select(x => x.CastInstanceId).Distinct().Count();

                if (activeCasts >= CurrentMap.Info.FireWallCount)
                {
                    IGrouping<int, SpellObject> oldest = activeFireWalls
                        .GroupBy(x => x.CastInstanceId)
                        .OrderBy(x => x.Key == 0 ? int.MinValue : x.Key)
                        .FirstOrDefault();

                    if (oldest != null)
                    {
                        foreach (SpellObject spell in oldest.ToList())
                            spell.Despawn();
                    }
                }
            }

            int power = Magic.GetPower() + Player.GetMC();
            int castId = ++_castSequence;
            DateTime delay = SEnvir.Now.AddMilliseconds(500);

            Cell[] cells =
            {
                CurrentMap.GetCell(location),
                CurrentMap.GetCell(Functions.Move(location, MirDirection.Up)),
                CurrentMap.GetCell(Functions.Move(location, MirDirection.Down)),
                CurrentMap.GetCell(Functions.Move(location, MirDirection.Left)),
                CurrentMap.GetCell(Functions.Move(location, MirDirection.Right))
            };

            for (int i = 0; i < cells.Length; i++)
            {
                ActionList.Add(new DelayedAction(
                    delay,
                    ActionType.DelayMagic,
                    Type,
                    cells[i],
                    castId,
                    power,
                    i == 0));
            }

            return response;
        }

        public override void MagicComplete(params object[] data)
        {
            Cell cell = (Cell)data[1];
            int castId = (int)data[2];
            int power = (int)data[3];
            bool train = (bool)data[4];

            if (train)
                Player.LevelMagic(Magic);

            if (cell == null) return;

            if (cell.Objects != null && cell.Objects.Any(x => x is SpellObject spell && spell.Effect == SpellEffect.FireWall))
                return;

            SpellObject ob = new SpellObject
            {
                DisplayLocation = cell.Location,
                TickCount = int.MaxValue,
                TickFrequency = TimeSpan.FromSeconds(2),
                TickTime = SEnvir.Now,
                ExpireTime = SEnvir.Now.AddSeconds(10 + power / 2),
                Owner = Player,
                Effect = SpellEffect.FireWall,
                Magic = Magic,
                Power = power,
                CastInstanceId = castId
            };

            ob.Spawn(cell.Map, cell.Location);
        }

        public override int ModifyPowerAdditionner(bool primary, int power, MapObject ob, Stats stats = null, int extra = 0)
        {
            return extra > 0 ? extra : Magic.GetPower() + Player.GetMC();
        }

        public override int ModifyPowerMultiplier(bool primary, int power, Stats stats = null, int extra = 0)
        {
            return power;
        }

        public override void MagicAttackSuccess(MapObject ob, int damageDealt)
        {
            // Crystal levels FireWall once when the cast is created, not once per tick/target.
        }
    }
}
