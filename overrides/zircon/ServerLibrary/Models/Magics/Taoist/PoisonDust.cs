using Library;
using Server.DBModels;
using Server.Envir;
using System;
using System.Drawing;

namespace Server.Models.Magics
{
    [MagicType(MagicType.PoisonDust)]
    public class PoisonDust : MagicObject
    {
        protected override Element Element => Element.None;

        public PoisonDust(PlayerObject player, UserMagic magic) : base(player, magic) { }

        public override MagicCast MagicCast(MapObject target, Point location, MirDirection direction)
        {
            var response = new MagicCast { Ob = target };

            if (target == null || !Player.CanAttackTarget(target))
            {
                response.Cast = false;
                response.Ob = null;
                return response;
            }

            if (!Player.UsePoison(1, out int shape))
            {
                response.Cast = false;
                return response;
            }

            response.Targets.Add(target.ObjectID);

            // Crystal snapshots SC-based power at cast and resolves Poisoning after 500 ms.
            int power = Magic.GetPower() + Player.GetSC();
            PoisonType poisonType = shape == 0 ? PoisonType.Green : PoisonType.Red;

            ActionList.Add(new DelayedAction(
                SEnvir.Now.AddMilliseconds(500),
                ActionType.DelayMagic,
                Type,
                target,
                power,
                poisonType));

            return response;
        }

        public override void MagicComplete(params object[] data)
        {
            MapObject target = (MapObject)data[1];
            int power = (int)data[2];
            PoisonType poisonType = (PoisonType)data[3];

            if (target?.Node == null || target.CurrentMap != CurrentMap || !Player.CanAttackTarget(target)) return;

            int durationSeconds = power * 2 + (Magic.Level + 1) * 7;
            int tickCount = Math.Max(1, durationSeconds / 2);

            int poisonValue = 0;
            if (poisonType == PoisonType.Green)
            {
                int poisonBonus = Player.Stats[Stat.PoisonAttack] > 0
                    ? SEnvir.Random.Next(Player.Stats[Stat.PoisonAttack])
                    : 0;

                poisonValue = power / 15 + Magic.Level + 1 + poisonBonus;
            }

            target.ApplyPoison(new Poison
            {
                Value = poisonValue,
                Type = poisonType,
                Owner = Player,
                TickCount = tickCount,
                TickFrequency = TimeSpan.FromSeconds(2),
            });

            Player.LevelMagic(Magic);
        }
    }
}
