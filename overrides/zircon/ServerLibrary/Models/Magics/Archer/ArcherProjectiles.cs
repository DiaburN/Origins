using Library;
using Server.DBModels;
using Server.Envir;
using System;
using System.Collections.Generic;
using System.Drawing;
using System.Linq;

namespace Server.Models.Magics
{
    public abstract class CrystalArcherProjectile : CrystalArcherMagic
    {
        protected CrystalArcherProjectile(PlayerObject player, UserMagic magic) : base(player, magic) { }

        protected MagicCast QueueSingle(MapObject target, int extraDelay = 0)
        {
            var response = new MagicCast { Ob = target };
            if (!CanCrystalProjectile(target))
            {
                response.Cast = false;
                response.Ob = null;
                return response;
            }

            int distance = RangeDistance(target.CurrentLocation);
            int power = Magic.GetPower() + GetRangeMCPower(distance);
            power = ApplyMentalState(power);
            Point locked = target.CurrentLocation;

            response.Targets.Add(target.ObjectID);
            ActionList.Add(new DelayedAction(
                SEnvir.Now.AddMilliseconds(ProjectileDelay(target) + extraDelay),
                ActionType.DelayMagic,
                Type,
                target,
                locked,
                power));
            return response;
        }

        protected int ResolveLockedTarget(MapObject target, Point locked, int power)
        {
            if (!TargetStillLocked(target, locked)) return 0;
            return Player.MagicAttack(new List<MagicType> { Type }, target, true, null, power);
        }

        public override int ModifyPowerAdditionner(bool primary, int power, MapObject ob, Stats stats = null, int extra = 0)
        {
            return extra != 0 ? extra : power;
        }
    }

    [MagicType(MagicType.StraightShot)]
    public sealed class StraightShot : CrystalArcherProjectile
    {
        public StraightShot(PlayerObject player, UserMagic magic) : base(player, magic) { }

        public override MagicCast MagicCast(MapObject target, Point location, MirDirection direction) => QueueSingle(target);

        public override void MagicComplete(params object[] data)
        {
            ResolveLockedTarget((MapObject)data[1], (Point)data[2], (int)data[3]);
        }
    }

    [MagicType(MagicType.DoubleShot)]
    public sealed class DoubleShot : CrystalArcherProjectile
    {
        public DoubleShot(PlayerObject player, UserMagic magic) : base(player, magic) { }

        public override MagicCast MagicCast(MapObject target, Point location, MirDirection direction)
        {
            var response = new MagicCast { Ob = target };
            if (!CanCrystalProjectile(target))
            {
                response.Cast = false;
                response.Ob = null;
                return response;
            }

            int distance = RangeDistance(target.CurrentLocation);
            int power = ApplyMentalState(Magic.GetPower() + GetRangeMCPower(distance));
            Point locked = target.CurrentLocation;
            int delay = ProjectileDelay(target);

            response.Targets.Add(target.ObjectID);
            ActionList.Add(new DelayedAction(SEnvir.Now.AddMilliseconds(delay), ActionType.DelayMagic, Type, target, locked, power));
            ActionList.Add(new DelayedAction(SEnvir.Now.AddMilliseconds(delay + 50), ActionType.DelayMagic, Type, target, locked, power));
            return response;
        }

        public override void MagicComplete(params object[] data)
        {
            ResolveLockedTarget((MapObject)data[1], (Point)data[2], (int)data[3]);
        }
    }

    public abstract class CrystalDelayedExplosionBase : CrystalArcherProjectile
    {
        protected virtual int ProjectileBaseDelay => 500;
        protected virtual BuffType ExplosionBuff => BuffType.CrystalDelayedExplosion;
        protected virtual bool Infect => false;
        protected virtual int ExplosionTickMilliseconds => 4000;

        protected CrystalDelayedExplosionBase(PlayerObject player, UserMagic magic) : base(player, magic) { }

        public override MagicCast MagicCast(MapObject target, Point location, MirDirection direction)
        {
            var response = new MagicCast { Ob = target };
            if (!CanCrystalProjectile(target))
            {
                response.Cast = false;
                return response;
            }

            int power = Magic.GetPower() + Player.GetMC();
            Point locked = target.CurrentLocation;
            int delay = ProjectileBaseDelay + RangeDistance(locked) * 50;

            response.Targets.Add(target.ObjectID);
            ActionList.Add(new DelayedAction(SEnvir.Now.AddMilliseconds(delay), ActionType.DelayMagic, Type, target, locked, power));
            return response;
        }

