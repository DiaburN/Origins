using Library;
using Server.DBModels;
using Server.Envir;
using System.Collections.Generic;
using System.Drawing;

namespace Server.Models.Magics
{
    [MagicType(MagicType.FrostCrunch)]
    public class FrostCrunch : MagicObject
    {
        protected override Element Element => Element.Ice;

        public FrostCrunch(PlayerObject player, UserMagic magic) : base(player, magic)
        {
        }

        public override MagicCast MagicCast(MapObject target, Point location, MirDirection direction)
        {
            var response = new MagicCast { Ob = target };

            if (!Player.CanAttackTarget(target))
            {
                response.Ob = null;
                response.Locations.Add(location);
                return response;
            }

            Point lockedLocation = target.CurrentLocation;
            if (!CanFly(lockedLocation))
            {
                response.Cast = false;
                response.Ob = null;
                return response;
            }

            response.Targets.Add(target.ObjectID);

            int castPower = Magic.GetPower() + Player.GetMC();
            int delayMilliseconds = 500 + Functions.Distance(CurrentLocation, lockedLocation) * 50;

            ActionList.Add(new DelayedAction(
                SEnvir.Now.AddMilliseconds(delayMilliseconds),
                ActionType.DelayMagic,
                Type,
                target,
                lockedLocation,
                castPower));

            return response;
        }

        public override void MagicComplete(params object[] data)
        {
            MapObject target = (MapObject)data[1];
            Point lockedLocation = (Point)data[2];
            int castPower = (int)data[3];

            if (target?.Node == null || target.CurrentMap != CurrentMap) return;
            if (Functions.Distance(target.CurrentLocation, lockedLocation) > 2) return;

            Player.MagicAttack(new List<MagicType> { Type }, target, true, null, castPower);
        }

        public override int ModifyPowerAdditionner(bool primary, int power, MapObject ob, Stats stats = null, int extra = 0)
        {
            power += extra != 0 ? extra : Magic.GetPower() + Player.GetMC();
            return power;
        }

        private bool CanFly(Point destination)
        {
            Point current = CurrentLocation;

            while (current != destination)
            {
                MirDirection direction = Functions.DirectionFromPoint(current, destination);
                Point next = Functions.Move(current, direction);

                if (next == current) return false;
                if (next.X < 0 || next.Y < 0 || next.X >= CurrentMap.Width || next.Y >= CurrentMap.Height) return false;
                if (CurrentMap.Cells[next.X, next.Y] == null) return false;

                current = next;
            }

            return true;
        }
    }
}
