using Library;
using Server.DBModels;
using Server.Envir;
using System;
using System.Drawing;

namespace Server.Models.Magics
{
    [MagicType(MagicType.ElementalBarrier1)]
    public sealed class ElementalBarrier1 : CrystalArcherMagic
    {
        public override bool UpdateCombatTime => false;

        public ElementalBarrier1(PlayerObject player, UserMagic magic) : base(player, magic) { }

        public override MagicCast MagicCast(MapObject target, Point location, MirDirection direction)
        {
            var response = new MagicCast { Ob = Player };

            // Jev: magic.GetPower(GetAttackPower(MinDC, MaxDC)), resolved after 500 ms.
            int duration = Math.Max(1, Magic.GetPower() + Player.GetDC());
            ActionList.Add(new DelayedAction(
                SEnvir.Now.AddMilliseconds(500),
                ActionType.DelayMagic,
                Type,
                duration));

            return response;
        }

        public override void MagicComplete(params object[] data)
        {
            int duration = (int)data[1];

            // Jev resets the elemental/orb state on activation.
            Player.CrystalArcherElementsLevel = 0;

            Player.BuffAdd(
                BuffType.CrystalElementalBarrier1,
                TimeSpan.FromSeconds(duration),
                new Stats
                {
                    [Stat.CrystalArcherBarrierReductionPercent] = (Magic.Level + 2) * 10,
                },
                true,
                false,
                TimeSpan.Zero);

            Player.LevelMagic(Magic);
        }
    }
}
