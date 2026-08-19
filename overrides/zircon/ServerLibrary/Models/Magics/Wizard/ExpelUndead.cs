using Library;
using Server.DBModels;
using Server.Envir;
using System.Drawing;

namespace Server.Models.Magics
{
    [MagicType(MagicType.ExpelUndead)]
    public class ExpelUndead : MagicObject
    {
        protected override Element Element => Element.None;

        public ExpelUndead(PlayerObject player, UserMagic magic) : base(player, magic)
        {
        }

        public override MagicCast MagicCast(MapObject target, Point location, MirDirection direction)
        {
            var response = new MagicCast { Ob = target };

            if (!Player.CanAttackTarget(target) || target?.Race != ObjectType.Monster)
            {
                response.Ob = null;
                return response;
            }

            MonsterObject monster = (MonsterObject)target;
            if (!monster.MonsterInfo.Undead)
            {
                response.Ob = null;
                return response;
            }

            response.Targets.Add(monster.ObjectID);

            // Crystal first compares caster/target level, then performs the skill-level success roll.
            if (SEnvir.Random.Next(2) + Player.Level - 1 <= monster.Level)
            {
                if (monster.Target == null && monster.CanAttackTarget(Player))
                    monster.Target = Player;
                return response;
            }

            int difference = Player.Level - monster.Level + 15;
            int successThreshold = ((Magic.Level + 1) << 3) + difference;

            if (SEnvir.Random.Next(100) >= successThreshold)
            {
                if (monster.Target == null && monster.CanAttackTarget(Player))
                    monster.Target = Player;
                return response;
            }

            ActionList.Add(new DelayedAction(
                SEnvir.Now.AddMilliseconds(500),
                ActionType.DelayMagic,
                Type,
                monster));

            return response;
        }

        public override void MagicComplete(params object[] data)
        {
            MonsterObject monster = (MonsterObject)data[1];

            if (monster?.Node == null || monster.CurrentMap != CurrentMap) return;
            if (!Player.CanAttackTarget(monster) || !monster.MonsterInfo.Undead) return;

            if (monster.EXPOwner == null && monster.PetOwner == null)
                monster.EXPOwner = Player;

            monster.Die();
            Player.LevelMagic(Magic);
        }
    }
}
