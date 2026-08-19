using Library;
using Server.DBModels;
using Server.Envir;
using System.Drawing;

namespace Server.Models.Magics
{
    [MagicType(MagicType.DoubleSlash)]
    public sealed class DoubleSlash : MagicObject
    {
        protected override Element Element => Element.None;
        public override bool AttackSkill => true;
        public override bool UseMagicDefenseForPhysicalAttack => true;

        private int secondHitPower;

        public DoubleSlash(PlayerObject player, UserMagic magic) : base(player, magic) { }

        public override AttackCast AttackCast(MagicType attackType)
        {
            var response = new AttackCast();
            if (attackType != Type || !CheckCost()) return response;

            MagicConsume();
            response.Cast = true;
            response.Magics.Add(Type);

            // Crystal computes the secondary hit from the same DC snapshot and skill damage.
            secondHitPower = Player.GetDC() + Magic.GetPower();
            Player.LevelMagic(Magic);
            return response;
        }

        public override int ModifyPowerAdditionner(bool primary, int power, MapObject ob, Stats stats = null, int extra = 0)
        {
            return power + Magic.GetPower();
        }

        public override void AttackComplete(MapObject target)
        {
            if (target?.Node == null || target.Dead || secondHitPower <= 0) return;

            int power = secondHitPower;
            secondHitPower = 0;

            // Crystal second slash resolves 400 ms later with DefenceType.Agility:
            // perform the agility roll now, then schedule raw physical damage with no AC/MAC subtraction.
            if (SEnvir.Random.Next(target.Stats[Stat.Agility]) > Player.Stats[Stat.Accuracy])
            {
                target.Dodged();
                return;
            }

            ActionList.Add(new DelayedAction(
                SEnvir.Now.AddMilliseconds(400),
                ActionType.DelayedAttackDamage,
                target,
                power,
                Element.None,
                true,
                false,
                false,
                true));
        }
    }
}
