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

            // Crystal first checks an already-armed proc. Only after that check does it
            // roll 1/10, so a new success is stored for the following physical attack.
            if (ready)
            {
                response.Magics.Add(Type);
            }
            else if (SEnvir.Random.Next(10) == 0)
            {
                ready = true;
            }

            return response;
        }

        public override int ModifyPowerAdditionner(bool primary, int power, MapObject ob, Stats stats = null, int extra = 0)
        {
            return power + Magic.GetPower();
        }

        public override void AttackComplete(MapObject target)
        {
            // Crystal consumes FatalSword only after a successful damaging proc.
            ready = false;
            Player.LevelMagic(Magic);
        }
    }
}
