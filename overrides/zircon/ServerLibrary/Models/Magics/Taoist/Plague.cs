using Library;
using Server.DBModels;
using Server.Envir;
using System;
using System.Collections.Generic;
using System.Drawing;

namespace Server.Models.Magics
{
    [MagicType(MagicType.Plague)]
    public sealed class Plague : MagicObject
    {
        protected override Element Element => Element.None;
        public override bool UpdateCombatTime => false;

        public Plague(PlayerObject player, UserMagic magic) : base(player, magic) { }

        public override MagicCast MagicCast(MapObject target, Point location, MirDirection direction)
        {
            var response = new MagicCast { Ob = null };

            if (!Functions.InRange(CurrentLocation, location, Globals.MagicRange) || !Player.UseAmulet(1, 0))
            {
                response.Cast = false;
                return response;
            }

            PoisonType heldPoison = PoisonType.None;
            if (Player.UsePoison(1, out int shape))
                heldPoison = shape == 0 ? PoisonType.Green : PoisonType.Red;

            response.Locations.Add(location);

            int value = Magic.GetPower() + Player.GetSC();
            var delay = SEnvir.Now.AddMilliseconds(500 + Functions.Distance(CurrentLocation, location) * 50);
            ActionList.Add(new DelayedAction(delay, ActionType.DelayMagic, Type, CurrentMap, location, value, heldPoison));

            return response;
        }

        public override void MagicComplete(params object[] data)
        {
            Map map = (Map)data[1];
            Point location = (Point)data[2];
            int value = (int)data[3];
            PoisonType heldPoison = (PoisonType)data[4];
            if (map != CurrentMap) return;

            bool trained = false;

            foreach (Cell cell in map.GetCells(location, 0, 1))
            {
                if (cell?.Objects == null) continue;

                for (int i = cell.Objects.Count - 1; i >= 0; i--)
                {
                    MapObject ob = cell.Objects[i];
                    if (ob?.Node == null || !Player.CanAttackTarget(ob)) continue;

                    int chance = SEnvir.Random.Next(15);
                    PoisonType poison = chance <= 2
                        ? PoisonType.Slow
                        : chance <= 4
                            ? PoisonType.Frozen
                            : chance <= 9
                                ? heldPoison
                                : PoisonType.None;

                    int tempValue = poison == PoisonType.Red
                        ? value / 15 + Magic.Level + 1
                        : value + (Magic.Level + 1) * 2;

                    if (poison != PoisonType.None)
                    {
                        int duration = (2 * (Magic.Level + 1)) + (value / 10);
                        ob.ApplyPoison(new Poison
                        {
                            Owner = Player,
                            Type = poison,
                            Value = tempValue,
                            TickCount = Math.Max(1, duration),
                            TickFrequency = TimeSpan.FromSeconds(1),
                        });
                    }

                    if (ob.Race == ObjectType.Player && tempValue > 0)
                        ob.ChangeMP(-tempValue);

                    Player.MagicAttack(new List<MagicType> { Type }, ob, true, null, Player.Stats[Stat.MaxSC] * 2);
                    trained = true;
                }
            }

            if (trained)
                Player.LevelMagic(Magic);
        }

        public override int ModifyPowerAdditionner(bool primary, int power, MapObject ob, Stats stats = null, int extra = 0)
        {
            return extra;
        }

        public override void MagicAttackSuccess(MapObject ob, int damageDealt)
        {
            // Crystal levels once per successful area cast, not once per target.
        }
    }
}
