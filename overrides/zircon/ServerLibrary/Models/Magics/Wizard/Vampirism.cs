using Library;
using Server.DBModels;
using Server.Envir;
using System;
using System.Collections.Generic;
using System.Drawing;

namespace Server.Models.Magics
{
    [MagicType(MagicType.Vampirism)]
    public sealed class Vampirism : MagicObject
    {
        protected override Element Element => Element.None;

        private int _vampAmount;
        private DateTime _vampTime;

        public Vampirism(PlayerObject player, UserMagic magic) : base(player, magic)
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

            int castPower = Magic.GetPower() + Player.GetMC();

            ActionList.Add(new DelayedAction(
                SEnvir.Now.AddMilliseconds(500),
                ActionType.DelayMagic,
                Type,
                target,
                castPower));

            return response;
        }

        public override void MagicComplete(params object[] data)
        {
            MapObject target = (MapObject)data[1];
            int castPower = (int)data[2];

            if (!Player.CanAttackTarget(target) || target.CurrentMap != CurrentMap || target.Node == null)
                return;

            Player.MagicAttack(new List<MagicType> { Type }, target, true, null, castPower);
        }

        public override int ModifyPowerAdditionner(bool primary, int power, MapObject ob, Stats stats = null, int extra = 0)
        {
            power += extra != 0 ? extra : Magic.GetPower() + Player.GetMC();
            return power;
        }

        public override void MagicAttackSuccess(MapObject ob, int damageDealt)
        {
            base.MagicAttackSuccess(ob, damageDealt);

            if (damageDealt <= 0) return;

            if (_vampAmount == 0)
                _vampTime = SEnvir.Now.AddMilliseconds(1000);

            _vampAmount += (int)(damageDealt * (Magic.Level + 1) * 0.25F);
        }

        public override void Process()
        {
            if (_vampAmount <= 0 || SEnvir.Now < _vampTime || Player.Dead)
                return;

            int heal = Math.Min(10, _vampAmount);
            _vampAmount -= heal;
            Player.ChangeHP(heal);

            if (_vampAmount > 0)
                _vampTime = SEnvir.Now.AddMilliseconds(500);
        }
    }
}
