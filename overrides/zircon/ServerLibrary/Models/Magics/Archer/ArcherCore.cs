using Library;
using Server.DBModels;
using Server.Envir;
using System;
using System.Collections.Generic;
using System.Drawing;
using System.Linq;
using S = Library.Network.ServerPackets;

namespace Server.Models.Magics
{
    public abstract class CrystalArcherMagic : MagicObject
    {
        protected override Element Element => Element.None;

        protected CrystalArcherMagic(PlayerObject player, UserMagic magic) : base(player, magic) { }

        protected int RangeDistance(Point point)
        {
            return Math.Max(Math.Abs(CurrentLocation.X - point.X), Math.Abs(CurrentLocation.Y - point.Y));
        }

        protected int GetRangeMCPower(int range)
        {
            int min = Player.Stats[Stat.MinMC];
            int max = Player.Stats[Stat.MaxMC];
            range = Math.Max(0, Math.Min(9, range));

            decimal loss = ((decimal)min / 9M) * (9 - range);
            min -= (int)Math.Floor(loss);

            int roll = min >= max ? max : SEnvir.Random.Next(min, max + 1);
            return roll;
        }

        protected int ApplyMentalState(int damage)
        {
            switch (Player.CrystalArcherMentalState)
            {
                case 1: // Crystal Trickshot.
                    return damage * (55 + Player.CrystalArcherMentalStateLevel * 5) / 100;
                case 2: // Crystal group-attack stance.
                    return damage * 80 / 100;
                default:
                    return damage;
            }
        }

        protected bool CanCrystalProjectile(MapObject target)
        {
            if (target?.Node == null || !Player.CanAttackTarget(target)) return false;

            // Crystal Trickshot is the only mental state allowed to ignore the
            // normal CanFly projectile-line check. Zircon's map line-of-sight
            // remains authoritative for the two normal states.
            if (Player.CrystalArcherMentalState == 1) return true;
            return CurrentMap.LineOfSight(CurrentLocation, target.CurrentLocation);
        }

        protected int ProjectileDelay(MapObject target, int baseDelay = 500)
        {
            return baseDelay + RangeDistance(target.CurrentLocation) * 50;
        }

        protected bool TargetStillLocked(MapObject target, Point lockedLocation)
        {
            if (target?.Node == null || target.Dead || target.CurrentMap != CurrentMap || !Player.CanAttackTarget(target)) return false;
            return Functions.InRange(target.CurrentLocation, lockedLocation, 2);
        }
    }

    [MagicType(MagicType.Focus)]
    public sealed class Focus : CrystalArcherMagic
    {
        public override bool UpdateCombatTime => false;

        public Focus(PlayerObject player, UserMagic magic) : base(player, magic) { }

        public bool TryProc()
        {
            if (SEnvir.Random.Next(5) > Magic.Level) return false;
            Player.LevelMagic(Magic);
            return true;
        }
    }

    [MagicType(MagicType.Meditation)]
    public sealed class Meditation : CrystalArcherMagic
    {
        public override bool UpdateCombatTime => false;

        public Meditation(PlayerObject player, UserMagic magic) : base(player, magic) { }

        public override void AttackCompletePassive(MapObject target, List<MagicType> types)
        {
            if (target?.Node == null || target.Dead) return;

            BuffInfo concentration = Player.Buffs.FirstOrDefault(x => x.Type == BuffType.ArcherConcentration);
            int concentrationChance = concentration == null ? 0 : concentration.Extra + 1;

            if (SEnvir.Random.Next(10) < 8 - Magic.Level - concentrationChance) return;

            Player.CrystalArcherGatherElement(Magic.Level);
            Player.LevelMagic(Magic);
        }
    }

    [MagicType(MagicType.MentalState)]
    public sealed class MentalState : CrystalArcherMagic
    {
        public override bool UpdateCombatTime => false;

        public MentalState(PlayerObject player, UserMagic magic) : base(player, magic) { }

        public override MagicCast MagicCast(MapObject target, Point location, MirDirection direction)
        {
            Player.CrystalArcherMentalState = (byte)((Player.CrystalArcherMentalState + 1) % 3);
            Player.CrystalArcherMentalStateLevel = Magic.Level;

            return new MagicCast
            {
                Ob = Player,
                Cast = true,
            };
        }
    }

    [MagicType(MagicType.ArcherConcentration)]
    public sealed class ArcherConcentration : CrystalArcherMagic
    {
        public override bool UpdateCombatTime => false;

        public ArcherConcentration(PlayerObject player, UserMagic magic) : base(player, magic) { }

        public override MagicCast MagicCast(MapObject target, Point location, MirDirection direction)
        {
            int duration = 45 + 15 * Magic.Level;

            Player.BuffAdd(
                BuffType.ArcherConcentration,
                TimeSpan.FromSeconds(duration),
                new Stats(),
                true,
                false,
                TimeSpan.Zero,
                false,
                Magic.Level);

            Player.LevelMagic(Magic);
            return new MagicCast { Ob = Player };
        }
    }

    [MagicType(MagicType.BackStep)]
    public sealed class BackStep : CrystalArcherMagic
    {
        public BackStep(PlayerObject player, UserMagic magic) : base(player, magic) { }

