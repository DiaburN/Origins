using Library;
using Server.DBModels;
using Server.Envir;
using System.Drawing;

namespace Server.Models.Magics
{
    [MagicType(MagicType.HeavenlySword)]
    public sealed class HeavenlySword : MagicObject
    {
        protected override Element Element => Element.None;

        public HeavenlySword(PlayerObject player, UserMagic magic) : base(player, magic) { }

        public override MagicCast MagicCast(MapObject target, Point location, MirDirection direction)
        {
            var response = new MagicCast { Ob = null };
            response.Locations.Add(CurrentLocation);

            int power = Magic.GetPower() + Player.GetDC();
            ActionList.Add(new DelayedAction(
                SEnvir.Now.AddMilliseconds(500),
                ActionType.DelayMagic,
                Type,
                CurrentMap,
                CurrentLocation,
                direction,
                power));

            return response;
        }

        public override void MagicComplete(params object[] data)
        {
            Map map = (Map)data[1];
            Point location = (Point)data[2];
            MirDirection direction = (MirDirection)data[3];
            int power = (int)data[4];
            if (map != CurrentMap) return;

            bool trained = false;
            for (int i = 0; i < 3; i++)
            {
                location = Functions.Move(location, direction);
                Cell cell = map.GetCell(location);
                if (cell?.Objects == null) continue;

                for (int o = cell.Objects.Count - 1; o >= 0; o--)
                {
                    MapObject ob = cell.Objects[o];
                    if (ob?.Node == null || !Player.CanAttackTarget(ob)) continue;

                    int damage = power - ob.GetMR();
                    if (damage <= 0)
                    {
                        ob.Blocked();
                        break;
                    }

                    if (ob.Attacked(Player, damage, Element.None, true, false, false, true) > 0)
                        trained = true;
                    break;
                }
            }

            if (trained)
                Player.LevelMagic(Magic);
        }
    }
}
