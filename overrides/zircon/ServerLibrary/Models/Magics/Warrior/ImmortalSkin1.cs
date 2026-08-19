using Library;
using Server.DBModels;
using Server.Envir;
using System;
using System.Drawing;

namespace Server.Models.Magics
{
    [MagicType(MagicType.ImmortalSkin1)]
    public sealed class ImmortalSkin1 : MagicObject
    {
        protected override Element Element => Element.None;
        public override bool UpdateCombatTime => false;

        private DateTime BuffExpiry;
        private DateTime RegenTick;
        private int RegenPool;

        public ImmortalSkin1(PlayerObject player, UserMagic magic) : base(player, magic)
        {
        }

        public override MagicCast MagicCast(MapObject target, Point location, MirDirection direction)
        {
            ActionList.Add(new DelayedAction(
                SEnvir.Now.AddMilliseconds(500),
                ActionType.DelayMagic,
                Type));

            return new MagicCast
            {
                Ob = null,
                Direction = MirDirection.Down,
            };
        }

        public override void MagicComplete(params object[] data)
        {
            int reduce = 50 - Magic.Level * 10;
            int regen = 400 + Magic.Level * 100 + Math.Max(0, Player.Stats[Stat.Luck] * 100);

            Player.BuffRemove(BuffType.ImmortalSkin);
            Player.BuffAdd(
                BuffType.ImmortalSkin,
                TimeSpan.FromSeconds(50),
                new Stats
                {
                    [Stat.IncomingDamageReductionPercent] = 60,
                    [Stat.DCPercent] = -reduce,
                },
                true,
                false,
                TimeSpan.Zero);

            BuffExpiry = SEnvir.Now.AddSeconds(50);
            RegenPool = regen;
            RegenTick = BuffExpiry;

            Player.LevelMagic(Magic);
        }

        public override void Process()
        {
            // Crystal-Monk transfers Values[2] to VampAmount when the 50-second
            // ImmortalSkin buff expires. HumanObject then restores at most 10 HP
            // every 500 ms until that pool is exhausted.
            if (RegenPool <= 0 || SEnvir.Now < BuffExpiry || Player.Dead) return;
            if (SEnvir.Now < RegenTick) return;

            RegenTick = SEnvir.Now.AddMilliseconds(500);

            int heal = Math.Min(10, RegenPool);
            RegenPool -= heal;
            Player.ChangeHP(heal);
        }
    }
}