        public override void MagicComplete(params object[] data)
        {
            MapObject target = (MapObject)data[1];
            Point locked = (Point)data[2];
            int power = (int)data[3];
            if (!TargetStillLocked(target, locked)) return;

            int damage = Player.MagicAttack(new List<MagicType> { Type }, target, true, null, power);
            if (damage > 0) Player.LevelMagic(Magic);

            target.BuffAdd(
                ExplosionBuff,
                TimeSpan.FromSeconds(Math.Max(6, (power * 2) + (Magic.Level + 1) * 7)),
                new Stats
                {
                    [Stat.CrystalDelayedExplosionPower] = power,
                    [Stat.CrystalDelayedExplosionInfect] = Infect ? 1 : 0,
                },
                false,
                false,
                TimeSpan.FromMilliseconds(ExplosionTickMilliseconds),
                false,
                (int)Player.ObjectID);

            // Base Crystal levels this spell again when the delayed state is attached.
            Player.LevelMagic(Magic);
        }

        public void Explode(Map map, Point location, int power)
        {
            if (map == null || Player.Node == null || Player.Dead) return;

            bool found = false;
            foreach (Cell cell in map.GetCells(location, 0, 1))
            {
                if (cell.Objects == null) continue;

                foreach (MapObject ob in cell.Objects.ToList())
                {
                    if (ob?.Node == null || ob.Dead || !Player.CanAttackTarget(ob)) continue;
                    Player.MagicAttack(new List<MagicType> { Type }, ob, true, null, power);
                    found = true;
                }
            }

            if (found) Player.LevelMagic(Magic);
        }
    }

    [MagicType(MagicType.DelayedExplosion)]
    public sealed class DelayedExplosion : CrystalDelayedExplosionBase
    {
        public DelayedExplosion(PlayerObject player, UserMagic magic) : base(player, magic) { }
    }

    public abstract class CrystalSpecialArrow : CrystalArcherProjectile
    {
        protected CrystalSpecialArrow(PlayerObject player, UserMagic magic) : base(player, magic) { }

        public override MagicCast MagicCast(MapObject target, Point location, MirDirection direction) => QueueSingle(target);

        protected void AddGreenPoison(MapObject target, int value, int divisor)
        {
            if (target?.Node == null || target.Dead) return;

            int poisonBonus = Math.Max(0, Player.Stats[Stat.PoisonAttack]);
            int poisonRoll = poisonBonus == 0 ? 0 : SEnvir.Random.Next(poisonBonus);

            target.ApplyPoison(new Poison
            {
                Owner = Player,
                Type = PoisonType.Green,
                TickCount = Math.Max(1, (value * 2) + (Magic.Level + 1) * 7),
                TickFrequency = TimeSpan.FromSeconds(2),
                Value = value / divisor + Magic.Level + 1 + poisonRoll,
            });
        }
    }

    [MagicType(MagicType.VampireShot)]
    public sealed class VampireShot : CrystalSpecialArrow
    {
        private int _vampAmount;
        private DateTime _vampTime;

        public VampireShot(PlayerObject player, UserMagic magic) : base(player, magic) { }

        public override void MagicComplete(params object[] data)
        {
            MapObject target = (MapObject)data[1];
            Point locked = (Point)data[2];
            int value = (int)data[3];
            int damage = ResolveLockedTarget(target, locked, value);
            if (damage <= 0) return;

            AddVamp(value);

            bool hasVamp = Player.Buffs.Any(x => x.Type == BuffType.CrystalVampireShot);
            bool hasPoison = Player.Buffs.Any(x => x.Type == BuffType.CrystalPoisonShot);

            // Preserve source condition (Random.Next(20) >= 8), regardless of the old 40% comment.
            if (!hasVamp && !hasPoison && SEnvir.Random.Next(20) >= 8)
            {
                Player.BuffAdd(
                    BuffType.CrystalVampireShot,
                    TimeSpan.FromSeconds(5 + 5 * Magic.Level),
                    new Stats(),
                    true,
                    false,
                    TimeSpan.Zero);
            }
        }

