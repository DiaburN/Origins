using Library;
using Server.DBModels;
using Server.Envir;
using System;
using System.Collections.Generic;
using System.Drawing;

namespace Server.Models.Magics
{
    [MagicType(MagicType.IceThrust)]
    public sealed class IceThrust : MagicObject
    {
        protected override Element Element => Element.Ice;

        public IceThrust(PlayerObject player, UserMagic magic) : base(player, magic)
        {
        }

        public override MagicCast MagicCast(MapObject target, Point location, MirDirection direction)
        {
            var response = new MagicCast { Ob = null };

            Point first = Functions.Move(CurrentLocation, direction);
            Point[] starts =
            {
                Functions.Move(first, Functions.ShiftDirection(direction, -1)),
                Functions.Move(first, direction),
                Functions.Move(first, Functions.ShiftDirection(direction, 1)),
            };

            for (int col = 0; col < starts.Length; col++)
            {
                for (int row = 0; row < 3; row++)
                {
                    Point point = Functions.Move(starts[col], direction, row);
                    Cell cell = CurrentMap.GetCell(point);
                    if (cell == null) continue;
                    response.Locations.Add(point);
                }
            }

            int nearDamage = Magic.GetPower() + Player.GetMC();
            if (SEnvir.Random.Next(100) < 1 + Player.Stats[Stat.Luck])
                nearDamage *= 2;

            int farDamage = (int)(nearDamage * 0.6F);

            ActionList.Add(new DelayedAction(
                SEnvir.Now.AddMilliseconds(1500),
                ActionType.DelayMagic,
                Type,
                first,
                direction,
                nearDamage,
                farDamage));

            return response;
        }

        public override void MagicComplete(params object[] data)
        {
            Point first = (Point)data[1];
            MirDirection direction = (MirDirection)data[2];
            int nearDamage = (int)data[3];
            int farDamage = (int)data[4];
            bool train = false;

            Point[] starts =
            {
                Functions.Move(first, Functions.ShiftDirection(direction, -1)),
                Functions.Move(first, direction),
                Functions.Move(first, Functions.ShiftDirection(direction, 1)),
            };

            for (int col = 0; col < starts.Length; col++)
            {
                for (int row = 0; row < 3; row++)
                {
                    Point point = Functions.Move(starts[col], direction, row);
                    Cell cell = CurrentMap.GetCell(point);
                    if (cell?.Objects == null) continue;

                    int damage = row <= 1 ? nearDamage : farDamage;

                    for (int i = cell.Objects.Count - 1; i >= 0; i--)
                    {
                        if (i >= cell.Objects.Count) continue;

                        MapObject ob = cell.Objects[i];
                        if (ob.Race != ObjectType.Player && ob.Race != ObjectType.Monster) continue;
                        if (!Player.CanAttackTarget(ob)) continue;

                        if (Player.MagicAttack(new List<MagicType> { Type }, ob, true, null, damage) <= 0) continue;
                        train = true;

                        bool playerTarget = ob.Race == ObjectType.Player;
                        int levelAllowance = playerTarget ? 2 : 10;

                        if (Player.Level + levelAllowance >= ob.Level &&
                            SEnvir.Random.Next(playerTarget ? 100 : 20) <= Magic.Level)
                        {
                            int slowDuration = playerTarget ? 4 : 5 + SEnvir.Random.Next(5);
                            ob.ApplyPoison(new Poison
                            {
                                Type = PoisonType.Slow,
                                Owner = Player,
                                Value = 10,
                                TickCount = slowDuration,
                                TickFrequency = TimeSpan.FromSeconds(1),
                            });
                        }

                        if (Player.Level + levelAllowance >= ob.Level &&
                            SEnvir.Random.Next(playerTarget ? 100 : 40) <= Magic.Level)
                        {
                            int freezing = Math.Max(1, Player.Stats[Stat.Freezing]);
                            int frozenDuration = playerTarget ? 2 : 5 + SEnvir.Random.Next(freezing);
                            ob.ApplyPoison(new Poison
                            {
                                Type = PoisonType.Frozen,
                                Owner = Player,
                                TickCount = frozenDuration,
                                TickFrequency = TimeSpan.FromSeconds(1),
                            });
                        }
                    }
                }
            }

            if (train)
                Player.LevelMagic(Magic);
        }

        public override void MagicAttackSuccess(MapObject ob, int damageDealt)
        {
            // Crystal trains IceThrust once per successful frontal cast.
        }

        public override int ModifyPowerAdditionner(bool primary, int power, MapObject ob, Stats stats = null, int extra = 0)
        {
            power += extra != 0 ? extra : Magic.GetPower() + Player.GetMC();
            return power;
        }
    }
}
