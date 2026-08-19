using Library;
using Server.DBModels;
using Server.Envir;
using System;
using System.Drawing;

namespace Server.Models.Magics
{
    [MagicType(MagicType.Curse)]
    public sealed class Curse : MagicObject
    {
        protected override Element Element => Element.None;
        public override bool UpdateCombatTime => false;

        public Curse(PlayerObject player, UserMagic magic) : base(player, magic) { }

        public override MagicCast MagicCast(MapObject target, Point location, MirDirection direction)
        {
            var response = new MagicCast { Ob = null };

            if (!Functions.InRange(CurrentLocation, location, Globals.MagicRange) || !Player.UseAmulet(1, 0))
            {
                response.Cast = false;
                return response;
            }

            // Crystal has a cast-level gate before the area is emitted.
            int castRoll = Math.Max(1, 10 - ((Magic.Level + 1) * 2));
            if (SEnvir.Random.Next(castRoll) > 2)
                return response;

            response.Locations.Add(location);

            int durationSeconds = Magic.GetPower() + Player.GetSC();
            int reductionPercent = 1 + ((Magic.Level + 1) * 2);
            var delay = SEnvir.Now.AddMilliseconds(500 + Functions.Distance(CurrentLocation, location) * 50);

            foreach (Cell cell in CurrentMap.GetCells(location, 0, 3))
                ActionList.Add(new DelayedAction(delay, ActionType.DelayMagic, Type, cell, durationSeconds, reductionPercent));

            return response;
        }

        public override void MagicComplete(params object[] data)
        {
            Cell cell = (Cell)data[1];
            int durationSeconds = (int)data[2];
            int reductionPercent = (int)data[3];
            if (cell?.Objects == null) return;

            bool trained = false;

            for (int i = cell.Objects.Count - 1; i >= 0; i--)
            {
                MapObject ob = cell.Objects[i];
                if (ob?.Node == null || !Player.CanAttackTarget(ob)) continue;

                // Crystal applies a second 40% roll independently to every target.
                if (SEnvir.Random.Next(10) >= 4) continue;

                ob.ApplyPoison(new Poison
                {
                    Owner = Player,
                    Type = PoisonType.Slow,
                    Value = reductionPercent,
                    TickCount = durationSeconds,
                    TickFrequency = TimeSpan.FromSeconds(1),
                });

                Stats stats = new Stats
                {
                    [Stat.DCPercent] = -reductionPercent,
                    [Stat.MCPercent] = -reductionPercent,
                    [Stat.SCPercent] = -reductionPercent,
                };

                // Crystal only reduces AttackSpeed on player targets.
                if (ob.Race == ObjectType.Player)
                    stats[Stat.AttackSpeed] = -(ob.Stats[Stat.AttackSpeed] * reductionPercent / 100);

                ob.BuffAdd(BuffType.Curse, TimeSpan.FromSeconds(durationSeconds), stats, true, false, TimeSpan.Zero);
                trained = true;
            }

            if (trained)
                Player.LevelMagic(Magic);
        }
    }
}
