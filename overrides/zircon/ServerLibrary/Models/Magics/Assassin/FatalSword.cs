using Library;
using Server.DBModels;
using Server.Envir;

namespace Server.Models.Magics
{
    [MagicType(MagicType.FatalSword)]
    public sealed class FatalSword : MagicObject
    {
        protected override Element Element => Element.None;
        public override bool AttackSkill => true;
        public override bool IgnorePhysicalDefense => true;

        private bool ready;
        private bool armAfterAttack;

        public FatalSword(PlayerObject player, UserMagic magic) : base(player, magic) { }

        public override AttackCast AttackCast(MagicType attackType)
        {
            var response = new AttackCast();

            // Crystal consumes an already-armed proc first. The 1/10 roll made for this
            // attack only arms FatalSword for the following attack.
            if (ready)
                response.Magics.Add(Type);
            else if (SEnvir.Random.Next(10) == 0)
                armAfterAttack = true;

            return response;
        }

        public override int ModifyPowerAdditionner(bool primary, int power, MapObject ob, Stats stats = null, int extra = 0)
        {
            return power + Magic.GetPower();
        }

        public override void AttackComplete(MapObject target)
        {
            ready = false;
            Player.LevelMagic(Magic);
        }

        public override void AttackCompletePassive(MapObject target, System.Collections.Generic.List<MagicType> types)
        {
            if (!armAfterAttack) return;

            armAfterAttack = false;
            ready = true;
        }
    }
}
