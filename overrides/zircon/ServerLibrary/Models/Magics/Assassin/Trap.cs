using Library;
using Server.DBModels;
using Server.Envir;
using System;
using System.Drawing;

namespace Server.Models.Magics
{
    [MagicType(MagicType.Trap)]
    public sealed class Trap : MagicObject
    {
        protected override Element Element => Element.None;
        public override bool UpdateCombatTime => false;

        public Trap(PlayerObject player, UserMagic magic) : base(player, magic) { }

        public override MagicCast MagicCast(MapObject target, Point location, MirDirection direction)
        {
            var response = new MagicCast { Ob = target };
            if (target is not MonsterObject monster || !Player.CanAttackTarget(monster) || monster.Level >= Player.Level + 2)
            {
                response.Cast = false;
                response.Ob = null;
                return response;
            }

            response.Targets.Add(monster.ObjectID);
            Player.LevelMagic(Magic);
            ActionList.Add(new DelayedAction(SEnvir.Now.AddMilliseconds(500), ActionType.DelayMagic, Type, monster));
            return response;
        }

        public override void MagicComplete(params object[] data)
        {
            MonsterObject target = (MonsterObject)data[1];
            if (target?.Node == null || !Player.CanAttackTarget(target) || target.Level >= Player.Level + 2) return;

            target.ShockTime = SEnvir.Now.AddSeconds(60);
            target.Target = null;
        }
    }
}
