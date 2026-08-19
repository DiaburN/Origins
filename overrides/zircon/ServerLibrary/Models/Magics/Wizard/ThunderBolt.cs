using Library;
using Server.DBModels;
using Server.Envir;
using System.Collections.Generic;
using System.Drawing;

namespace Server.Models.Magics
{
    [MagicType(MagicType.ThunderBolt)]
    public class ThunderBolt : MagicObject
    {
        protected override Element Element => Element.Lightning;

        public ThunderBolt(PlayerObject player, UserMagic magic) : base(player, magic)
        {
        }

        public override MagicCast MagicCast(MapObject target, Point location, MirDirection direction)
        {
            var response = new MagicCast
            {
                Ob = target
            };

            if (!Player.CanAttackTarget(target))
            {
                response.Ob = null;
                response.Locations.Add(location);
                return response;
            }

            response.Targets.Add(target.ObjectID);

            Point lockedLocation = target.CurrentLocation;
            int castPower = Magic.GetPower() + Player.GetMC();

            if (target.Race == ObjectType.Monster && ((MonsterObject)target).MonsterInfo.Undead)
                castPower = castPower * 3 / 2;

            ActionList.Add(new DelayedAction(
                SEnvir.Now.AddMilliseconds(500),
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

            if (target.Node == null || target.CurrentMap != CurrentMap) return;
            if (Functions.Distance(target.CurrentLocation, lockedLocation) > 2) return;

            Player.MagicAttack(new List<MagicType> { Type }, target, true, null, castPower);
        }

        public override int ModifyPowerAdditionner(bool primary, int power, MapObject ob, Stats stats = null, int extra = 0)
        {
            power += extra != 0 ? extra : Magic.GetPower() + Player.GetMC();
            return power;
        }
    }
}
