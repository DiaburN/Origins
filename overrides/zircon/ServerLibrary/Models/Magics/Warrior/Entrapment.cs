using Library;
using Server.DBModels;
using Server.Envir;
using System;
using System.Drawing;

namespace Server.Models.Magics
{
    [MagicType(MagicType.Entrapment)]
    public sealed class Entrapment : MagicObject
    {
        protected override Element Element => Element.None;

        public Entrapment(PlayerObject player, UserMagic magic) : base(player, magic)
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
            if (!Player.CanAttackTarget(target) || target.Race != ObjectType.Monster) return;
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

            int levelGap = Player.Level - target.Level + 9;
            if (SEnvir.Random.Next(30) >= (Magic.Level + 1) * 3 + levelGap) return;

            int duration = (int)Math.Round((Magic.Level + 1) * 0.8D);
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