        public void AddVamp(int value)
        {
            if (_vampAmount == 0) _vampTime = SEnvir.Now.AddSeconds(1);
            _vampAmount += (int)(value * (Magic.Level + 1) * 0.25F);
        }

        public override void Process()
        {
            if (_vampAmount <= 0 || SEnvir.Now < _vampTime || Player.Dead) return;

            int heal = Math.Min(10, _vampAmount);
            _vampAmount -= heal;
            Player.ChangeHP(heal);
            if (_vampAmount > 0) _vampTime = SEnvir.Now.AddMilliseconds(500);
        }
    }

    [MagicType(MagicType.PoisonShot)]
    public sealed class PoisonShot : CrystalSpecialArrow
    {
        public PoisonShot(PlayerObject player, UserMagic magic) : base(player, magic) { }

        public override void MagicComplete(params object[] data)
        {
            MapObject target = (MapObject)data[1];
            Point locked = (Point)data[2];
            int value = (int)data[3];
            int damage = ResolveLockedTarget(target, locked, value);
            if (damage <= 0) return;

            AddGreenPoison(target, value, 25);

            bool hasVamp = Player.Buffs.Any(x => x.Type == BuffType.CrystalVampireShot);
            bool hasPoison = Player.Buffs.Any(x => x.Type == BuffType.CrystalPoisonShot);
            if (!hasPoison && !hasVamp && SEnvir.Random.Next(20) >= 8)
            {
                Player.BuffAdd(
                    BuffType.CrystalPoisonShot,
                    TimeSpan.FromSeconds(5 + 5 * Magic.Level),
                    new Stats(),
                    true,
                    false,
                    TimeSpan.Zero);
            }
        }
    }

    [MagicType(MagicType.CrippleShot)]
    public sealed class CrippleShot : CrystalSpecialArrow
    {
        public CrippleShot(PlayerObject player, UserMagic magic) : base(player, magic) { }

        public override void MagicComplete(params object[] data)
        {
            MapObject target = (MapObject)data[1];
            Point locked = (Point)data[2];
            int value = (int)data[3];
            if (ResolveLockedTarget(target, locked, value) <= 0) return;

            bool hasVamp = Player.Buffs.Any(x => x.Type == BuffType.CrystalVampireShot);
            bool hasPoison = Player.Buffs.Any(x => x.Type == BuffType.CrystalPoisonShot);
            if (!hasVamp && !hasPoison) return;

            if (hasVamp) Player.BuffRemove(BuffType.CrystalVampireShot);
            if (hasPoison) Player.BuffRemove(BuffType.CrystalPoisonShot);

            VampireShot vampire = null;
            if (hasVamp && Player.GetMagic(MagicType.VampireShot, out MagicObject vampMagic))
                vampire = vampMagic as VampireShot;

            foreach (Cell cell in CurrentMap.GetCells(target.CurrentLocation, 0, 1))
            {
                if (cell.Objects == null) continue;

                foreach (MapObject areaTarget in cell.Objects.ToList())
                {
                    if (areaTarget?.Node == null || areaTarget.Dead || !Player.CanAttackTarget(areaTarget)) continue;

                    if (hasVamp)
                    {
                        // Crystal's implementation deliberately re-hits the original
                        // target once for every hostile object found in the 3x3.
                        Player.MagicAttack(new List<MagicType> { Type }, target, true, null, value);
                        vampire?.AddVamp(value);
                    }

                    if (hasPoison)
                        AddGreenPoison(areaTarget, value, 25);
                }
            }
        }
    }

    [MagicType(MagicType.NapalmShot)]
    public sealed class NapalmShot : CrystalArcherProjectile
    {
        public NapalmShot(PlayerObject player, UserMagic magic) : base(player, magic) { }

