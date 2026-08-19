using Library;
using Server.DBModels;
using Server.Envir;
using System.Collections.Generic;
using System.Drawing;

namespace Server.Models.Magics
{
    [MagicType(MagicType.FlameField)]
    public sealed class FlameField : MagicObject
    {
        protected override Element Element => Element.Fire;

        public FlameField(PlayerObject player, UserMagic magic) : base(player, magic)
        {
        }

        public override MagicCast MagicCast(MapObject target, Point location, MirDirection direction)
        {
            var response = new MagicCast { Ob = null };
            Point center = CurrentLocation;

            foreach (Cell cell in CurrentMap.GetCells(center, 0, 2))
            {
                if (cell == null) continue;
                response.Locations.Add(cell.Location);
            }

            int castPower = Magic.GetPower() + Player.GetMC();

            ActionList.Add(new DelayedAction(
                SEnvir.Now.AddMilliseconds(500),
                ActionType.DelayMagic,
                Type,
                center,
                castPower));

            return response;
        }

        public override void MagicComplete(params object[] data)
        {
            Point center = (Point)data[1];
            int castPower = (int)data[2];
            bool train = false;

            foreach (Cell cell in CurrentMap.GetCells(center, 0, 2))
            {
                if (cell?.Objects == null) continue;

                for (int i = cell.Objects.Count - 1; i >= 0; i--)
                {
                    MapObject ob = cell.Objects[i];
                    if (ob.Race != ObjectType.Player && ob.Race != ObjectType.Monster) continue;
                    if (!Player.CanAttackTarget(ob)) continue;

                    Player.MagicAttack(new List<MagicType> { Type }, ob, true, null, castPower);
                    train = true;
                }
            }

            if (train)
                Player.LevelMagic(Magic);
        }

        public override void MagicAttackSuccess(MapObject ob, int damageDealt)
        {
            // Crystal trains FlameField once per successful 5x5 cast.
        }

        public override int ModifyPowerAdditionner(bool primary, int power, MapObject ob, Stats stats = null, int extra = 0)
        {
            power += extra != 0 ? extra : Magic.GetPower() + Player.GetMC();
            return power;
        }
    }
}
