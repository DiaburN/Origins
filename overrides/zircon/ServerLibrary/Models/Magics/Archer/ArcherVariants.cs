using Library;
using Server.DBModels;
using Server.Envir;
using System;
using System.Collections.Generic;
using System.Drawing;
using System.Linq;

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

            // Jev consumes/reset the elemental state regardless of stored orb tier.
            Player.CrystalArcherElementsLevel = 0;

            int reduction = (Magic.Level + 2) * 10; // 20/30/40/50%.
            Player.BuffAdd(
                BuffType.CrystalElementalBarrier1,
                TimeSpan.FromSeconds(duration),
                new Stats { [Stat.CrystalArcherBarrierReductionPercent] = reduction },
                true,
                false,
                TimeSpan.Zero);

            Player.LevelMagic(Magic);
        }
    }

    [MagicType(MagicType.DelayedExplosion2)]
    public sealed class DelayedExplosion2 : CrystalDelayedExplosionBase
    {
        protected override int ProjectileBaseDelay => 2600;
        protected override BuffType ExplosionBuff => BuffType.CrystalDelayedExplosion2;
        protected override bool Infect => true;
        protected override int ExplosionTickMilliseconds => 1500;

        public DelayedExplosion2(PlayerObject player, UserMagic magic) : base(player, magic) { }

        public override void MagicComplete(params object[] data)
        {
            MapObject target = (MapObject)data[1];
            Point locked = (Point)data[2];
            int power = (int)data[3];
            if (!TargetStillLocked(target, locked)) return;

            // Jev's second version does not add a separate impact-damage call here;
            // it seeds the six-tick infecting delayed-explosion state.
            target.BuffAdd(
                BuffType.CrystalDelayedExplosion2,
                TimeSpan.FromSeconds(6),
                new Stats
                {
                    [Stat.CrystalDelayedExplosionPower] = power,
                    [Stat.CrystalDelayedExplosionInfect] = 1,
                },
                false,
                false,
                TimeSpan.FromMilliseconds(1500),
                false,
                (int)Player.ObjectID);

            Player.LevelMagic(Magic);
        }
    }

    [MagicType(MagicType.NapalmShot2)]
    public sealed class NapalmShot2 : CrystalArcherProjectile
    {
        public NapalmShot2(PlayerObject player, UserMagic magic) : base(player, magic) { }

        public override MagicCast MagicCast(MapObject target, Point location, MirDirection direction)
        {
            var response = new MagicCast { Ob = target, Return = true };
            if (!CanCrystalProjectile(target))
            {
                response.Cast = false;
                return response;
            }

            int distance = RangeDistance(target.CurrentLocation);
            int power = ApplyMentalState(Magic.GetPower() + GetRangeMCPower(distance));
            Point impact = target.CurrentLocation;

            response.Targets.Add(target.ObjectID);
            ActionList.Add(new DelayedAction(
                SEnvir.Now.AddMilliseconds(ProjectileDelay(target)),
                ActionType.DelayMagic,
                Type,
                CurrentMap,
                impact,
                power));

            return response;
        }

        public override void MagicComplete(params object[] data)
        {
            Map map = (Map)data[1];
            Point impact = (Point)data[2];
            int value = (int)data[3];
            if (map != CurrentMap) return;

            bool hasVamp = Player.Buffs.Any(x => x.Type == BuffType.CrystalVampireShot);
            bool hasPoison = Player.Buffs.Any(x => x.Type == BuffType.CrystalPoisonShot);

            // Source contains: value = (int)1.3F * value.  The cast to int happens
            // before multiplication, so it is effectively value = 1 * value.
            int hitPower = (hasVamp || hasPoison) ? value * 2 : value;

            VampireShot vampire = null;
            if (hasVamp && Player.GetMagic(MagicType.VampireShot, out MagicObject vampMagic))
                vampire = vampMagic as VampireShot;

            bool train = false;
            foreach (Cell cell in map.GetCells(impact, 0, 2))
            {
                if (cell.Objects == null) continue;
                foreach (MapObject ob in cell.Objects.ToList())
                {
                    if (ob?.Node == null || ob.Dead || !Player.CanAttackTarget(ob)) continue;

                    Player.MagicAttack(new List<MagicType> { Type }, ob, true, null, hitPower);

                    if (hasPoison && SEnvir.Random.Next(5) == 0)
                    {
                        int poisonBonus = Math.Max(0, Player.Stats[Stat.PoisonAttack]);
                        int roll = poisonBonus == 0 ? 0 : SEnvir.Random.Next(poisonBonus);
                        ob.ApplyPoison(new Poison
                        {
                            Owner = Player,
                            Type = PoisonType.Green,
                            TickCount = Math.Max(1, (value * 2) + (Magic.Level + 1) * 7),
                            TickFrequency = TimeSpan.FromSeconds(2),
                            Value = value / 15 + Magic.Level + 1 + roll,
                        });
                    }

                    if (hasVamp)
                        vampire?.AddVamp(value);

                    train = true;
                }
            }

            if (hasVamp)
            {
                BuffInfo buff = Player.Buffs.FirstOrDefault(x => x.Type == BuffType.CrystalVampireShot);
                if (buff != null) buff.RemainingTime = TimeSpan.FromSeconds(1);
            }
            if (hasPoison)
            {
                BuffInfo buff = Player.Buffs.FirstOrDefault(x => x.Type == BuffType.CrystalPoisonShot);
                if (buff != null) buff.RemainingTime = TimeSpan.FromSeconds(1);
            }

            if (train) Player.LevelMagic(Magic);
        }

        public override int ModifyPowerAdditionner(bool primary, int power, MapObject ob, Stats stats = null, int extra = 0) => extra;
    }
}
