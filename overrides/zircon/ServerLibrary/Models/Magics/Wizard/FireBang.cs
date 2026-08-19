using Library;
using Server.DBModels;
using Server.Envir;
using System.Collections.Generic;
using System.Drawing;

namespace Server.Models.Magics
{
    [MagicType(MagicType.FireBang)]
    public class FireBang : MagicObject
    {
        protected override Element Element => Element.Fire;

        public FireBang(PlayerObject player, UserMagic magic) : base(player, magic)
        {
        }

        public override MagicCast MagicCast(MapObject target, Point location, MirDirection direction)
        {
            var response = new MagicCast
            {
                Ob = null
            };

            foreach (Cell cell in CurrentMap.GetCells(location, 0, 1))
            {
                if (cell == null) continue;
                response.Locations.Add(cell.Location);
            }

            int castPower = Magic.GetPower() + Player.GetMC();

            ActionList.Add(new DelayedAction(
                SEnvir.Now.AddMilliseconds(500),
                ActionType.DelayMagic,
                Type,
                location,
                castPower));

            return response;
        }

        public override void MagicComplete(params object[] data)
        {
            Point location = (Point)data[1];
            int castPower = (int)data[2];
            bool train = false;

            foreach (Cell cell in CurrentMap.GetCells(location, 0, 1))
            {
                if (cell?.Objects == null) continue;

                for (int i = cell.Objects.Count - 1; i >= 0; i--)
                {
                    MapObject ob = cell.Objects[i];
                    if (!Player.CanAttackTarget(ob)) continue;

                    if (Player.MagicAttack(new List<MagicType> { Type }, ob, true, null, castPower) > 0)
                        train = true;
                }
            }

            if (train)
                Player.LevelMagic(Magic);
        }

        public override void MagicAttackSuccess(MapObject ob, int damageDealt)
        {
            // Crystal trains FireBang once per successful 3x3 cast.
        }

        public override int ModifyPowerAdditionner(bool primary, int power, MapObject ob, Stats stats = null, int extra = 0)
        {
            power += extra != 0 ? extra : Magic.GetPower() + Player.GetMC();
            return power;
        }
    }
}
