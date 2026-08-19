using Library;
using Server.DBModels;
using Server.Envir;
using System.Collections.Generic;
using System.Drawing;

namespace Server.Models.Magics
{
    [MagicType(MagicType.CatTongue)]
    public sealed class CatTongue : MagicObject
    {
        protected override Element Element => Element.None;

        public CatTongue(PlayerObject player, UserMagic magic) : base(player, magic) { }

        public override MagicCast MagicCast(MapObject target, Point location, MirDirection direction)
        {
            var response = new MagicCast { Ob = target };
            if (target == null || !Player.CanAttackTarget(target))
            {
                response.Cast = false;
                response.Ob = null;
                return response;
            }

            response.Targets.Add(target.ObjectID);
            int power = Magic.GetPower() + Player.GetDC();
            int delay = 500 + Functions.Distance(CurrentLocation, target.CurrentLocation) * 50;
            ActionList.Add(new DelayedAction(SEnvir.Now.AddMilliseconds(delay), ActionType.DelayMagic, Type, target, power));
            return response;
        }

        public override void MagicComplete(params object[] data)
        {
            MapObject target = (MapObject)data[1];
            int power = (int)data[2];
            if (target?.Node == null || !Player.CanAttackTarget(target)) return;

            Player.MagicAttack(new List<MagicType> { Type }, target, true, null, power);
        }

        public override int ModifyPowerAdditionner(bool primary, int power, MapObject ob, Stats stats = null, int extra = 0) => extra;
    }
}
