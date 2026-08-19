using Library;
using Server.DBModels;
using System.Collections.Generic;
using S = Library.Network.ServerPackets;

namespace Server.Models.Magics
{
    [MagicType(MagicType.CrossHalfMoon)]
    public sealed class CrossHalfMoon : MagicObject
    {
        protected override Element Element => Element.None;
        public override bool AttackSkill => true;

        private bool Enabled;
        private bool LevelledThisSwing;

        public CrossHalfMoon(PlayerObject player, UserMagic magic) : base(player, magic)
        {
        }

        public override void RefreshToggle()
        {
            if (Enabled)
                Player.Enqueue(new S.MagicToggle { Magic = Type, CanUse = true });
        }

        public override void Toggle(bool canUse)
        {
            Enabled = canUse;
            Player.Enqueue(new S.MagicToggle { Magic = Type, CanUse = Enabled });
        }

        public override AttackCast AttackCast(MagicType attackType)
        {
            var response = new AttackCast();

            if (attackType != Type || !Enabled || !CheckCost())
                return response;

            MagicConsume();
            LevelledThisSwing = false;

            response.Cast = true;
            response.Magics.Add(Type);
            return response;
        }

        public override void SecondaryAttackLocation(List<MagicType> magics)
        {
            // Primary attack owns the forward cell. Crystal then sweeps the
            // remaining seven adjacent directions, producing the full 3x3 ring.
            for (int i = 1; i < 8; i++)
            {
                Player.AttackLocation(
                    Functions.Move(CurrentLocation, Functions.ShiftDirection(Direction, i)),
                    magics,
                    false);
            }
        }

        public override int ModifyPowerAdditionner(bool primary, int power, MapObject ob, Stats stats = null, int extra = 0)
        {
            power += Magic.GetPower();
            return power;
        }

        public override void AttackComplete(MapObject target)
        {
            if (LevelledThisSwing) return;

            LevelledThisSwing = true;
            Player.LevelMagic(Magic);
        }
    }
}
