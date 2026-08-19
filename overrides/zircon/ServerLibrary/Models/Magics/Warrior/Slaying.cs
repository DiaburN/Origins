using Library;
using Server.DBModels;
using Server.Envir;
using S = Library.Network.ServerPackets;

namespace Server.Models.Magics
{
    [MagicType(MagicType.Slaying)]
    public sealed class Slaying : MagicObject
    {
        protected override Element Element => Element.None;
        public override bool AttackSkill => true;

        private bool CanPowerAttack;

        public Slaying(PlayerObject player, UserMagic magic) : base(player, magic)
        {
        }

        public override AttackCast AttackCast(MagicType attackType)
        {
            var response = new AttackCast();

            if (attackType != Type || !CanPowerAttack)
                return response;

            CanPowerAttack = false;
            Player.Enqueue(new S.MagicToggle { Magic = Type, CanUse = false });

            response.Cast = true;
            response.Magics.Add(Type);
            return response;
        }

        public override void AttackCompletePassive(MapObject target, System.Collections.Generic.List<MagicType> types)
        {
            if (CanPowerAttack) return;

            // Crystal arms Slaying with Random.Next(12) <= magic.Level.
            if (SEnvir.Random.Next(12) > Magic.Level) return;

            CanPowerAttack = true;
            Player.Enqueue(new S.MagicToggle { Magic = Type, CanUse = true });
        }

        public override int ModifyPowerAdditionner(bool primary, int power, MapObject ob, Stats stats = null, int extra = 0)
        {
            power += Magic.GetPower();
            return power;
        }

        public override Stats GetPassiveStats()
        {
            int[] dcBonus = { 5, 6, 7, 8 };
            int level = System.Math.Max(0, System.Math.Min(Magic.Level, dcBonus.Length - 1));

            return new Stats
            {
                // Crystal RefreshSkills(): Accuracy += level, MaxDC += {5,6,7,8}.
                [Stat.Accuracy] = Magic.Level,
                [Stat.MaxDC] = dcBonus[level],
            };
        }
    }
}
