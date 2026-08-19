using Library;
using Library.Network.ServerPackets;
using Library.SystemModels;
using Server.DBModels;
using Server.Envir;
using System;
using System.Collections.Generic;
using System.Drawing;
using System.Linq;
using S = Library.Network.ServerPackets;

namespace Server.Models.Magics
{
    public abstract class CrystalMonkMagic : MagicObject
    {
        protected override Element Element => Element.None;

        protected CrystalMonkMagic(PlayerObject player, UserMagic magic) : base(player, magic) { }

        protected int SCPower()
        {
            // Crystal UserMagic.GetDamage(GetAttackPower(MinSC, MaxSC)).
            // Zircon's imported Magic.GetPower carries the spell power component.
            return Player.GetSC() + Magic.GetPower();
        }
    }

    [MagicType(MagicType.JiBenGunFa)]
    public sealed class JiBenGunFa : CrystalMonkMagic
    {
        public override bool UpdateCombatTime => false;

        public JiBenGunFa(PlayerObject player, UserMagic magic) : base(player, magic) { }

        public override Stats GetPassiveStats()
        {
            // Crystal-Monk RefreshStats:
            // Accuracy += magic.Level * 2 + 2
            // MaxAC    += magic.Level + 1
            return new Stats
            {
                [Stat.Accuracy] = Magic.Level * 2 + 2,
                [Stat.MaxAC] = Magic.Level + 1,
            };
        }

        public override void AttackCompletePassive(MapObject target, List<MagicType> types)
        {
            // Crystal levels JiBenGunFa through successful normal attacks.
            if (target?.Node != null && Player.CanAttackTarget(target))
                Player.LevelMagic(Magic);
        }
    }

    [MagicType(MagicType.LuoHanGunFa)]
    public sealed class LuoHanGunFa : CrystalMonkMagic
    {
        public override bool AttackSkill => true;

        private bool Enabled;
        private bool LevelledThisSwing;

        public LuoHanGunFa(PlayerObject player, UserMagic magic) : base(player, magic) { }

        public override void RefreshToggle()
        {
            if (Enabled)
                Player.Enqueue(new S.MagicToggle { Magic = Type, CanUse = true });
        }

        public override void Toggle(bool canUse)
        {
            Enabled = canUse;
            Player.Enqueue(new S.MagicToggle { Magic = Type, CanUse = Enabled });
        }

        public override AttackCast AttackCast(MagicType attackType)
        {
            var response = new AttackCast();

            if (attackType != Type || !Enabled || !CheckCost())
                return response;

            MagicConsume();
            LevelledThisSwing = false;

            response.Cast = true;
            response.Magics.Add(Type);
            return response;
        }

        public override void SecondaryAttackLocation(List<MagicType> magics)
        {
            // The Jev source mutates the target point inside j=1..2. Starting
            // from the normal forward hit this produces additional cells at
            // distances 2 and 4 from the caster. Preserve that source quirk.
            Point second = Functions.Move(CurrentLocation, Direction, 2);
            Point fourth = Functions.Move(CurrentLocation, Direction, 4);

            Player.AttackLocation(second, magics, false);
            Player.AttackLocation(fourth, magics, false);
        }

        public override int ModifyPowerAdditionner(bool primary, int power, MapObject ob, Stats stats = null, int extra = 0)
        {
            // Unlike normal warrior attacks, Crystal-Monk explicitly rolls SC.
            return extra != 0 ? extra : SCPower();
        }

        public override void AttackComplete(MapObject target)
        {
            if (LevelledThisSwing) return;
            LevelledThisSwing = true;
            Player.LevelMagic(Magic);
        }
    }

    [MagicType(MagicType.DaMoGunFa)]
    public sealed class DaMoGunFa : CrystalMonkMagic
    {
        public override bool AttackSkill => true;
        public override bool IgnoreAccuracy => true; // Crystal uses DefenceType.AC for the charged hit.

        private bool Armed;
        private DateTime ArmedUntil;

        public DaMoGunFa(PlayerObject player, UserMagic magic) : base(player, magic) { }

        public override void Process()
        {
            if (!Armed || SEnvir.Now < ArmedUntil) return;
            Armed = false;
            Player.Enqueue(new S.MagicToggle { Magic = Type, CanUse = false });
        }

        public override void RefreshToggle()
        {
            if (Armed)
                Player.Enqueue(new S.MagicToggle { Magic = Type, CanUse = true });
        }

