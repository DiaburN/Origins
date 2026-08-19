using Library;
using Server.DBModels;
using Server.Envir;
using System.Collections.Generic;
using System.Drawing;

namespace Server.Models.Magics
{
    [MagicType(MagicType.FlameDisruptor)]
    public sealed class FlameDisruptor : MagicObject
    {
        protected override Element Element => Element.Fire;

        public FlameDisruptor(PlayerObject player, UserMagic magic) : base(player, magic)
        {
        }

        public override MagicCast MagicCast(MapObject target, Point location, MirDirection direction)
        {
            var response = new MagicCast { Ob = target };

            if (target == null || (target.Race != ObjectType.Player && target.Race != ObjectType.Monster) || !Player.CanAttackTarget(target))
            {
                response.Ob = null;
                return response;
            }

            response.Targets.Add(target.ObjectID);

            Point targetLocation = target.CurrentLocation;
            int castPower = Magic.GetPower() + Player.GetMC();

            // Crystal applies the 1.5x bonus only to living monsters. Players stay at normal power.
            if (target is MonsterObject monster && !monster.MonsterInfo.Undead)
                castPower = (int)(castPower * 1.5F);

            ActionList.Add(new DelayedAction(
                SEnvir.Now.AddMilliseconds(500),
                ActionType.DelayMagic,
                Type,
                target,
                targetLocation,
                castPower));

            return response;
        }

        public override void MagicComplete(params object[] data)
        {
            MapObject target = (MapObject)data[1];
            Point targetLocation = (Point)data[2];
            int castPower = (int)data[3];

            if (target?.Node == null || target.CurrentMap != CurrentMap) return;
            if (!Player.CanAttackTarget(target)) return;
            if (!Functions.InRange(target.CurrentLocation, targetLocation, 2)) return;

            Player.MagicAttack(new List<MagicType> { Type }, target, true, null, castPower);
        }

        public override int ModifyPowerAdditionner(bool primary, int power, MapObject ob, Stats stats = null, int extra = 0)
        {
            power += extra != 0 ? extra : Magic.GetPower() + Player.GetMC();
            return power;
        }
    }
}
