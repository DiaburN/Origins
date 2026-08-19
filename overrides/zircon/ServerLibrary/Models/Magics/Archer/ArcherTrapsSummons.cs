using Library;
using Library.SystemModels;
using Server.DBModels;
using Server.Envir;
using System;
using System.Drawing;
using System.Linq;

namespace Server.Models.Magics
{
    [MagicType(MagicType.ExplosiveTrap)]
    public sealed class ExplosiveTrap : CrystalArcherMagic
    {
        public override bool UpdateCombatTime => false;

        public ExplosiveTrap(PlayerObject player, UserMagic magic) : base(player, magic) { }

        public override MagicCast MagicCast(MapObject target, Point location, MirDirection direction)
        {
            var response = new MagicCast { Ob = null };
            Point front = Functions.Move(CurrentLocation, direction);
            response.Locations.Add(front);

            int maxGroups = Magic.Level + 1;
            int groupId = -1;
            var used = Player.SpellList
                .Where(x => x.Effect == SpellEffect.CrystalExplosiveTrap && !x.CrystalTrapDetonated)
                .Select(x => x.CrystalTrapGroupId)
                .Distinct()
                .ToHashSet();

            if (used.Count >= maxGroups)
            {
                response.Cast = false;
                return response;
            }

            for (int i = 0; i < maxGroups; i++)
            {
                if (used.Contains(i)) continue;
                groupId = i;
                break;
            }

            if (groupId < 0)
            {
                response.Cast = false;
                return response;
            }

            int power = Magic.GetPower() + Player.GetMC();
            ActionList.Add(new DelayedAction(
                SEnvir.Now.AddMilliseconds(500),
                ActionType.DelayMagic,
                Type,
                CurrentMap,
                front,
                direction,
                power,
                groupId));

            return response;
        }

        public override void MagicComplete(params object[] data)
        {
            Map map = (Map)data[1];
            Point front = (Point)data[2];
            MirDirection direction = (MirDirection)data[3];
            int power = (int)data[4];
            int groupId = (int)data[5];
            if (map != CurrentMap) return;

            Point[] locations =
            {
                front,
                Functions.Move(front, Functions.ShiftDirection(direction, -2)),
                Functions.Move(front, Functions.ShiftDirection(direction, 2)),
            };

            bool spawned = false;
            for (int i = 0; i < locations.Length; i++)
            {
                Cell cell = map.GetCell(locations[i]);
                if (cell == null) continue;

                bool blockedByField = cell.Objects != null && cell.Objects.OfType<SpellObject>().Any(x =>
                    x.Effect == SpellEffect.FireWall || x.Effect == SpellEffect.CrystalExplosiveTrap);

                // Crystal refuses the cast when the front is occupied. Side pieces
                // are independently skipped if they overlap an existing field.
                if (blockedByField)
                {
                    if (i == 0) return;
                    continue;
                }

                int durationMs = Math.Max(1000, (10 + power / 2) * 1000);
                SpellObject trap = new SpellObject
                {
                    DisplayLocation = cell.Location,
                    Effect = SpellEffect.CrystalExplosiveTrap,
                    TickCount = Math.Max(1, durationMs / 500),
                    TickFrequency = TimeSpan.FromMilliseconds(500),
                    TickTime = SEnvir.Now,
                    Owner = Player,
                    Magic = Magic,
                    Power = power,
                    CrystalTrapGroupId = groupId,
                };

                if (trap.Spawn(map, cell.Location))
                    spawned = true;
            }

            if (spawned) Player.LevelMagic(Magic);
        }

        public override int ModifyPowerAdditionner(bool primary, int power, MapObject ob, Stats stats = null, int extra = 0) => extra;

        public override void MagicAttackSuccess(MapObject ob, int damageDealt)
        {
            // Crystal trains when the trap group is created, not on every detonation hit.
        }
    }

    public abstract class CrystalArcherSummon : CrystalArcherMagic
    {
        protected abstract string MonsterName { get; }
        protected abstract int BaseLifeMs { get; }
        protected abstract int LifePerLevelMs { get; }

        protected CrystalArcherSummon(PlayerObject player, UserMagic magic) : base(player, magic) { }

        public override bool UpdateCombatTime => false;

        public override MagicCast MagicCast(MapObject target, Point location, MirDirection direction)
        {
            var response = new MagicCast { Ob = target };

            if (target != null && Player.CanAttackTarget(target))
                location = target.CurrentLocation;

            if (CurrentMap.GetCell(location) == null || (Player.CrystalArcherMentalState != 1 && !CurrentMap.LineOfSight(CurrentLocation, location)))
            {
                response.Cast = false;
                return response;
            }

            MonsterInfo info = SEnvir.MonsterInfoList.Binding.FirstOrDefault(x => x.MonsterName == MonsterName);
            if (info == null)
            {
                response.Cast = false;
                return response;
            }

            int delay = 500 + RangeDistance(location) * 50;
            ActionList.Add(new DelayedAction(
                SEnvir.Now.AddMilliseconds(delay),
                ActionType.DelayMagic,
                Type,
                info,
                location,
                target));

            response.Locations.Add(location);
            return response;
        }

        public override void MagicComplete(params object[] data)
        {
            MonsterInfo info = (MonsterInfo)data[1];
            Point location = (Point)data[2];
            MapObject target = (MapObject)data[3];
            if (info == null) return;

            MonsterObject existing = Player.Pets.FirstOrDefault(x => x.MonsterInfo == info && x.Node != null && !x.Dead);
            if (existing != null)
            {
                existing.Target = target;
                existing.PetRecall();
                return;
            }

            if (Player.Pets.Count(x => x.Race == ObjectType.Monster && !x.Dead) >= 2) return;

            // Crystal schedules the actual summon spawn another 500 ms after
            // the projectile/cast arrival.
            ActionList.Add(new DelayedAction(
                SEnvir.Now.AddMilliseconds(500),
                ActionType.DelayMagic,
                Type,
                true,
                info,
                CurrentMap,
                location,
                target));
        }

