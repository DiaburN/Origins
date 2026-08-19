using Library;
using Server.DBModels;
using Server.Envir;
using System;
using System.Collections.Generic;
using System.Drawing;

namespace Server.Models.Magics
{
    [MagicType(MagicType.JiBenGunFa)]
    public sealed class JiBenGunFa : MagicObject
    {
        protected override Element Element => Element.None;
        public override bool AttackSkill => true;

        public JiBenGunFa(PlayerObject player, UserMagic magic) : base(player, magic) { }

        public override AttackCast AttackCast(MagicType attackType)
        {
            var response = new AttackCast();
            response.Magics.Add(Type);
            return response;
        }

        public override Stats GetPassiveStats()
        {
            return new Stats
            {
                [Stat.Accuracy] = (Magic.Level + 1) * 2,
                [Stat.MaxAC] = Magic.Level + 1,
            };
        }

        public override int ModifyPowerAdditionner(bool primary, int power, MapObject ob, Stats stats = null, int extra = 0)
        {
            return power;
        }
    }

    [MagicType(MagicType.LuoHanGunFa)]
    public sealed class LuoHanGunFa : MagicObject
    {
        protected override Element Element => Element.None;
        public override bool AttackSkill => true;

        private int _scPower;

        public LuoHanGunFa(PlayerObject player, UserMagic magic) : base(player, magic) { }

        public override AttackCast AttackCast(MagicType attackType)
        {
            var response = new AttackCast();
            if (attackType != Type) return response;
            if (Magic.Cost > Player.CurrentMP) return response;

            Player.ChangeMP(-Magic.Cost);
            _scPower = Magic.GetPower() + Player.GetSC();
            response.Cast = true;
            response.Magics.Add(Type);
            return response;
        }

        public override int ModifyPowerAdditionner(bool primary, int power, MapObject ob, Stats stats = null, int extra = 0)
        {
            return _scPower;
        }

        public override void SecondaryAttackLocation(List<MagicType> magics)
        {
            Point distance2 = Functions.Move(Player.CurrentLocation, Player.Direction, 2);
            Point distance4 = Functions.Move(Player.CurrentLocation, Player.Direction, 4);

            Player.AttackLocation(distance2, magics, false);
            Player.AttackLocation(distance4, magics, false);
        }
    }

    [MagicType(MagicType.DaMoGunFa)]
    public sealed class DaMoGunFa : MagicObject
    {
        protected override Element Element => Element.None;
        public override bool AttackSkill => true;
        public override bool IgnoreAccuracy => true;

        private bool _armed;
        private DateTime _nextArmTime;
        private int _scPower;

        public DaMoGunFa(PlayerObject player, UserMagic magic) : base(player, magic) { }

        public override void RefreshToggle()
        {
            Player.Enqueue(new Library.Network.ServerPackets.MagicToggle { Magic = Type, CanUse = _armed });
        }

        public override void Toggle(bool canUse)
        {
            if (!canUse)
            {
                _armed = false;
                Player.Enqueue(new Library.Network.ServerPackets.MagicToggle { Magic = Type, CanUse = false });
                return;
            }

            if (_armed || SEnvir.Now < _nextArmTime) return;
            if (Magic.Cost >= Player.CurrentMP) return;

            Player.ChangeMP(-Magic.Cost);
            _armed = true;
            _nextArmTime = SEnvir.Now.AddSeconds(9);
            Player.Enqueue(new Library.Network.ServerPackets.MagicToggle { Magic = Type, CanUse = true });
        }

        public override AttackCast AttackCast(MagicType attackType)
        {
            var response = new AttackCast();
            if (attackType != Type || !_armed) return response;

            _scPower = Magic.GetPower() + Player.GetSC();
            response.Cast = true;
            response.Magics.Add(Type);
            return response;
        }

        public override int ModifyPowerAdditionner(bool primary, int power, MapObject ob, Stats stats = null, int extra = 0)
        {
            return _scPower;
        }

        public override void AttackComplete(MapObject target)
        {
            _armed = false;
            Player.Enqueue(new Library.Network.ServerPackets.MagicToggle { Magic = Type, CanUse = false });
            Player.LevelMagic(Magic);
        }
    }

    [MagicType(MagicType.JinGangGunFa)]
    public sealed class JinGangGunFa : MagicObject
    {
        protected override Element Element => Element.None;

        public JinGangGunFa(PlayerObject player, UserMagic magic) : base(player, magic) { }

