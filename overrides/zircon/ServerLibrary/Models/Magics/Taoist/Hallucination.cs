using Library;
using Server.DBModels;
using Server.Envir;
using System;
using System.Drawing;

namespace Server.Models.Magics
{
    [MagicType(MagicType.Hallucination)]
    public sealed class Hallucination : MagicObject
    {
        protected override Element Element => Element.None;
        public override bool UpdateCombatTime => false;

        public Hallucination(PlayerObject player, UserMagic magic) : base(player, magic) { }

        public override MagicCast MagicCast(MapObject target, Point location, MirDirection direction)
        {
            var response = new MagicCast { Ob = target };
            if (target is not MonsterObject monster || !Player.CanAttackTarget(monster))
            {
                response.Ob = null;
                return response;
            }

            response.Targets.Add(monster.ObjectID);
            int delay = 500 + Functions.Distance(CurrentLocation, monster.CurrentLocation) * 50;
            ActionList.Add(new DelayedAction(SEnvir.Now.AddMilliseconds(delay), ActionType.DelayMagic, Type, monster));
            return response;
        }

        public override void MagicComplete(params object[] data)
        {
            MonsterObject target = (MonsterObject)data[1];
            if (target?.Node == null || target.CurrentMap != CurrentMap || !Player.CanAttackTarget(target)) return;
            if (Functions.Distance(CurrentLocation, target.CurrentLocation) > 7) return;
            if (SEnvir.Random.Next(Player.Level + 20 + Magic.Level * 5) <= target.Level + 10) return;

            // Crystal consumes the amulet only after the Hallucination success roll.
            if (!Player.UseAmulet(1, 0)) return;

            target.HallucinationTime = SEnvir.Now.AddSeconds(SEnvir.Random.Next(20) + 10);
            target.Target = null;
            Player.LevelMagic(Magic);
        }
    }
}