        protected void SpawnSummon(params object[] data)
        {
            MonsterInfo info = (MonsterInfo)data[2];
            Map map = (Map)data[3];
            Point location = (Point)data[4];
            MapObject target = (MapObject)data[5];
            if (map == null || info == null || Player.Pets.Count(x => x.Race == ObjectType.Monster && !x.Dead) >= 2) return;

            MonsterObject monster = MonsterObject.GetMonster(info);
            if (monster == null) return;

            monster.PetOwner = Player;
            monster.Target = target;
            monster.Direction = Player.Direction;
            monster.SummonLevel = Magic.Level * 2;
            monster.TameTime = SEnvir.Now.AddDays(365);
            monster.CrystalArcherExpireTime = SEnvir.Now.AddMilliseconds(BaseLifeMs + LifePerLevelMs * Magic.Level);
            Player.Pets.Add(monster);

            Cell cell = map.GetCell(location);
            if (cell == null || cell.Movements != null || !monster.Spawn(map, location))
                monster.Spawn(CurrentMap, CurrentLocation);

            monster.SetHP(monster.Stats[Stat.Health]);
            Player.LevelMagic(Magic);
        }
    }

    [MagicType(MagicType.SummonVampire)]
    public sealed class SummonVampire : CrystalArcherSummon
    {
        protected override string MonsterName => "VampireSpider";
        protected override int BaseLifeMs => 15000;
        protected override int LifePerLevelMs => 1500;

        public SummonVampire(PlayerObject player, UserMagic magic) : base(player, magic) { }

        public override void MagicComplete(params object[] data)
        {
            if (data.Length > 1 && data[1] is bool spawn && spawn) { SpawnSummon(data); return; }
            base.MagicComplete(data);
        }
    }

    [MagicType(MagicType.SummonToad)]
    public sealed class SummonToad : CrystalArcherSummon
    {
        protected override string MonsterName => "SpittingToad";
        protected override int BaseLifeMs => 25000;
        protected override int LifePerLevelMs => 2000;

        public SummonToad(PlayerObject player, UserMagic magic) : base(player, magic) { }

        public override void MagicComplete(params object[] data)
        {
            if (data.Length > 1 && data[1] is bool spawn && spawn) { SpawnSummon(data); return; }
            base.MagicComplete(data);
        }
    }

    [MagicType(MagicType.SummonSnakes)]
    public sealed class SummonSnakes : CrystalArcherSummon
    {
        protected override string MonsterName => "SnakeTotem";
        protected override int BaseLifeMs => 20000;
        protected override int LifePerLevelMs => 1500;

        public SummonSnakes(PlayerObject player, UserMagic magic) : base(player, magic) { }

        public override void MagicComplete(params object[] data)
        {
            if (data.Length > 1 && data[1] is bool spawn && spawn) { SpawnSummon(data); return; }
            base.MagicComplete(data);
        }
    }

    [MagicType(MagicType.Stonetrap)]
    public sealed class Stonetrap : CrystalArcherMagic
    {
        public override bool UpdateCombatTime => false;

        public Stonetrap(PlayerObject player, UserMagic magic) : base(player, magic) { }

        public override MagicCast MagicCast(MapObject target, Point location, MirDirection direction)
        {
            var response = new MagicCast { Ob = null };
            if (CurrentMap.GetCell(location) == null || (Player.CrystalArcherMentalState != 1 && !CurrentMap.LineOfSight(CurrentLocation, location)))
            {
                response.Cast = false;
                return response;
            }

            MonsterInfo info = SEnvir.MonsterInfoList.Binding.FirstOrDefault(x => x.MonsterName == "StoneTrap");
            if (info == null || Player.Pets.Any(x => x.MonsterInfo == info && x.Node != null && !x.Dead))
            {
                response.Cast = false;
                return response;
            }

            int durationMs = (Magic.Level * 5 + 10) * 1000;
            int delay = 500 + RangeDistance(location) * 50;
            ActionList.Add(new DelayedAction(
                SEnvir.Now.AddMilliseconds(delay + 500),
                ActionType.DelayMagic,
                Type,
                CurrentMap,
                location,
                info,
                durationMs));

            response.Locations.Add(location);
            return response;
        }

        public override void MagicComplete(params object[] data)
        {
            Map map = (Map)data[1];
            Point location = (Point)data[2];
            MonsterInfo info = (MonsterInfo)data[3];
            int durationMs = (int)data[4];
            if (map == null || info == null || Player.Pets.Count(x => x.Race == ObjectType.Monster && !x.Dead) >= Magic.Level + 1) return;

            MonsterObject monster = MonsterObject.GetMonster(info);
            if (monster == null) return;

            monster.PetOwner = Player;
            monster.Direction = Player.Direction;
            monster.SummonLevel = Magic.Level * 2;
            monster.TameTime = SEnvir.Now.AddDays(365);
            monster.CrystalArcherExpireTime = SEnvir.Now.AddMilliseconds(durationMs);
            Player.Pets.Add(monster);

            Cell cell = map.GetCell(location);
            if (cell == null || cell.Movements != null || !monster.Spawn(map, location))
            {
                Player.Pets.Remove(monster);
                return;
            }

            monster.SetHP(monster.Stats[Stat.Health]);
            Player.LevelMagic(Magic);
        }
    }
}
