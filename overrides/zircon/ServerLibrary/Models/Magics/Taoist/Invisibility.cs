using Library;
using Server.DBModels;
using Server.Envir;
using System;
using System.Drawing;
using System.Linq;

namespace Server.Models.Magics
{
    // Crystal Hiding mapped to Zircon Invisibility.
    [MagicType(MagicType.Invisibility)]
    public sealed class Invisibility : MagicObject
    {
        protected override Element Element => Element.None;
        public override bool UpdateCombatTime => false;

        public Invisibility(PlayerObject player, UserMagic magic) : base(player, magic) { }

        public override MagicCast MagicCast(MapObject target, Point location, MirDirection direction)
        {
            var response = new MagicCast { Ob = null };
            if (!Player.UseAmulet(1, 0))
            {
                response.Cast = false;
                return response;
            }

            int durationSeconds = Player.GetSC() + (Magic.Level + 1) * 5;
            ActionList.Add(new DelayedAction(SEnvir.Now.AddMilliseconds(500), ActionType.DelayMagic, Type, durationSeconds));
            return response;
        }

        public override void MagicComplete(params object[] data)
        {
            int durationSeconds = (int)data[1];
            if (Player.Buffs.Any(x => x.Type == BuffType.Invisibility)) return;

            Player.BuffAdd(
                BuffType.Invisibility,
                TimeSpan.FromSeconds(durationSeconds),
                new Stats { [Stat.Invisibility] = 1 },
                true,
                false,
                TimeSpan.Zero);

            Player.LevelMagic(Magic);
        }
    }
}
