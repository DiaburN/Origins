using Library;
using Library.Network.ServerPackets;
using Server.DBModels;
using Server.Envir;
using System;
using System.Collections.Generic;
using System.Drawing;

namespace Server.Models.Magics
{
    [MagicType(MagicType.ShoulderDash)]
    public sealed class ShoulderDash : MagicObject
    {
        protected override Element Element => Element.None;
        public override bool IgnoreAccuracy => true;
        public override bool IgnorePhysicalDefense => true;

        public ShoulderDash(PlayerObject player, UserMagic magic) : base(player, magic)
        {
        }

        public override MagicCast MagicCast(MapObject target, Point location, MirDirection direction)
        {
            var response = new MagicCast
            {
                Ob = null,
                Direction = direction,
                Return = true,
            };

            if (!Player.CanMove || Player.Dead) return response;
            if (!CheckCost() || SEnvir.Now < Magic.Cooldown) return response;

            Player.Direction = direction;

            int distance = SEnvir.Random.Next(2) + Magic.Level + 2;
            int travelled = 0;
            MapObject pushedTarget = null;

            for (int step = 0; step < distance; step++)
            {
                Point next = Functions.Move(CurrentLocation, direction);
                Cell cell = CurrentMap.GetCell(next);
                if (cell == null) break;

                bool blocked = false;

                if (step == 0 && cell.Objects != null)
                {
                    for (int i = cell.Objects.Count - 1; i >= 0; i--)
                    {
                        MapObject ob = cell.Objects[i];
                        if (!ob.Blocking) continue;

                        if (pushedTarget == null && Player.CanAttackTarget(ob) && ob.Level < Player.Level)
                        {
                            pushedTarget = ob;
                            continue;
                        }

                        blocked = true;
                        break;
                    }
                }

                if (blocked) break;

                if (pushedTarget != null)
                {
                    if (pushedTarget.Pushed(direction, 1) == 0)
                        break;
                }
                else if (cell.Objects != null)
                {
                    for (int i = cell.Objects.Count - 1; i >= 0; i--)
                    {
                        if (!cell.Objects[i].Blocking) continue;
                        blocked = true;
                        break;
                    }
                    if (blocked) break;
                }

                Player.CurrentCell = cell.GetMovement(Player);
                Player.RemoveAllObjects();
                Player.AddAllObjects();
                Player.Broadcast(new ObjectDash
                {
                    ObjectID = Player.ObjectID,
                    Direction = direction,
                    Location = CurrentLocation,
                    Distance = 1,
                    Magic = Type,
                });

                travelled++;
            }

            if (travelled > 0)
            {
                if (pushedTarget?.Node != null && !pushedTarget.Dead)
                    Player.Attack(pushedTarget, new List<MagicType> { Type }, true, Magic.GetPower());

                Player.LevelMagic(Magic);
            }

            MagicConsume();
            MagicCooldown();
            Player.ActionTime = SEnvir.Now.AddMilliseconds(600);

            return response;
        }

        public override int ModifyPowerAdditionner(bool primary, int power, MapObject ob, Stats stats = null, int extra = 0)
        {
            return extra > 0 ? extra : Magic.GetPower();
        }

        public override void AttackComplete(MapObject target)
        {
            // ShoulderDash trains once if at least one cell was travelled.
        }
    }
}
