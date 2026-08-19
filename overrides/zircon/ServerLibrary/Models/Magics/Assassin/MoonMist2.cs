using Library;
using Server.DBModels;
using Server.Envir;
using System;
using System.Drawing;

namespace Server.Models.Magics
{
    [MagicType(MagicType.MoonMist2)]
    public sealed class MoonMist2 : MagicObject
    {
        protected override Element Element => Element.None;
        public override bool UpdateCombatTime => false;
        public override bool AttackSkill => true;

        private bool pendingNextAttackStun;

        public MoonMist2(PlayerObject player, UserMagic magic) : base(player, magic) { }

        public override MagicCast MagicCast(MapObject target, Point location, MirDirection direction)
        {
            var response = new MagicCast { Ob = Player };

            if (Player.Buffs.Exists(x => x.Type == BuffType.MoonMist))
            {
                response.Cast = false;
                return response;
            }

            response.Targets.Add(Player.ObjectID);

            Player.BuffAdd(
                BuffType.MoonMist,
                TimeSpan.FromSeconds(Magic.Level * 3 + 15),
                new Stats(),
                true,
                false,
                TimeSpan.Zero,
                false,
                1);

            int power = Magic.GetPower() + Player.GetDC();
            ActionList.Add(new DelayedAction(
                SEnvir.Now.AddMilliseconds(2000),
                ActionType.DelayMagic,
                Type,
                CurrentMap,
                CurrentLocation,
                power));

            Player.LevelMagic(Magic);
            return response;
        }

        public override void MagicComplete(params object[] data)
        {
            Map map = (Map)data[1];
            Point location = (Point)data[2];
            int power = (int)data[3];
            if (map != CurrentMap) return;

            foreach (Cell cell in map.GetCells(location, 0, 2))
            {
                if (cell?.Objects == null) continue;

                for (int i = cell.Objects.Count - 1; i >= 0; i--)
                {
                    MapObject ob = cell.Objects[i];
                    if (ob?.Node == null || !Player.CanAttackTarget(ob)) continue;

                    int damage = power - ob.GetAC();
                    if (damage > 0)
                        ob.Attacked(Player, damage, Element.None, true, false, false, true);
                    else
                        ob.Blocked();

                    int duration = Math.Max(3, SEnvir.Random.Next(Magic.Level + 1));
                    ob.ApplyPoison(new Poison
                    {
                        Owner = Player,
                        Type = PoisonType.Paralysis,
                        TickCount = duration,
                        TickFrequency = TimeSpan.FromSeconds(1),
                    });
                }
            }
        }

        public override AttackCast AttackCast(MagicType attackType)
        {
            // Clear a stale marker from a previous attack that missed before AttackComplete.
            pendingNextAttackStun = false;

            var response = new AttackCast();
            BuffInfo buff = Player.Buffs.Find(x => x.Type == BuffType.MoonMist && x.Extra > 0);
            if (buff == null) return response;

            Player.BuffRemove(buff);
            pendingNextAttackStun = true;
            response.Magics.Add(Type);
            return response;
        }

        public override int ModifyPowerAdditionner(bool primary, int power, MapObject ob, Stats stats = null, int extra = 0)
        {
            // Preserve Jev's source quirk: the stealth-break bonus resolves through DarkBody power.
            if (Player.GetMagic(MagicType.DarkBody, out DarkBody darkBody))
                power += darkBody.Magic.GetPower();

            return power;
        }

        public override void AttackComplete(MapObject target)
        {
            if (!pendingNextAttackStun) return;

            pendingNextAttackStun = false;
            if (target?.Node == null || target.Dead || SEnvir.Random.Next(3) != 0) return;

            target.ApplyPoison(new Poison
            {
                Owner = Player,
                Type = PoisonType.Paralysis,
                TickCount = 5,
                TickFrequency = TimeSpan.FromSeconds(1),
            });
        }
    }
}
