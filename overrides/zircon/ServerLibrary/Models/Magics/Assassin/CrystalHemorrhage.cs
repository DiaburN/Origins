using Library;
using Server.DBModels;
using Server.Envir;
using System;

namespace Server.Models.Magics
{
    [MagicType(MagicType.CrystalHemorrhage)]
    public sealed class CrystalHemorrhage : MagicObject
    {
        protected override Element Element => Element.None;
        public override bool AttackSkill => true;

        private int counter;
        private bool ready;

        public CrystalHemorrhage(PlayerObject player, UserMagic magic) : base(player, magic) { }

        public override AttackCast AttackCast(MagicType attackType)
        {
            var response = new AttackCast();

            if (ready)
            {
                response.Magics.Add(Type);
                return response;
            }

            counter += SEnvir.Random.Next(1, 1 + Magic.Level * 2);

            // Crystal crossing 55 arms the bleed for the next attack.
            if (counter >= 55)
                ready = true;

            return response;
        }

        public override int ModifyPowerAdditionner(bool primary, int power, MapObject ob, Stats stats = null, int extra = 0)
        {
            return power + Magic.GetPower();
        }

        public override void AttackComplete(MapObject target)
        {
            if (target?.Node != null && !target.Dead)
            {
                int duration = Math.Max(1, Magic.Level * 2 + Player.Stats[Stat.Luck] / 6);
                target.ApplyPoison(new Poison
                {
                    Owner = Player,
                    Type = PoisonType.Hemorrhage,
                    TickCount = duration,
                    TickFrequency = TimeSpan.FromSeconds(1),
                    Value = Player.Stats[Stat.MaxDC] + 1,
                });
            }

            counter = 0;
            ready = false;
            Player.LevelMagic(Magic);
        }
    }
}