        public override MagicCast MagicCast(MapObject target, Point location, MirDirection direction)
        {
            var response = new MagicCast { Ob = target };
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
            int power = (int)data[3];
            if (map != CurrentMap) return;

            bool train = false;
            foreach (Cell cell in map.GetCells(impact, 0, 2))
            {
                if (cell.Objects == null) continue;
                foreach (MapObject ob in cell.Objects.ToList())
                {
                    if (ob?.Node == null || ob.Dead || !Player.CanAttackTarget(ob)) continue;
                    Player.MagicAttack(new List<MagicType> { Type }, ob, true, null, power);
                    train = true;
                }
            }
            if (train) Player.LevelMagic(Magic);
        }

        public override int ModifyPowerAdditionner(bool primary, int power, MapObject ob, Stats stats = null, int extra = 0) => extra;
    }

    [MagicType(MagicType.OneWithNature)]
    public sealed class OneWithNature : CrystalArcherProjectile
    {
        public OneWithNature(PlayerObject player, UserMagic magic) : base(player, magic) { }

        public override MagicCast MagicCast(MapObject target, Point location, MirDirection direction)
        {
            var response = new MagicCast { Ob = Player };
            int power = Magic.GetPower() + Player.GetMC();
            ActionList.Add(new DelayedAction(
                SEnvir.Now.AddMilliseconds(500),
                ActionType.DelayMagic,
                Type,
                CurrentMap,
                CurrentLocation,
                power));
            return response;
        }

        public override void MagicComplete(params object[] data)
        {
            Map map = (Map)data[1];
            Point location = (Point)data[2];
            int value = (int)data[3];
            if (map != CurrentMap) return;

            bool hasVamp = Player.Buffs.Any(x => x.Type == BuffType.CrystalVampireShot);
            bool hasPoison = Player.Buffs.Any(x => x.Type == BuffType.CrystalPoisonShot);
            VampireShot vampire = null;
            if (hasVamp && Player.GetMagic(MagicType.VampireShot, out MagicObject vampMagic))
                vampire = vampMagic as VampireShot;

            bool train = false;
            foreach (Cell cell in map.GetCells(location, 0, 2))
            {
                if (cell.Objects == null) continue;
                foreach (MapObject ob in cell.Objects.ToList())
                {
                    if (ob?.Node == null || ob.Dead || !Player.CanAttackTarget(ob)) continue;

                    int damage = Player.MagicAttack(new List<MagicType> { Type }, ob, true, null, value);
                    if (damage <= 0) continue;

                    if (hasVamp) vampire?.AddVamp(value);
                    if (hasPoison)
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

    [MagicType(MagicType.BindingShot)]
    public sealed class BindingShot : CrystalArcherProjectile
    {
        public BindingShot(PlayerObject player, UserMagic magic) : base(player, magic) { }

        public override MagicCast MagicCast(MapObject target, Point location, MirDirection direction)
        {
            var response = new MagicCast { Ob = target };
            if (target is not MonsterObject monster || !Player.CanAttackTarget(monster) || monster.Level > Player.Level + 2 || SEnvir.Now < monster.ShockTime || !CanCrystalProjectile(monster))
            {
                response.Cast = false;
                return response;
            }

            int durationMs = (Magic.Level * 5 + 10) * 1000;
            Point locked = target.CurrentLocation;
            response.Targets.Add(target.ObjectID);
            ActionList.Add(new DelayedAction(
                SEnvir.Now.AddMilliseconds(ProjectileDelay(target)),
                ActionType.DelayMagic,
                Type,
                target,
                locked,
                durationMs));
            return response;
        }

        public override void MagicComplete(params object[] data)
        {
            MapObject target = (MapObject)data[1];
            Point locked = (Point)data[2];
            int durationMs = (int)data[3];
            if (!TargetStillLocked(target, locked) || target is not MonsterObject center || SEnvir.Now < center.ShockTime) return;

            bool train = false;
            foreach (Cell cell in CurrentMap.GetCells(center.CurrentLocation, 0, 1))
            {
                if (cell.Objects == null) continue;
                foreach (MapObject ob in cell.Objects.ToList())
                {
                    if (ob is not MonsterObject monster || monster.Node == null || !Player.CanAttackTarget(monster) || monster.Level > Player.Level + 2) continue;
                    monster.ShockTime = SEnvir.Now.AddMilliseconds(durationMs);
                    monster.Target = null;
                    train = true;
                }
            }

            if (train) Player.LevelMagic(Magic);
        }
    }
}
