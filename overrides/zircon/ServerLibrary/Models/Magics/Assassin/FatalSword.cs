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

        public FatalSword(PlayerObject player, UserMagic magic) : base(player, magic) { }

        public override AttackCast AttackCast(MagicType attackType)
        {
            var response = new AttackCast();

            // Crystal rolls 1/10 on every physical attack. A successful roll powers that same hit.
            if (!ready && SEnvir.Random.Next(10) == 0)
                ready = true;

            if (ready)
                response.Magics.Add(Type);

            return response;
        }

        public override int ModifyPowerAdditionner(bool primary, int power, MapObject ob, Stats stats = null, int extra = 0)
        {
            return power + Magic.GetPower();
        }

        public override void AttackComplete(MapObject target)
        {
            // Crystal only consumes the ready proc after a successful damaging hit.
            ready = false;
            Player.LevelMagic(Magic);
        }
    }
}
