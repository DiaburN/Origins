using Library;
using Server.DBModels;
using Server.Envir;
using System;
using S = Library.Network.ServerPackets;

namespace Server.Models.Magics
{
    [MagicType(MagicType.TwinDrakeBlade)]
    public sealed class TwinDrakeBlade : MagicObject
    {
        protected override Element Element => Element.None;
        public override bool AttackSkill => true;

        private bool Armed;

        public TwinDrakeBlade(PlayerObject player, UserMagic magic) : base(player, magic)
        {
        }

        public override void RefreshToggle()
        {
            if (Armed)
                Player.Enqueue(new S.MagicToggle { Magic = Type, CanUse = true });
        }

        public override void Toggle(bool canUse)
        {
            // Crystal only arms this skill; it stays armed until a valid strike
            // consumes it. Re-toggling an already armed skill is ignored.
            if (!canUse || Armed || !CheckCost() || Player.Dead) return;

            MagicConsume();
            Armed = true;
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
            power += Magic.GetPower();
            return power;
        }

        public override void AttackComplete(MapObject target)
        {
            if (target != null && !target.Dead && target.Level < Player.Level + 10)
            {
                int denominator = target.Race == ObjectType.Player ? 40 : 20;

                if (SEnvir.Random.Next(denominator) <= Magic.Level + 1)
                {
                    target.ApplyPoison(new Poison
                    {
                        Type = PoisonType.Paralysis,
                        Owner = Player,
                        TickCount = 1,
                        TickFrequency = TimeSpan.FromSeconds(target.Race == ObjectType.Player ? 2 : 2 + Magic.Level),
                    });
                }
            }

            Player.LevelMagic(Magic);
        }
    }
}