        public override void Toggle(bool canUse)
        {
            if (!canUse || Armed || SEnvir.Now < ArmedUntil || Player.Dead) return;

            // Jev uses `if (cost >= MP) return`, so one MP must remain after arming.
            if (!Player.Superman && Magic.Cost >= Player.CurrentMP) return;

            MagicConsume();
            Armed = true;
            ArmedUntil = SEnvir.Now.AddSeconds(9);
            MagicCooldown(Magic, 9000);

            Player.Enqueue(new S.MagicToggle { Magic = Type, CanUse = true });
        }

        public override AttackCast AttackCast(MagicType attackType)
        {
            var response = new AttackCast();
            if (attackType != Type || !Armed) return response;

            Armed = false;
            Player.Enqueue(new S.MagicToggle { Magic = Type, CanUse = false });

            response.Cast = true;
            response.Magics.Add(Type);
            return response;
        }

        public override int ModifyPowerAdditionner(bool primary, int power, MapObject ob, Stats stats = null, int extra = 0)
        {
            return extra != 0 ? extra : SCPower();
        }
    }

    [MagicType(MagicType.JinGangGunFa)]
    public sealed class JinGangGunFa : CrystalMonkMagic
    {
        // The frontal sector is DefenceType.None in Crystal-Monk. When routed
        // through Zircon's physical attack primitive this removes both dodge
        // and physical defence for that one sector.
        public override bool IgnoreAccuracy => true;
        public override bool IgnorePhysicalDefense => true;

        public JinGangGunFa(PlayerObject player, UserMagic magic) : base(player, magic) { }

        public override MagicCast MagicCast(MapObject target, Point location, MirDirection direction)
        {
            var response = new MagicCast { Ob = null };
            Point origin = CurrentLocation;
            int power = SCPower();

            ActionList.Add(new DelayedAction(
                SEnvir.Now.AddMilliseconds(500),
                ActionType.DelayMagic,
                Type,
                CurrentMap,
                origin,
                direction,
                power));

            MirDirection sweep = Functions.ShiftDirection(direction, -1);
            for (int i = 0; i < 4; i++)
            {
                response.Locations.Add(Functions.Move(origin, sweep));
                sweep = Functions.ShiftDirection(sweep, 1);
            }

            return response;
        }

        public override void MagicComplete(params object[] data)
        {
            Map map = (Map)data[1];
            Point origin = (Point)data[2];
            MirDirection direction = (MirDirection)data[3];
            int power = (int)data[4];
            if (map == null || Player.CurrentMap != map) return;

            // Crystal-Monk crit: Random.Next(0,100) <= 1 + Luck.
            if (SEnvir.Random.Next(100) <= 1 + Player.Stats[Stat.Luck])
                power *= 2;

            bool trained = false;
            MirDirection sweep = Functions.ShiftDirection(direction, -1);

            for (int i = 0; i < 4; i++)
            {
                Point hitPoint = Functions.Move(origin, sweep);
                Cell cell = map.GetCell(hitPoint);
                MapObject ob = cell?.Objects?.FirstOrDefault(x =>
                    (x.Race == ObjectType.Player || x.Race == ObjectType.Monster) &&
                    Player.CanAttackTarget(x));

                if (ob != null)
                {
                    if (sweep == direction)
                    {
                        // Source front cell: DefenceType.None.
                        Player.Attack(ob, new List<MagicType> { Type }, true, power);
                        trained = true;
                    }
                    else
                    {
                        // Source side sectors: DefenceType.MACAgility. Zircon has
                        // no combined DefenceType, so preserve the agility gate
                        // explicitly and route surviving hits through MagicAttack.
                        int agility = Math.Max(1, ob.Stats[Stat.Agility]);
                        int accuracy = Math.Max(1, Player.Stats[Stat.Accuracy]);
                        if (SEnvir.Random.Next(agility) <= accuracy)
                        {
                            if (Player.MagicAttack(new List<MagicType> { Type }, ob, true, null, power) > 0)
                                trained = true;
                        }
                        else
                        {
                            ob.Dodged();
                        }
                    }
                }

                sweep = Functions.ShiftDirection(sweep, 1);
            }

            if (trained)
                Player.LevelMagic(Magic);
        }

        public override int ModifyPowerAdditionner(bool primary, int power, MapObject ob, Stats stats = null, int extra = 0)
        {
            return extra != 0 ? extra : SCPower();
        }

        public override void AttackComplete(MapObject target)
        {
            // MagicComplete trains once for the four-sector cast.
        }

