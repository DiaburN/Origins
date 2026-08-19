using Library;
using Server.DBModels;
using Server.Envir;
using System;
using S = Library.Network.ServerPackets;

namespace Server.Models.Magics
{
    [MagicType(MagicType.FlamingSword)]
    public sealed class FlamingSword : MagicObject
    {
        protected override Element Element => Element.None;
        public override bool AttackSkill => true;

        private bool Armed;
        private DateTime ArmedUntil;

        public FlamingSword(PlayerObject player, UserMagic magic) : base(player, magic)
        {
        }

        public override void Process()
        {
            if (!Armed || SEnvir.Now < ArmedUntil) return;

            Armed = false;
            Player.Enqueue(new S.MagicToggle { Magic = Type, CanUse = false });
        }

        public override void Toggle(bool canUse)
        {
            if (Armed || SEnvir.Now < ArmedUntil) return;
            if (!CheckCost() || Player.Dead) return;

            MagicConsume();

            // Crystal keeps the charge available for 10 seconds and will not
            // allow it to be armed again until this same window has elapsed,
            // even if the charged strike is consumed early.
            Armed = true;
            ArmedUntil = SEnvir.Now.AddSeconds(10);
            MagicCooldown(Magic, 10000);

            Player.Enqueue(new S.MagicToggle { Magic = Type, CanUse = true });
        }

        public override AttackCast AttackCast(MagicType attackType)
        {
            var response = new AttackCast();

            if (attackType != Type || !Armed)
                return response;

            Armed = false;
            Player.Enqueue(new S.MagicToggle { Magic = Type, CanUse = false });

            response.Cast = true;
            response.Magics.Add(Type);
            return response;
        }

        public override int ModifyPowerAdditionner(bool primary, int power, MapObject ob, Stats stats = null, int extra = 0)
        {
            // Crystal UserMagic.GetDamage: base weapon roll + magic power
            // (Crystal's default multiplier is carried by imported spell data).
            power += Magic.GetPower();
            return power;
        }
    }
}
