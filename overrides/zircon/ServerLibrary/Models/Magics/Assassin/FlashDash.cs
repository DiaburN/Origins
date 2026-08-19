using Library;
using Library.Network;
using Server.DBModels;
using Server.Envir;
using System;
using System.Drawing;
using S = Library.Network.ServerPackets;

namespace Server.Models.Magics
{
    public abstract class CrystalFlashDashBase : MagicObject
    {
        protected override Element Element => Element.None;
        protected virtual bool ForceStun => false;

        protected CrystalFlashDashBase(PlayerObject player, UserMagic magic) : base(player, magic) { }

        public override MagicCast MagicCast(MapObject target, Point location, MirDirection direction)
        {
            var response = new MagicCast { Ob = null, Return = true };

            Player.Direction = direction;

            // Crystal only moves one cell at magic level 2+; levels 0/1 attack from the current cell.
            int jumpDistance = Magic.Level <= 1 ? 0 : 1;
            int travelled = 0;

            if (jumpDistance > 0)
            {
                Cell next = CurrentMap.GetCell(Functions.Move(CurrentLocation, direction));
                bool blocked = next == null || next.Movements != null;

                if (!blocked && next.Objects != null)
                {
                    foreach (MapObject ob in next.Objects)
                    {
                        if (ob.Blocking)
                        {
                            blocked = true;
                            break;
                        }
                    }
                }

                if (!blocked)
                {
                    Player.CurrentCell = next.GetMovement(Player);
                    Player.RemoveAllObjects();
                    Player.AddAllObjects();
                    travelled = 1;

                    Player.Broadcast(new S.ObjectDash
                    {
                        ObjectID = Player.ObjectID,
                        Direction = direction,
                        Location = Player.CurrentLocation,
                        Distance = 1,
                        Magic = Type,
                    });
                }
            }

            Point hitLocation = Functions.Move(Player.CurrentLocation, direction);
            Cell hitCell = CurrentMap.GetCell(hitLocation);
            if (hitCell?.Objects == null)
                return response;

            MapObject hitTarget = null;
            foreach (MapObject ob in hitCell.Objects)
            {
                if (ob?.Node == null || (ob.Race != ObjectType.Player && ob.Race != ObjectType.Monster) || !Player.CanAttackTarget(ob)) continue;
                hitTarget = ob;
                break;
            }

            if (hitTarget == null)
                return response;

            response.Targets.Add(hitTarget.ObjectID);

            int attackDelay = Globals.AttackDelay - Player.Stats[Stat.AttackSpeed] * Globals.ASpeedRate - 120;
            attackDelay = Math.Max(300, attackDelay);
            Player.AttackTime = SEnvir.Now.AddMilliseconds(attackDelay);
            Player.ActionTime = SEnvir.Now.AddMilliseconds(attackDelay);

            int power = Magic.GetPower() + Player.GetDC();
            int damage = Math.Max(0, power - hitTarget.GetAC());
            if (damage > 0)
            {
                Player.ActionList.Add(new DelayedAction(
                    Player.AttackTime,
                    ActionType.DelayedAttackDamage,
                    hitTarget,
                    damage,
                    Element.None,
                    true,
                    true,
                    false,
                    true));
            }

            bool stun = ForceStun;
            if (!stun && hitTarget.Race != ObjectType.Player)
            {
                // Base Crystal FlashDash: poison resistance gate plus level-scaled 15-point roll.
                int resistance = Math.Max(0, hitTarget.Stats[Stat.PoisonResistance]);
                stun = SEnvir.Random.Next(100) >= resistance && SEnvir.Random.Next(15) <= Magic.Level + 1;
            }

            if (stun)
            {
                hitTarget.ApplyPoison(new Poison
                {
                    Owner = Player,
                    Type = PoisonType.Paralysis,
                    TickCount = hitTarget.Race == ObjectType.Player ? 2 : Math.Max(1, Magic.Level),
                    TickFrequency = TimeSpan.FromSeconds(1),
                });
            }

            Player.LevelMagic(Magic);
            return response;
        }
    }

    [MagicType(MagicType.FlashDash)]
    public sealed class FlashDash : CrystalFlashDashBase
    {
        public FlashDash(PlayerObject player, UserMagic magic) : base(player, magic) { }
    }
}
