using Library;
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
    [MagicType(MagicType.Taunt)]
    public sealed class Taunt : MagicObject
    {
        protected override Element Element => Element.None;

        public Taunt(PlayerObject player, UserMagic magic) : base(player, magic) { }

        public override MagicCast MagicCast(MapObject target, Point location, MirDirection direction)
        {
            var response = new MagicCast { Ob = target };
            if (target is not MonsterObject monster || !Player.CanAttackTarget(monster))
            {
                response.Cast = false;
                response.Ob = null;
                return response;
            }

            response.Targets.Add(monster.ObjectID);
            ActionList.Add(new DelayedAction(
                SEnvir.Now.AddMilliseconds(500),
                ActionType.DelayMagic,
                Type,
                monster));
            return response;
        }

        public override void MagicComplete(params object[] data)
        {
            if (data[1] is not MonsterObject monster || monster.Node == null || monster.Dead || !Player.CanAttackTarget(monster)) return;

            // Jev source only resists the taunt when the monster is hidden and
            // higher level than the Monk. CanBeSeenBy is Zircon's visibility gate.
            if (!monster.CanBeSeenBy(Player) && Player.Level < monster.Level) return;

            monster.Target = Player;
            Player.LevelMagic(Magic);
        }
    }

    [MagicType(MagicType.TianLeiZhen)]
    public sealed class TianLeiZhen : MagicObject
    {
        protected override Element Element => Element.None;
        public override bool UpdateCombatTime => false;

        private bool _enabled;
        private DateTime _nextTick;

        public TianLeiZhen(PlayerObject player, UserMagic magic) : base(player, magic) { }

        public override void RefreshToggle()
        {
            Player.Enqueue(new S.MagicToggle { Magic = Type, CanUse = _enabled });
        }

        public override void Toggle(bool canUse)
        {
            _enabled = canUse;
            if (_enabled)
                _nextTick = SEnvir.Now.AddMilliseconds(1200);

            Player.Enqueue(new S.MagicToggle { Magic = Type, CanUse = _enabled });
        }

        public override void Process()
        {
            if (!_enabled || Player.Dead || SEnvir.Now < _nextTick) return;
            _nextTick = SEnvir.Now.AddMilliseconds(1200);

            // Source stops when cost >= current MP, then removes the infinite aura.
            if (Magic.Cost >= Player.CurrentMP)
            {
                _enabled = false;
                Player.Enqueue(new S.MagicToggle { Magic = Type, CanUse = false });
                return;
            }

            Player.ChangeMP(-Magic.Cost);
            int power = Magic.GetPower() + Player.GetSC();
            bool train = false;

            foreach (Cell cell in CurrentMap.GetCells(CurrentLocation, 0, 1))
            {
                if (cell.Objects == null) continue;

                foreach (MapObject ob in cell.Objects.ToList())
                {
                    if (ob?.Node == null || ob.Dead || !Player.CanAttackTarget(ob)) continue;

                    int damage = Player.MagicAttack(new List<MagicType> { Type }, ob, true, null, power);
                    if (damage > 0) train = true;
                }
            }

            if (train) Player.LevelMagic(Magic);
        }

        public override int ModifyPowerAdditionner(bool primary, int power, MapObject ob, Stats stats = null, int extra = 0)
        {
            return extra;
        }
    }

    [MagicType(MagicType.ShiBuYiSha)]
    public sealed class ShiBuYiSha : MagicObject
    {
        protected override Element Element => Element.None;

        public ShiBuYiSha(PlayerObject player, UserMagic magic) : base(player, magic) { }

        public override MagicCast MagicCast(MapObject target, Point location, MirDirection direction)
        {
            var response = new MagicCast { Ob = null };
            int power = Magic.GetPower() + Player.GetSC();

            ActionList.Add(new DelayedAction(
                SEnvir.Now.AddMilliseconds(500),
                ActionType.DelayMagic,
                Type,
                CurrentMap,
                location,
                power));

            response.Locations.Add(location);
            return response;
        }

        public override void MagicComplete(params object[] data)
        {
            Map map = (Map)data[1];
            Point location = (Point)data[2];
            int power = (int)data[3];

            if (map == null || map != CurrentMap) return;

            // Zircon has no Crystal NoTeleport flag; SkillDelay is its existing
            // map-level teleport restriction primitive used by Teleportation.
            if (map.Info.SkillDelay > 0) return;
            if (map.GetCell(location) == null || !Player.Teleport(map, location)) return;

            bool train = false;
            foreach (Cell cell in map.GetCells(location, 0, 2))
            {
                if (cell.Objects == null) continue;

                foreach (MapObject ob in cell.Objects.ToList())
                {
                    if (ob?.Node == null || ob.Dead || !Player.CanAttackTarget(ob)) continue;
                    int damage = Player.MagicAttack(new List<MagicType> { Type }, ob, true, null, power);
                    if (damage > 0) train = true;
                }
            }

            // Source levels after a successful teleport regardless of whether
            // the 5x5 found an enemy.
            Player.LevelMagic(Magic);
        }

        public override int ModifyPowerAdditionner(bool primary, int power, MapObject ob, Stats stats = null, int extra = 0)
        {
            return extra;
        }
    }

    [MagicType(MagicType.LuoHanZhen)]
    public sealed class LuoHanZhen : MagicObject
    {
        protected override Element Element => Element.None;
        public override bool UpdateCombatTime => false;

        public LuoHanZhen(PlayerObject player, UserMagic magic) : base(player, magic) { }

        public override MagicCast MagicCast(MapObject target, Point location, MirDirection direction)
        {
            var response = new MagicCast { Ob = Player };

            MonsterInfo info = SEnvir.MonsterInfoList.Binding.FirstOrDefault(x => x.MonsterName == "MonkClone");
            if (info == null)
            {
                response.Cast = false;
                return response;
            }

            foreach (MonsterObject clone in Player.Pets.Where(x => x.MonsterInfo == info && x.Node != null && !x.Dead).ToList())
                clone.SetHP(0);

            Point[] points =
            {
                new Point(CurrentLocation.X - 1, CurrentLocation.Y - 1),
                new Point(CurrentLocation.X - 1, CurrentLocation.Y + 1),
                new Point(CurrentLocation.X + 1, CurrentLocation.Y - 1),
                new Point(CurrentLocation.X + 1, CurrentLocation.Y + 1),
            };

            foreach (Point point in points)
            {
                MonsterObject clone = MonsterObject.GetMonster(info);
                if (clone == null) continue;

                clone.PetOwner = Player;
                clone.Direction = Player.Direction;
                clone.SummonLevel = Magic.Level * 2;
                clone.TameTime = SEnvir.Now.AddDays(365);
                Player.Pets.Add(clone);

                Cell cell = CurrentMap.GetCell(point);
                if (cell == null || !clone.Spawn(CurrentMap, point))
                {
                    Player.Pets.Remove(clone);
                    continue;
                }

                clone.SetHP(clone.Stats[Stat.Health]);
            }

            Player.LevelMagic(Magic);
            return response;
        }
    }
}
