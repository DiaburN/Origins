using Library;
using Server.DBModels;
using Server.Envir;
using System.Collections.Generic;
using System.Drawing;

namespace Server.Models.Magics
{
    [MagicType(MagicType.Lightning)]
    public class Lightning : MagicObject
    {
        protected override Element Element => Element.Lightning;

        public Lightning(PlayerObject player, UserMagic magic) : base(player, magic)
        {
        }

        public override MagicCast MagicCast(MapObject target, Point location, MirDirection direction)
        {
            var response = new MagicCast { Ob = null };
            Point point = CurrentLocation;

            for (int i = 0; i < 6; i++)
            {
                point = Functions.Move(point, direction);
                if (point.X < 0 || point.Y < 0 || point.X >= CurrentMap.Width || point.Y >= CurrentMap.Height) break;
                response.Locations.Add(point);
            }

            int castPower = Magic.GetPower() + Player.GetMC();
            ActionList.Add(new DelayedAction(
                SEnvir.Now.AddMilliseconds(500),
                ActionType.DelayMagic,
                Type,
                CurrentLocation,
                direction,
                castPower));

            return response;
        }

        public override void MagicComplete(params object[] data)
        {
            Point point = (Point)data[1];
            MirDirection direction = (MirDirection)data[2];
            int castPower = (int)data[3];
            bool train = false;

            for (int step = 0; step < 6; step++)
            {
                point = Functions.Move(point, direction);
                if (point.X < 0 || point.Y < 0 || point.X >= CurrentMap.Width || point.Y >= CurrentMap.Height) break;

                Cell cell = CurrentMap.GetCell(point);
                if (cell?.Objects == null) continue;

                for (int i = 0; i < cell.Objects.Count; i++)
                {
                    MapObject ob = cell.Objects[i];
                    if (ob.Race != ObjectType.Player && ob.Race != ObjectType.Monster) continue;
                    if (!Player.CanAttackTarget(ob)) continue;

                    if (Player.MagicAttack(new List<MagicType> { Type }, ob, true, null, castPower) > 0)
                        train = true;
                    break;
                }
            }

            if (train)
                Player.LevelMagic(Magic);
        }

        public override void MagicAttackSuccess(MapObject ob, int damageDealt)
        {
            // Crystal trains Lightning once per line cast, not once per target.
        }

        public override int ModifyPowerAdditionner(bool primary, int power, MapObject ob, Stats stats = null, int extra = 0)
        {
            power += extra != 0 ? extra : Magic.GetPower() + Player.GetMC();
            return power;
        }
    }
}