        public override MagicCast MagicCast(MapObject target, Point location, MirDirection direction)
        {
            var response = new MagicCast { Ob = null };
            int power = Magic.GetPower() + Player.GetSC();

            ActionList.Add(new DelayedAction(
                SEnvir.Now.AddMilliseconds(500),
                ActionType.DelayMagic,
                Type,
                CurrentMap,
                CurrentLocation,
                direction,
                power));

            return response;
        }

        public override void MagicComplete(params object[] data)
        {
            Map map = (Map)data[1];
            Point origin = (Point)data[2];
            MirDirection original = (MirDirection)data[3];
            int power = (int)data[4];
            if (map != CurrentMap) return;

            if (SEnvir.Random.Next(100) <= 1 + Player.Stats[Stat.Luck])
                power += power;

            MirDirection direction = Functions.ShiftDirection(original, -1);
            bool train = false;

            for (int i = 0; i < 4; i++)
            {
                Point hit = Functions.Move(origin, direction);
                Cell cell = map.GetCell(hit);
                if (cell?.Objects != null)
                {
                    foreach (MapObject ob in new List<MapObject>(cell.Objects))
                    {
                        if (ob?.Node == null || ob.Dead || !Player.CanAttackTarget(ob)) continue;

                        int damage = 0;
                        if (direction == original)
                        {
                            // Crystal DefenceType.None: full skill power reaches Attacked.
                            damage = ob.Attacked(Player, power, Element.None, true, false, false, true);
                        }
                        else
                        {
                            // Crystal DefenceType.MACAgility: first perform the agility
                            // gate, then subtract a Zircon MR roll before Attacked.
                            int accuracy = Math.Max(1, Player.Stats[Stat.Accuracy]);
                            int agility = Math.Max(0, ob.Stats[Stat.Agility]);
                            if (SEnvir.Random.Next(accuracy + agility + 1) < agility)
                                break;

                            int resolved = power - ob.GetMR();
                            if (resolved <= 0)
                            {
                                ob.Blocked();
                                break;
                            }

                            damage = ob.Attacked(Player, resolved, Element.None, true, false, false, true);
                        }

                        if (damage > 0) train = true;
                        break;
                    }
                }

                direction = Functions.ShiftDirection(direction, 1);
            }

            if (train) Player.LevelMagic(Magic);
        }
    }

    [MagicType(MagicType.XiangLongGunFa)]
    public sealed class XiangLongGunFa : MagicObject
    {
        protected override Element Element => Element.None;

        public XiangLongGunFa(PlayerObject player, UserMagic magic) : base(player, magic) { }

        public override MagicCast MagicCast(MapObject target, Point location, MirDirection direction)
        {
            var response = new MagicCast { Ob = null };
            int power = Magic.GetPower() + Player.GetSC();
            Map map = CurrentMap;
            Point origin = CurrentLocation;

            ActionList.Add(new DelayedAction(
                SEnvir.Now.AddMilliseconds(500),
                ActionType.DelayMagic,
                Type,
                map,
                origin,
                direction,
                power));

            Point landing = Functions.Move(origin, direction, 2);
            Cell landingCell = map.GetCell(landing);
            if (landingCell == null) return response;

            bool blocked = landingCell.Movements != null;
            if (!blocked && landingCell.Objects != null)
            {
                foreach (MapObject ob in landingCell.Objects)
                {
                    if (!ob.Blocking) continue;
                    blocked = true;
                    break;
                }
            }

            if (!blocked)
                Player.Teleport(map, landing);

            return response;
        }

        public override void MagicComplete(params object[] data)
        {
            Map map = (Map)data[1];
            Point origin = (Point)data[2];
            MirDirection direction = (MirDirection)data[3];
            int power = (int)data[4];
            if (map == null) return;

            Point hit = Functions.Move(origin, direction);
            Cell cell = map.GetCell(hit);
            if (cell?.Objects == null) return;

            bool train = false;
            foreach (MapObject ob in new List<MapObject>(cell.Objects))
            {
                if (ob?.Node == null || ob.Dead || !Player.CanAttackTarget(ob)) continue;

                // Crystal DefenceType.AC: subtract AC but do not apply agility.
                int resolved = power - ob.GetAC();
                if (resolved <= 0)
                {
                    ob.Blocked();
                    break;
                }

                int damage = ob.Attacked(Player, resolved, Element.None, true, false, false, true);
                if (damage > 0) train = true;
                break;
            }

            if (train) Player.LevelMagic(Magic);
        }
    }
}
