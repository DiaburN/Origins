using Library;
using Server.DBModels;
using Server.Envir;
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

            // Jev Crystal-Monk Healing2 is not a direct heal: it grants temporary MaxHP.
            int hpBonus = Magic.GetPower() + Player.GetSC() + Player.Level;
            int durationSeconds = Player.GetSC() + 25 + Magic.Level * 25;

            ActionList.Add(new DelayedAction(
                SEnvir.Now.AddMilliseconds(500),
                ActionType.DelayMagic,
                Type,
                target,
                hpBonus,
                durationSeconds));

            return response;
        }

        public override void MagicComplete(params object[] data)
        {
            MapObject target = (MapObject)data[1];
            int hpBonus = (int)data[2];
            int durationSeconds = (int)data[3];

            if (target?.Node == null || !Player.CanHelpTarget(target)) return;

            target.BuffAdd(
                BuffType.CrystalHealing2,
                TimeSpan.FromSeconds(durationSeconds),
                new Stats { [Stat.Health] = hpBonus },
                true,
                false,
                TimeSpan.Zero);

            Player.LevelMagic(Magic);
        }
    }
}