        public override void MagicAttackSuccess(MapObject ob, int damageDealt)
        {
            // MagicComplete trains once for the four-sector cast.
        }
    }

    [MagicType(MagicType.XiangLongGunFa)]
    public sealed class XiangLongGunFa : CrystalMonkMagic
    {
        // Jev resolves the one-cell thrust against AC only, without agility.
        public override bool IgnoreAccuracy => true;

        public XiangLongGunFa(PlayerObject player, UserMagic magic) : base(player, magic) { }

        public override MagicCast MagicCast(MapObject target, Point location, MirDirection direction)
        {
            var response = new MagicCast { Ob = null };
            Point origin = CurrentLocation;
            int power = SCPower();

            Point hitPoint = Functions.Move(origin, direction);
            response.Locations.Add(hitPoint);

            ActionList.Add(new DelayedAction(
                SEnvir.Now.AddMilliseconds(500),
                ActionType.DelayMagic,
                Type,
                CurrentMap,
                hitPoint,
                power));

            return response;
        }

        public override void MagicComplete(params object[] data)
        {
            Map map = (Map)data[1];
            Point hitPoint = (Point)data[2];
            int power = (int)data[3];
            if (map == null || Player.CurrentMap != map) return;

            Cell cell = map.GetCell(hitPoint);
            MapObject ob = cell?.Objects?.FirstOrDefault(x =>
                (x.Race == ObjectType.Player || x.Race == ObjectType.Monster) &&
                Player.CanAttackTarget(x));

            if (ob == null) return;
            Player.Attack(ob, new List<MagicType> { Type }, true, power);
        }

        public override int ModifyPowerAdditionner(bool primary, int power, MapObject ob, Stats stats = null, int extra = 0)
        {
            return extra != 0 ? extra : SCPower();
        }
    }

    [MagicType(MagicType.Taunt)]
    public sealed class Taunt : CrystalMonkMagic
    {
        public Taunt(PlayerObject player, UserMagic magic) : base(player, magic) { }

        public override MagicCast MagicCast(MapObject target, Point location, MirDirection direction)
        {
            var response = new MagicCast { Ob = target };

            if (target == null || target.Race != ObjectType.Monster || !Player.CanAttackTarget(target))
            {
                response.Cast = false;
                response.Ob = null;
                return response;
            }

            response.Targets.Add(target.ObjectID);
            ActionList.Add(new DelayedAction(
                SEnvir.Now.AddMilliseconds(500),
                ActionType.DelayMagic,
                Type,
                target));

            return response;
        }

        public override void MagicComplete(params object[] data)
        {
            MonsterObject target = data[1] as MonsterObject;
            if (target?.Node == null || target.Dead || target.CurrentMap != CurrentMap || !Player.CanAttackTarget(target)) return;

            // Crystal refuses to reveal/taunt a hidden higher-level monster.
            if (!target.Visible && Player.Level < target.Level) return;

            target.Target = Player;
            Player.LevelMagic(Magic);
        }
    }

    [MagicType(MagicType.TianLeiZhen)]
    public sealed class TianLeiZhen : CrystalMonkMagic
    {
        public override bool UpdateCombatTime => false;

        private bool Enabled;
        private DateTime NextTick;

        public TianLeiZhen(PlayerObject player, UserMagic magic) : base(player, magic) { }

        public override void RefreshToggle()
        {
            if (Enabled)
                Player.Enqueue(new S.MagicToggle { Magic = Type, CanUse = true });
        }

        public override void Toggle(bool canUse)
        {
            Enabled = canUse;
            if (Enabled)
                NextTick = SEnvir.Now; // BuffV2 TickTime starts at zero in Jev.

            Player.Enqueue(new S.MagicToggle { Magic = Type, CanUse = Enabled });
        }

        public override void Process()
        {
            if (!Enabled || Player.Dead || SEnvir.Now < NextTick) return;
            NextTick = SEnvir.Now.AddMilliseconds(1200);

            // Jev leaves the toggle enabled when MP is insufficient; it simply
            // skips the tick until enough MP is available again.
            if (!CheckCost()) return;

            MagicConsume();
            int power = SCPower();

            foreach (Cell cell in CurrentMap.GetCells(CurrentLocation, 0, 1))
            {
                if (cell?.Objects == null) continue;

                foreach (MapObject ob in cell.Objects.ToList())
                {
                    if (ob == Player || ob.Dead || !Player.CanAttackTarget(ob)) continue;
                    Player.MagicAttack(new List<MagicType> { Type }, ob, true, null, power);
                }
            }

            // Crystal-Monk trains DamageHalo once every paid 1.2 s tick,
            // regardless of whether an enemy occupied the 3x3 area.
            Player.LevelMagic(Magic);
        }

