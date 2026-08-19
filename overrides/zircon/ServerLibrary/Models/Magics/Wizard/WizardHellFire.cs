using Library;
using Server.DBModels;
using Server.Envir;
using System.Collections.Generic;
using System.Drawing;

namespace Server.Models.Magics
{
    [MagicType(MagicType.WizardHellFire)]
    public class WizardHellFire : MagicObject
    {
        protected override Element Element => Element.Fire;

        public WizardHellFire(PlayerObject player, UserMagic magic) : base(player, magic)
        {
        }

        public override MagicCast MagicCast(MapObject target, Point location, MirDirection direction)
        {
            var response = new MagicCast
            {
                Ob = null
            };

            int castPower = Magic.GetPower() + Player.GetMC();
            DateTime delay = SEnvir.Now.AddMilliseconds(500);

            QueueLine(response, delay, CurrentLocation, direction, castPower);

            if (Magic.Level == 3)
            {
                QueueLine(response, delay, CurrentLocation, Functions.ShiftDirection(direction, 1), castPower);
                QueueLine(response, delay, CurrentLocation, Functions.ShiftDirection(direction, -1), castPower);
            }

            return response;
        }

        private void QueueLine(MagicCast response, DateTime delay, Point origin, MirDirection direction, int castPower)
        {
            Point point = origin;
            for (int i = 0; i < 4; i++)
            {
                point = Functions.Move(point, direction);
                if (point.X < 0 || point.Y < 0 || point.X >= CurrentMap.Width || point.Y >= CurrentMap.Height) break;
                response.Locations.Add(point);
            }

            ActionList.Add(new DelayedAction(
                delay,
                ActionType.DelayMagic,
                Type,
                origin,
                direction,
                4,
                castPower));
        }

        public override void MagicComplete(params object[] data)
        {
            Point origin = (Point)data[1];
            MirDirection direction = (MirDirection)data[2];
            int remaining = (int)data[3];
            int castPower = (int)data[4];

            Point next = Functions.Move(origin, direction);
            if (next.X < 0 || next.Y < 0 || next.X >= CurrentMap.Width || next.Y >= CurrentMap.Height) return;

            if (remaining > 1)
            {
                ActionList.Add(new DelayedAction(
                    SEnvir.Now.AddMilliseconds(100),
                    ActionType.DelayMagic,
                    Type,
                    next,
                    direction,
                    remaining - 1,
                    castPower));
            }

            Cell cell = CurrentMap.GetCell(next);
            if (cell?.Objects == null) return;

            bool train = false;
            for (int i = cell.Objects.Count - 1; i >= 0; i--)
            {
                MapObject ob = cell.Objects[i];
                if (!Player.CanAttackTarget(ob)) continue;

                if (Player.MagicAttack(new List<MagicType> { Type }, ob, true, null, castPower) > 0)
                    train = true;
            }

            // Crystal's map action trains once per successful HellFire step.
            if (train)
                Player.LevelMagic(Magic);
        }

        public override void MagicAttackSuccess(MapObject ob, int damageDealt)
        {
        }

        public override int ModifyPowerAdditionner(bool primary, int power, MapObject ob, Stats stats = null, int extra = 0)
        {
            power += extra != 0 ? extra : Magic.GetPower() + Player.GetMC();
            return power;
        }
    }
}
