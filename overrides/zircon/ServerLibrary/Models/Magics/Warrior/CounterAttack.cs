using Library;
using Server.DBModels;
using Server.Envir;
using System;
using System.Collections.Generic;
using System.Drawing;

namespace Server.Models.Magics
{
    [MagicType(MagicType.CounterAttack)]
    public sealed class CounterAttack : MagicObject
    {
        protected override Element Element => Element.None;
        public override bool UpdateCombatTime => false;

        public CounterAttack(PlayerObject player, UserMagic magic) : base(player, magic)
        {
        }

        public override MagicCast MagicCast(MapObject target, Point location, MirDirection direction)
        {
            int defence = 11 + Magic.Level * 3;

            Player.BuffRemove(BuffType.CounterAttack);
            Player.BuffAdd(
                BuffType.CounterAttack,
                TimeSpan.FromSeconds(7),
                new Stats
                {
                    [Stat.MinAC] = defence,
                    [Stat.MaxAC] = defence,
                    [Stat.MinMR] = defence,
                    [Stat.MaxMR] = defence,
                },
                false,
                false,
                TimeSpan.Zero);

            return new MagicCast { Ob = null, Direction = MirDirection.Down };
        }

        public bool TryCounter(MapObject attacker)
        {
            if (attacker?.Node == null || attacker.Dead) return false;
            if (!Player.Buffs.Exists(x => x.Type == BuffType.CounterAttack)) return false;
            if (attacker.CurrentMap != CurrentMap || !Functions.InRange(CurrentLocation, attacker.CurrentLocation, 1)) return false;
            if (SEnvir.Random.Next(10) > Magic.Level + 6) return false;

            int damage = Player.GetDC();
            if (SEnvir.Random.Next(100) <= Player.Stats[Stat.Accuracy])
                damage *= 2;
            damage += Magic.GetPower();

            // Crystal faces ReverseDirection(target.Direction), not a newly
            // calculated direction from the two coordinates.
            Player.Direction = Functions.ShiftDirection(attacker.Direction, 4);
            Player.Attack(attacker, new List<MagicType> { Type }, true, damage);
            Player.LevelMagic(Magic);
            Player.BuffRemove(BuffType.CounterAttack);
            return true;
        }

        public override int ModifyPowerAdditionner(bool primary, int power, MapObject ob, Stats stats = null, int extra = 0)
        {
            return extra > 0 ? extra : power + Magic.GetPower();
        }

        public override void AttackComplete(MapObject target)
        {
            // Training and state consumption happen once in TryCounter.
        }
    }
}
