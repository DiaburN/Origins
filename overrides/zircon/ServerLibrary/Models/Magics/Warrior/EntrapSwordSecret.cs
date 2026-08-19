using Library;
using Server.DBModels;
using Server.Envir;
using System;
using System.Drawing;

namespace Server.Models.Magics
{
    [MagicType(MagicType.EntrapSwordSecret)]
    public sealed class EntrapSwordSecret : MagicObject
    {
        protected override Element Element => Element.None;

        public EntrapSwordSecret(PlayerObject player, UserMagic magic) : base(player, magic)
        {
        }

        public override MagicCast MagicCast(MapObject target, Point location, MirDirection direction)
        {
            var response = new MagicCast { Ob = target, Direction = direction };

            if (target == null || !Player.CanAttackTarget(target))
            {
                response.Ob = null;
                return response;
            }

            response.Targets.Add(target.ObjectID);

            ActionList.Add(new DelayedAction(
                SEnvir.Now.AddMilliseconds(500),
                ActionType.DelayMagic,
                Type,
                target,
                direction));

            return response;
        }

        public override void MagicComplete(params object[] data)
        {
            MapObject target = (MapObject)data[1];
            MirDirection castDirection = (MirDirection)data[2];

            if (target?.Node == null || target.CurrentMap != CurrentMap) return;
            if (!Player.CanAttackTarget(target)) return;
            if (target.Race != ObjectType.Monster && target.Race != ObjectType.Player) return;
            if (!Functions.InRange(CurrentLocation, target.CurrentLocation, 7)) return;
            if (target.Level >= Player.Level + 5 + SEnvir.Random.Next(8)) return;

            MirDirection pullDirection = Functions.ShiftDirection(castDirection, 4);
            int dx = Math.Abs(CurrentLocation.X - target.CurrentLocation.X);
            int dy = Math.Abs(CurrentLocation.Y - target.CurrentLocation.Y);

            int pullDistance;
            if (((int)pullDirection & 1) != 0)
                pullDistance = Math.Max(0, Math.Min(dx, dy));
            else
                pullDistance = Math.Max(0, (pullDirection == MirDirection.Up || pullDirection == MirDirection.Down ? dy : dx) - 2);

            // Crystal-Monk calculates levelGap here but does not perform the
            // random success gate used by normal Entrapment. Preserve that
            // source behaviour rather than silently adding the missing roll.
            int duration = target.Race == ObjectType.Player
                ? (int)Math.Round((Magic.Level + 1) * 1.6D)
                : (int)Math.Round((Magic.Level + 1) * 0.8D);

            if (duration > 0)
            {
                target.ApplyPoison(new Poison
                {
                    Type = PoisonType.Paralysis,
                    Owner = Player,
                    TickCount = 1,
                    TickFrequency = TimeSpan.FromSeconds(duration),
                });
            }

            if (target.Pushed(pullDirection, pullDistance) > 0)
                Player.LevelMagic(Magic);
        }
    }
}