        public override int ModifyPowerAdditionner(bool primary, int power, MapObject ob, Stats stats = null, int extra = 0)
        {
            return extra != 0 ? extra : SCPower();
        }

        public override void MagicAttackSuccess(MapObject ob, int damageDealt)
        {
            // Process() owns the once-per-tick training.
        }
    }

    [MagicType(MagicType.ShiBuYiSha)]
    public sealed class ShiBuYiSha : CrystalMonkMagic
    {
        public ShiBuYiSha(PlayerObject player, UserMagic magic) : base(player, magic) { }

        public override MagicCast MagicCast(MapObject target, Point location, MirDirection direction)
        {
            var response = new MagicCast { Ob = null };
            response.Locations.Add(location);

            int power = SCPower();
            ActionList.Add(new DelayedAction(
                SEnvir.Now.AddMilliseconds(500),
                ActionType.DelayMagic,
                Type,
                CurrentMap,
                location,
                power));

            return response;
        }

        public override void MagicComplete(params object[] data)
        {
            Map map = (Map)data[1];
            Point location = (Point)data[2];
            int power = (int)data[3];

            if (map == null || Player.CurrentMap != map || map.Info.NoTeleport || map.GetCell(location) == null) return;
            if (!Player.Teleport(map, location, false)) return;

            bool trained = false;
            foreach (Cell cell in map.GetCells(location, 0, 2))
            {
                if (cell?.Objects == null) continue;

                foreach (MapObject ob in cell.Objects.ToList())
                {
                    if (ob == Player || ob.Dead || !Player.CanAttackTarget(ob)) continue;
                    if (Player.MagicAttack(new List<MagicType> { Type }, ob, true, null, power) > 0)
                        trained = true;
                }
            }

            // The source only trains through successful offensive resolution;
            // teleporting into an empty area is not treated as a combat hit.
            if (trained)
                Player.LevelMagic(Magic);
        }

        public override int ModifyPowerAdditionner(bool primary, int power, MapObject ob, Stats stats = null, int extra = 0)
        {
            return extra != 0 ? extra : SCPower();
        }

        public override void MagicAttackSuccess(MapObject ob, int damageDealt)
        {
            // MagicComplete owns once-per-cast training.
        }
    }

    [MagicType(MagicType.LuoHanZhen)]
    public sealed class LuoHanZhen : CrystalMonkMagic
    {
        private const string MonkCloneName = "MonkClone";

        public override bool UpdateCombatTime => false;

        public LuoHanZhen(PlayerObject player, UserMagic magic) : base(player, magic) { }

        public override MagicCast MagicCast(MapObject target, Point location, MirDirection direction)
        {
            var response = new MagicCast { Ob = null };

            MonsterInfo info = SEnvir.MonsterInfoList.Binding.FirstOrDefault(x => x.MonsterName == MonkCloneName);
            if (info == null)
            {
                response.Cast = false;
                return response;
            }

            // Crystal-Monk kills all existing MonkClone pets before rebuilding
            // the four diagonal formation.
            foreach (MonsterObject old in Player.Pets.Where(x => x.MonsterInfo == info && x.Node != null && !x.Dead).ToList())
                old.Die();

            Point[] positions =
            {
                new Point(CurrentLocation.X - 1, CurrentLocation.Y - 1),
                new Point(CurrentLocation.X - 1, CurrentLocation.Y + 1),
                new Point(CurrentLocation.X + 1, CurrentLocation.Y - 1),
                new Point(CurrentLocation.X + 1, CurrentLocation.Y + 1),
            };

            bool spawned = false;
            foreach (Point point in positions)
            {
                MonsterObject clone = MonsterObject.GetMonster(info);
                if (clone == null) continue;

                clone.PetOwner = Player;
                clone.Direction = Player.Direction;
                clone.TameTime = SEnvir.Now.AddDays(365);

                Cell cell = CurrentMap.GetCell(point);
                if (cell == null || !clone.Spawn(CurrentMap, point))
                    continue;

                Player.Pets.Add(clone);
                clone.SetHP(clone.Stats[Stat.Health]);
                response.Locations.Add(point);
                spawned = true;
            }

            if (spawned)
                Player.LevelMagic(Magic);

            return response;
        }
    }
}
