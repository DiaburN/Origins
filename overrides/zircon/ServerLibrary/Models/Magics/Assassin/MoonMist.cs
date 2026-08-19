using Library;
using Server.DBModels;
using Server.Envir;
using System;
using System.Drawing;

namespace Server.Models.Magics
{
    [MagicType(MagicType.MoonMist)]
    public sealed class MoonMist : MagicObject
    {
        protected override Element Element => Element.None;
        public override bool UpdateCombatTime => false;

        public MoonMist(PlayerObject player, UserMagic magic) : base(player, magic) { }

        public override MagicCast MagicCast(MapObject target, Point location, MirDirection direction)
        {
            var response = new MagicCast { Ob = Player };

            // Base Crystal MoonMist refuses to cast while MoonLight stealth is already active.
            if (Player.Buffs.Exists(x => x.Type == BuffType.MoonLight))
            {
                response.Cast = false;
                return response;
            }

            response.Targets.Add(Player.ObjectID);

            double stealthSeconds = (Player.GetAC() + (Magic.Level + 1) * 5) * 0.5D;
            Player.BuffAdd(BuffType.MoonLight, TimeSpan.FromSeconds(stealthSeconds), new Stats(), true, false, TimeSpan.Zero);

            int power = Magic.GetPower() + Player.GetDC();
            ActionList.Add(new DelayedAction(
                SEnvir.Now.AddMilliseconds(500),
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
                    int dealt = 0;
                    if (damage > 0)
                        dealt = ob.Attacked(Player, damage, Element.None, true, false, false, true);
                    else
                        ob.Blocked();

                    // Preserve the source quirk: the undead Stun is only attempted when
                    // the AC-resolved hit does not deal damage.
                    if (dealt <= 0 && ob.Undead)
                    {
                        ob.ApplyPoison(new Poison
                        {
                            Owner = Player,
                            Type = PoisonType.Paralysis,
                            TickCount = Magic.Level + 2,
                            TickFrequency = TimeSpan.FromSeconds(1),
                        });
                    }
                }
            }
        }
    }
}
