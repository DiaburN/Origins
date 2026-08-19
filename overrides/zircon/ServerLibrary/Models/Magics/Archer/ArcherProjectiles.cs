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

        protected int RangeMCPower(int distance, bool mentalState = true)
        {
            int min = Math.Max(0, Player.Stats[Stat.MinMC]);
            int max = Math.Max(min, Player.Stats[Stat.MaxMC]);
            int clamped = Math.Max(0, Math.Min(9, distance));
            decimal x = ((decimal)min / 9M) * (9 - clamped);
            min -= (int)Math.Floor(x);
            int roll = min >= max ? max : SEnvir.Random.Next(min, max + 1);
            int damage = Magic.GetPower() + roll;
            return mentalState ? ApplyMentalState(damage) : damage;
        }

        protected MagicCast QueueTarget(MapObject target, int power, int baseDelay = 500)
        {
            var response = new MagicCast { Ob = target };
            if (!CanCrystalProjectile(target))
            {
                response.Cast = false;
                response.Ob = null;
                return response;
            }

            Point locked = target.CurrentLocation;
            response.Targets.Add(target.ObjectID);
            ActionList.Add(new DelayedAction(
                SEnvir.Now.AddMilliseconds(ProjectileDelay(target, baseDelay)),
                ActionType.DelayMagic, Type, target, locked, power));
            return response;
        }

        protected int ResolveTarget(MapObject target, Point locked, int power)
        {
            if (!TargetStillLocked(target, locked)) return 0;
            return Player.MagicAttack(new List<MagicType> { Type }, target, true, null, power);
        }

        public override int ModifyPowerAdditionner(bool primary, int power, MapObject ob, Stats stats = null, int extra = 0) => extra;
    }

    [MagicType(MagicType.StraightShot)]
    public sealed class StraightShot : CrystalArcherProjectile
    {
        public StraightShot(PlayerObject player, UserMagic magic) : base(player, magic) { }
        public override MagicCast MagicCast(MapObject target, Point location, MirDirection direction)
        {
            int distance = target == null ? 0 : RangeDistance(target.CurrentLocation);
            return QueueTarget(target, RangeMCPower(distance));
        }
        public override void MagicComplete(params object[] data)
        {
            if (ResolveTarget((MapObject)data[1], (Point)data[2], (int)data[3]) > 0) Player.LevelMagic(Magic);
        }
    }

    [MagicType(MagicType.DoubleShot)]
    public sealed class DoubleShot : CrystalArcherProjectile
    {
        public DoubleShot(PlayerObject player, UserMagic magic) : base(player, magic) { }
        public override MagicCast MagicCast(MapObject target, Point location, MirDirection direction)
        {
            int distance = target == null ? 0 : RangeDistance(target.CurrentLocation);
            return QueueTarget(target, RangeMCPower(distance));
        }
        public override void MagicComplete(params object[] data)
        {
            if (ResolveTarget((MapObject)data[1], (Point)data[2], (int)data[3]) > 0) Player.LevelMagic(Magic);
        }
    }

    public abstract class CrystalDelayedExplosionBase : CrystalArcherProjectile
    {
        protected virtual int FlightBaseDelay => 500;
        protected virtual BuffType ExplosionBuff => BuffType.CrystalDelayedExplosion;
        protected virtual bool Infect => false;
        protected CrystalDelayedExplosionBase(PlayerObject player, UserMagic magic) : base(player, magic) { }

        public override MagicCast MagicCast(MapObject target, Point location, MirDirection direction)
        {
            var response = new MagicCast { Ob = target };
            if (!CanCrystalProjectile(target)) { response.Cast = false; return response; }
            int power = Magic.GetPower() + Player.GetMC();
            Point locked = target.CurrentLocation;
            response.Targets.Add(target.ObjectID);
            ActionList.Add(new DelayedAction(SEnvir.Now.AddMilliseconds(ProjectileDelay(target, FlightBaseDelay)), ActionType.DelayMagic, Type, target, locked, power));
            return response;
        }

        public override void MagicComplete(params object[] data)
        {
            MapObject target = (MapObject)data[1];
            Point locked = (Point)data[2];
            int power = (int)data[3];
            if (!TargetStillLocked(target, locked)) return;
            int damage = Player.MagicAttack(new List<MagicType> { Type }, target, true, null, power);
            if (damage <= 0) return;

            target.BuffAdd(ExplosionBuff, TimeSpan.FromSeconds(8), new Stats
            {
                [Stat.CrystalDelayedExplosionPower] = power,
                [Stat.CrystalDelayedExplosionInfect] = Infect ? 1 : 0,
            }, false, false, TimeSpan.FromSeconds(7), false, (int)Player.ObjectID);
            Player.LevelMagic(Magic);
        }
    }

    [MagicType(MagicType.DelayedExplosion)]
    public sealed class DelayedExplosion : CrystalDelayedExplosionBase
    {
        public DelayedExplosion(PlayerObject player, UserMagic magic) : base(player, magic) { }
    }

    [MagicType(MagicType.DelayedExplosion2)]
    public sealed class DelayedExplosion2 : CrystalDelayedExplosionBase
    {
        protected override int FlightBaseDelay => 2600;
        protected override BuffType ExplosionBuff => BuffType.CrystalDelayedExplosion2;
        protected override bool Infect => true;
        public DelayedExplosion2(PlayerObject player, UserMagic magic) : base(player, magic) { }
    }

    public abstract class CrystalSpecialArrow : CrystalArcherProjectile
    {
        protected CrystalSpecialArrow(PlayerObject player, UserMagic magic) : base(player, magic) { }
        protected void ApplyGreenPoison(MapObject target, int power, byte skillLevel)
        {
            if (target?.Node == null || target.Dead) return;
            int bonus = Player.Stats[Stat.PoisonAttack] > 0 ? SEnvir.Random.Next(Player.Stats[Stat.PoisonAttack]) : 0;
            int durationSeconds = power * 2 + (skillLevel + 1) * 7;
            target.ApplyPoison(new Poison
            {
                Owner = Player, Type = PoisonType.Green,
                Value = power / 25 + skillLevel + 1 + bonus,
                TickCount = Math.Max(1, durationSeconds / 2),
                TickFrequency = TimeSpan.FromSeconds(2),
            });
        }
        protected static void ShortenBuff(PlayerObject player, BuffType type)
        {
            BuffInfo buff = player.Buffs.FirstOrDefault(x => x.Type == type);
            if (buff != null && buff.RemainingTime > TimeSpan.FromSeconds(1)) buff.RemainingTime = TimeSpan.FromSeconds(1);
        }
    }

    [MagicType(MagicType.VampireShot)]
    public sealed class VampireShot : CrystalSpecialArrow
    {
        private int _vampAmount;
        private DateTime _vampTime;
        public VampireShot(PlayerObject player, UserMagic magic) : base(player, magic) { }
        public override MagicCast MagicCast(MapObject target, Point location, MirDirection direction)
        {
            int distance = target == null ? 0 : RangeDistance(target.CurrentLocation);
            return QueueTarget(target, RangeMCPower(distance));
        }
        internal void AddVamp(int power, byte skillLevel)
        {
            if (_vampAmount == 0) _vampTime = SEnvir.Now.AddSeconds(1);
            _vampAmount += (int)(power * (skillLevel + 1) * 0.25F);
        }
        public override void MagicComplete(params object[] data)
        {
            MapObject target = (MapObject)data[1]; Point locked = (Point)data[2]; int power = (int)data[3];
            if (ResolveTarget(target, locked, power) <= 0) return;
            bool hasVamp = Player.Buffs.Any(x => x.Type == BuffType.CrystalVampireShot);
            bool hasPoison = Player.Buffs.Any(x => x.Type == BuffType.CrystalPoisonShot);
            if (!hasVamp && !hasPoison && SEnvir.Random.Next(20) >= 8)
                Player.BuffAdd(BuffType.CrystalVampireShot, TimeSpan.FromSeconds(5 + 5 * Magic.Level), new Stats(), true, false, TimeSpan.Zero);
            AddVamp(power, Magic.Level);
            Player.LevelMagic(Magic);
        }
        public override void Process()
        {
            if (_vampAmount <= 0 || Player.Dead || SEnvir.Now < _vampTime) return;
            int heal = Math.Min(10, _vampAmount); _vampAmount -= heal; Player.ChangeHP(heal); _vampTime = SEnvir.Now.AddMilliseconds(500);
        }
    }

    [MagicType(MagicType.PoisonShot)]
    public sealed class PoisonShot : CrystalSpecialArrow
    {
        public PoisonShot(PlayerObject player, UserMagic magic) : base(player, magic) { }
        public override MagicCast MagicCast(MapObject target, Point location, MirDirection direction)
        {
            int distance = target == null ? 0 : RangeDistance(target.CurrentLocation);
            return QueueTarget(target, RangeMCPower(distance));
        }
        public override void MagicComplete(params object[] data)
        {
            MapObject target = (MapObject)data[1]; Point locked = (Point)data[2]; int power = (int)data[3];
            if (ResolveTarget(target, locked, power) <= 0) return;
            bool hasVamp = Player.Buffs.Any(x => x.Type == BuffType.CrystalVampireShot);
            bool hasPoison = Player.Buffs.Any(x => x.Type == BuffType.CrystalPoisonShot);
            if (!hasVamp && !hasPoison && SEnvir.Random.Next(20) >= 8)
                Player.BuffAdd(BuffType.CrystalPoisonShot, TimeSpan.FromSeconds(5 + 5 * Magic.Level), new Stats(), true, false, TimeSpan.Zero);
            ApplyGreenPoison(target, power, Magic.Level);
            Player.LevelMagic(Magic);
        }
    }

    [MagicType(MagicType.CrippleShot)]
    public sealed class CrippleShot : CrystalSpecialArrow
    {
        public CrippleShot(PlayerObject player, UserMagic magic) : base(player, magic) { }
        public override MagicCast MagicCast(MapObject target, Point location, MirDirection direction)
        {
            int distance = target == null ? 0 : RangeDistance(target.CurrentLocation);
            return QueueTarget(target, RangeMCPower(distance));
        }
        public override void MagicComplete(params object[] data)
        {
            MapObject target = (MapObject)data[1]; Point locked = (Point)data[2]; int power = (int)data[3];
            if (ResolveTarget(target, locked, power) <= 0) return;
            bool hasVamp = Player.Buffs.Any(x => x.Type == BuffType.CrystalVampireShot);
            bool hasPoison = Player.Buffs.Any(x => x.Type == BuffType.CrystalPoisonShot);
            if (hasVamp || hasPoison)
            {
                foreach (Cell cell in CurrentMap.GetCells(target.CurrentLocation, 0, 1))
                {
                    if (cell?.Objects == null) continue;
                    foreach (MapObject victim in cell.Objects.ToList())
                    {
                        if (victim?.Node == null || victim.Dead || !Player.CanAttackTarget(victim)) continue;
                        if (hasVamp)
                        {
                            int dealt = Player.MagicAttack(new List<MagicType> { Type }, victim, true, null, power);
                            if (dealt > 0 && Player.GetMagic(MagicType.VampireShot, out VampireShot vampire)) vampire.AddVamp(power, Magic.Level);
                        }
                        if (hasPoison) ApplyGreenPoison(victim, power, Magic.Level);
                    }
                }
                if (hasVamp) ShortenBuff(Player, BuffType.CrystalVampireShot);
                if (hasPoison) ShortenBuff(Player, BuffType.CrystalPoisonShot);
            }
            Player.LevelMagic(Magic);
        }
    }

    public abstract class CrystalNapalmBase : CrystalSpecialArrow
    {
        protected virtual bool ConsumeSpecialState => false;
        protected CrystalNapalmBase(PlayerObject player, UserMagic magic) : base(player, magic) { }
        public override MagicCast MagicCast(MapObject target, Point location, MirDirection direction)
        {
            var response = new MagicCast { Ob = target };
            if (!CanCrystalProjectile(target)) { response.Cast = false; return response; }
            int distance = RangeDistance(target.CurrentLocation);
            int power = RangeMCPower(distance);
            Point impact = target.CurrentLocation;
            response.Targets.Add(target.ObjectID);
            ActionList.Add(new DelayedAction(SEnvir.Now.AddMilliseconds(ProjectileDelay(target)), ActionType.DelayMagic, Type, impact, power));
            return response;
        }
        public override void MagicComplete(params object[] data)
        {
            Point location = (Point)data[1]; int power = (int)data[2];
            bool hasVamp = ConsumeSpecialState && Player.Buffs.Any(x => x.Type == BuffType.CrystalVampireShot);
            bool hasPoison = ConsumeSpecialState && Player.Buffs.Any(x => x.Type == BuffType.CrystalPoisonShot);
            bool trained = false;
            foreach (Cell cell in CurrentMap.GetCells(location, 0, 2))
            {
                if (cell?.Objects == null) continue;
                foreach (MapObject victim in cell.Objects.ToList())
                {
                    if (victim?.Node == null || victim.Dead || !Player.CanAttackTarget(victim)) continue;
                    int dealt = Player.MagicAttack(new List<MagicType> { Type }, victim, true, null, power);
                    if (dealt <= 0) continue;
                    trained = true;
                    if (hasVamp && Player.GetMagic(MagicType.VampireShot, out VampireShot vampire)) vampire.AddVamp(power, Magic.Level);
                    if (hasPoison) ApplyGreenPoison(victim, power, Magic.Level);
                }
            }
            if (hasVamp) ShortenBuff(Player, BuffType.CrystalVampireShot);
            if (hasPoison) ShortenBuff(Player, BuffType.CrystalPoisonShot);
            if (trained) Player.LevelMagic(Magic);
        }
    }

    [MagicType(MagicType.NapalmShot)]
    public sealed class NapalmShot : CrystalNapalmBase { public NapalmShot(PlayerObject player, UserMagic magic) : base(player, magic) { } }

    [MagicType(MagicType.NapalmShot2)]
    public sealed class NapalmShot2 : CrystalNapalmBase
    {
        protected override bool ConsumeSpecialState => true;
        public NapalmShot2(PlayerObject player, UserMagic magic) : base(player, magic) { }
    }

    [MagicType(MagicType.OneWithNature)]
    public sealed class OneWithNature : CrystalSpecialArrow
    {
        public OneWithNature(PlayerObject player, UserMagic magic) : base(player, magic) { }
        public override MagicCast MagicCast(MapObject target, Point location, MirDirection direction)
        {
            int power = Magic.GetPower() + Player.GetMC();
            ActionList.Add(new DelayedAction(SEnvir.Now.AddMilliseconds(500), ActionType.DelayMagic, Type, Player.CurrentLocation, power));
            return new MagicCast { Ob = Player };
        }
        public override void MagicComplete(params object[] data)
        {
            Point location = (Point)data[1]; int power = (int)data[2];
            bool hasVamp = Player.Buffs.Any(x => x.Type == BuffType.CrystalVampireShot);
            bool hasPoison = Player.Buffs.Any(x => x.Type == BuffType.CrystalPoisonShot);
            bool trained = false;
            foreach (Cell cell in CurrentMap.GetCells(location, 0, 2))
            {
                if (cell?.Objects == null) continue;
                foreach (MapObject victim in cell.Objects.ToList())
                {
                    if (victim?.Node == null || victim.Dead || !Player.CanAttackTarget(victim)) continue;
                    int dealt = Player.MagicAttack(new List<MagicType> { Type }, victim, true, null, power);
                    if (dealt <= 0) continue;
                    trained = true;
                    if (hasVamp && Player.GetMagic(MagicType.VampireShot, out VampireShot vampire)) vampire.AddVamp(power, Magic.Level);
                    if (hasPoison) ApplyGreenPoison(victim, power, Magic.Level);
                }
            }
            if (hasVamp) ShortenBuff(Player, BuffType.CrystalVampireShot);
            if (hasPoison) ShortenBuff(Player, BuffType.CrystalPoisonShot);
            if (trained) Player.LevelMagic(Magic);
        }
    }

    [MagicType(MagicType.BindingShot)]
    public sealed class BindingShot : CrystalArcherProjectile
    {
        public BindingShot(PlayerObject player, UserMagic magic) : base(player, magic) { }
        public override MagicCast MagicCast(MapObject target, Point location, MirDirection direction)
        {
            var response = new MagicCast { Ob = target };
            if (target is not MonsterObject monster || !Player.CanAttackTarget(monster) || monster.Level > Player.Level + 2 || monster.ShockTime > SEnvir.Now || !CanCrystalProjectile(monster))
            { response.Cast = false; return response; }
            int durationMs = (Magic.Level * 5 + 10) * 1000;
            Point locked = monster.CurrentLocation;
            response.Targets.Add(monster.ObjectID);
            ActionList.Add(new DelayedAction(SEnvir.Now.AddMilliseconds(ProjectileDelay(monster)), ActionType.DelayMagic, Type, monster, locked, durationMs));
            return response;
        }
        public override void MagicComplete(params object[] data)
        {
            MonsterObject target = (MonsterObject)data[1]; Point locked = (Point)data[2]; int durationMs = (int)data[3];
            if (!TargetStillLocked(target, locked) || target.ShockTime > SEnvir.Now) return;
            bool trained = false;
            foreach (Cell cell in CurrentMap.GetCells(target.CurrentLocation, 0, 1))
            {
                if (cell?.Objects == null) continue;
                foreach (MapObject ob in cell.Objects.ToList())
                {
                    if (ob is not MonsterObject monster || monster.Node == null || !Player.CanAttackTarget(monster) || monster.Level > Player.Level + 2) continue;
                    monster.ShockTime = SEnvir.Now.AddMilliseconds(durationMs); monster.Target = null; trained = true;
                }
            }
            if (trained) Player.LevelMagic(Magic);
        }
    }
}
