using Library;
using Server.DBModels;
using Server.Envir;
using System;
using System.Collections.Generic;
using System.Drawing;

namespace Server.Models.Magics
{
    [MagicType(MagicType.BladeAvalanche)]
    public sealed class BladeAvalanche : MagicObject
    {
        protected override Element Element => Element.None;
        public override bool IgnoreAccuracy => true;

        public BladeAvalanche(PlayerObject player, UserMagic magic) : base(player, magic)
        {
        }

        public override MagicCast MagicCast(MapObject target, Point location, MirDirection direction)
        {
            var response = new MagicCast { Ob = null, Direction = direction };

            int damageBase = Player.GetDC();
            if (SEnvir.Random.Next(100) <= 1 + Player.Stats[Stat.Luck])
                damageBase *= 2;

            int fullDamage = damageBase + Magic.GetPower();
            bool train = false;

            Point[] starts =
            {
                Functions.Move(CurrentLocation, Functions.ShiftDirection(direction, -1)),
                Functions.Move(CurrentLocation, direction),
                Functions.Move(CurrentLocation, Functions.ShiftDirection(direction, 1)),
            };

            for (int col = 0; col < starts.Length; col++)
            {
                for (int row = 0; row < 3; row++)
                {
                    Point hitPoint = Functions.Move(starts[col], direction, row);
                    Cell cell = CurrentMap.GetCell(hitPoint);
                    if (cell?.Objects == null) continue;

                    int damage = row <= 1 ? fullDamage : (int)(fullDamage * 0.6F);

                    for (int i = cell.Objects.Count - 1; i >= 0; i--)
                    {
                        if (i >= cell.Objects.Count) continue;
                        MapObject ob = cell.Objects[i];
                        if (!Player.CanAttackTarget(ob)) continue;

                        Player.Attack(ob, new List<MagicType> { Type }, true, damage);
                        train = true;
                    }
                }
            }

            if (train)
                Player.LevelMagic(Magic);

            return response;
        }

        public override int ModifyPowerAdditionner(bool primary, int power, MapObject ob, Stats stats = null, int extra = 0)
        {
            return extra > 0 ? extra : power + Magic.GetPower();
        }

        public override void AttackComplete(MapObject target)
        {
            // Crystal trains once for the whole 3x3 avalanche, not per target.
        }
    }
}
