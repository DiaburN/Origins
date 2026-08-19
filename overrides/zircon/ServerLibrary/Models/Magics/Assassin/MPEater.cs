using Library;
using Server.DBModels;
using Server.Envir;

namespace Server.Models.Magics
{
    [MagicType(MagicType.MPEater)]
    public sealed class MPEater : MagicObject
    {
        protected override Element Element => Element.None;
        public override bool AttackSkill => true;

        private int counter;
        private bool ready;

        public MPEater(PlayerObject player, UserMagic magic) : base(player, magic) { }

        public override AttackCast AttackCast(MagicType attackType)
        {
            var response = new AttackCast();

            if (ready)
            {
                response.Magics.Add(Type);
                return response;
            }

            int baseCount = 1 + Player.Stats[Stat.Accuracy] / 2;
            int maxCount = baseCount + Magic.Level * 5;
            counter += SEnvir.Random.Next(baseCount, maxCount + 1);

            // Crystal crossing 100 arms the proc for the next attack.
            if (counter >= 100)
                ready = true;

            return response;
        }

        public override int ModifyPowerAdditionner(bool primary, int power, MapObject ob, Stats stats = null, int extra = 0)
        {
            return power + Magic.GetPower();
        }

        public override void AttackComplete(MapObject target)
        {
            int amount = 5 * (Magic.Level + Player.Stats[Stat.Accuracy] / 4);

            if (target is PlayerObject targetPlayer)
                targetPlayer.ChangeMP(-amount);

            Player.ChangeMP(amount);
            counter = 0;
            ready = false;
            Player.LevelMagic(Magic);
        }
    }
}
