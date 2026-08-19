using Library;
using Server.DBModels;
using System;
using System.Drawing;

namespace Server.Models.Magics
{
    [MagicType(MagicType.Healing2)]
    public sealed class Healing2 : MagicObject
    {
        protected override Element Element => Element.None;
        public override bool UpdateCombatTime => false;

        public Healing2(PlayerObject player, UserMagic magic) : base(player, magic) { }

        public override MagicCast MagicCast(MapObject target, Point location, MirDirection direction)
        {
            if (target == null || !Player.CanHelpTarget(target)) target = Player;

            var response = new MagicCast { Ob = target };
            response.Targets.Add(target.ObjectID);

            // Jev calls Healing2 directly from the magic switch: there is no 500 ms delayed completion.
            int hpBonus = Magic.GetPower() + Player.GetSC() + Player.Level;
            int durationSeconds = Player.GetSC() + 25 + Magic.Level * 25;

            target.BuffAdd(
                BuffType.CrystalHealing2,
                TimeSpan.FromSeconds(durationSeconds),
                new Stats { [Stat.Health] = hpBonus },
                true,
                false,
                TimeSpan.Zero);

            Player.LevelMagic(Magic);
            return response;
        }

        public override void MagicComplete(params object[] data)
        {
            // Healing2 is immediate in Crystal-Monk; nothing is scheduled here.
        }
    }
}