        public override MagicCast MagicCast(MapObject target, Point location, MirDirection direction)
        {
            var response = new MagicCast { Ob = null, Return = true };

            int distance = Magic.Level == 0 ? 1 : Magic.Level;
            MirDirection reverse = Functions.ShiftDirection(direction, 4);
            int travelled = 0;

            for (int i = 0; i < distance; i++)
            {
                Cell cell = CurrentMap.GetCell(Functions.Move(Player.CurrentLocation, reverse));
                if (cell == null || cell.Movements != null) break;

                bool blocked = false;
                if (cell.Objects != null)
                {
                    foreach (MapObject ob in cell.Objects)
                    {
                        if (!ob.Blocking) continue;
                        blocked = true;
                        break;
                    }
                }
                if (blocked) break;

                Player.CurrentCell = cell.GetMovement(Player);
                Player.RemoveAllObjects();
                Player.AddAllObjects();
                travelled++;
            }

            if (travelled > 0)
            {
                Player.Broadcast(new S.ObjectDash
                {
                    ObjectID = Player.ObjectID,
                    Direction = direction,
                    Location = Player.CurrentLocation,
                    Distance = travelled,
                    Magic = Type,
                });
                Player.LevelMagic(Magic);
            }

            Player.CellTime = SEnvir.Now.AddMilliseconds(500);
            return response;
        }
    }

    [MagicType(MagicType.ElementalShot)]
    public sealed class ElementalShot : CrystalArcherMagic
    {
        public ElementalShot(PlayerObject player, UserMagic magic) : base(player, magic) { }

        public override MagicCast MagicCast(MapObject target, Point location, MirDirection direction)
        {
            var response = new MagicCast { Ob = target };

            if (!Player.GetMagic(MagicType.Meditation, out Meditation meditation))
            {
                response.Cast = false;
                return response;
            }

            if (Player.CrystalArcherOrbCount == 0)
            {
                Player.CrystalArcherSeedElement(meditation.Magic.Level);
                Player.LevelMagic(Magic);
                response.Cast = false;
                return response;
            }

            if (!CanCrystalProjectile(target))
            {
                response.Cast = false;
                return response;
            }

            int orbCount = Player.CrystalArcherOrbCount;
            int power = Magic.GetPower() + Player.GetMC() + 4 * orbCount;
            Point locked = target.CurrentLocation;

            response.Targets.Add(target.ObjectID);
            ActionList.Add(new DelayedAction(
                SEnvir.Now.AddMilliseconds(ProjectileDelay(target)),
                ActionType.DelayMagic,
                Type,
                target,
                locked,
                power,
                orbCount));

            return response;
        }

        public override void MagicComplete(params object[] data)
        {
            MapObject target = (MapObject)data[1];
            Point locked = (Point)data[2];
            int power = (int)data[3];
            int orbCount = (int)data[4];

            // Crystal destroys all elemental orbs even if the target moved.
            Player.CrystalArcherElementsLevel = 0;

            if (!TargetStillLocked(target, locked)) return;

            int damage = Player.MagicAttack(new List<MagicType> { Type }, target, true, null, power);
            if (damage <= 0) return;

            Player.LevelMagic(Magic);

            // ORIGINS rule: players never push players. Crystal's knockback
            // chance/distance is retained for monsters.
            if (target is not MonsterObject monster) return;

            int chance = 6 + Magic.Level * 3 + orbCount + Player.Level - monster.Level;
            if (SEnvir.Random.Next(20) >= chance) return;

            int push = 1 + Math.Max(0, Magic.Level - 1) + SEnvir.Random.Next(2);
            monster.Pushed(Player.Direction, push);
        }

        public override int ModifyPowerAdditionner(bool primary, int power, MapObject ob, Stats stats = null, int extra = 0)
        {
            return extra;
        }
    }

    [MagicType(MagicType.ElementalBarrier)]
    public sealed class ElementalBarrier : CrystalArcherMagic
    {
        public override bool UpdateCombatTime => false;

        public ElementalBarrier(PlayerObject player, UserMagic magic) : base(player, magic) { }

        public override MagicCast MagicCast(MapObject target, Point location, MirDirection direction)
        {
            var response = new MagicCast { Ob = Player };

            if (!Player.GetMagic(MagicType.Meditation, out Meditation meditation))
            {
                response.Cast = false;
                return response;
            }

            if (Player.CrystalArcherOrbCount == 0)
            {
                Player.CrystalArcherSeedElement(meditation.Magic.Level);
                Player.LevelMagic(Magic);
                return response;
            }

            int orbPower = Player.CrystalArcherOrbCount * 2;
            int duration = Magic.GetPower() + Player.GetMC() + orbPower;
            int reduction = (Magic.Level + 1) * 10;

            Player.CrystalArcherElementsLevel = 0;
            Player.BuffAdd(
                BuffType.CrystalElementalBarrier,
                TimeSpan.FromSeconds(Math.Max(1, duration)),
                new Stats { [Stat.CrystalArcherBarrierReductionPercent] = reduction },
                true,
                false,
                TimeSpan.Zero);

            Player.LevelMagic(Magic);
            return response;
        }
    }
}
