using Library;
using Server.DBModels;
using Server.Envir;
using System;
using System.Drawing;

namespace Server.Models.Magics
{
    [MagicType(MagicType.PoisonSword)]
    public sealed class PoisonSword : MagicObject
    {
        protected override Element Element => Element.None;

        public PoisonSword(PlayerObject player, UserMagic magic) : base(player, magic) { }

        public override MagicCast MagicCast(MapObject target, Point location, MirDirection direction)
        {
            var response = new MagicCast { Ob = null };
            if (!Player.UsePoison(1, out _))
            {
                response.Cast = false;
                return response;
            }

            int power = Magic.GetPower() + Player.GetDC();
            bool touched = false;

            for (int i = -1; i <= 3; i++)
            {
                MirDirection hitDirection = Functions.ShiftDirection(direction, i);
                Cell cell = CurrentMap.GetCell(Functions.Move(CurrentLocation, hitDirection));
                if (cell?.Objects == null) continue;

                for (int o = 0; o < cell.Objects.Count; o++)
                {
                    MapObject ob = cell.Objects[o];
                    if (ob?.Node == null || (ob.Race != ObjectType.Player && ob.Race != ObjectType.Monster) || !Player.CanAttackTarget(ob)) continue;

                    int poisonBonus = Player.Stats[Stat.PoisonAttack] > 0
                        ? SEnvir.Random.Next(Player.Stats[Stat.PoisonAttack])
                        : 0;
                    int duration = Math.Max(1, 3 + power / 10 + Magic.Level * 3);

                    ob.ApplyPoison(new Poison
                    {
                        Owner = Player,
                        Type = PoisonType.Green,
                        TickCount = duration,
                        TickFrequency = TimeSpan.FromSeconds(1),
                        Value = power / 10 + Magic.Level + 1 + poisonBonus,
                    });

                    touched = true;
                    break;
                }
            }

            // Crystal consumes the poison and trains after the sweep even if no target is struck.
            Player.LevelMagic(Magic);
            response.Locations.Add(CurrentLocation);
            return response;
        }
    }
}
