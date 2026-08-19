using Library;
using Server.DBModels;
using Server.Envir;
using System;
using System.Drawing;

namespace Server.Models.Magics
{
    [MagicType(MagicType.LionRoar)]
    public sealed class LionRoar : MagicObject
    {
        protected override Element Element => Element.None;

        public LionRoar(PlayerObject player, UserMagic magic) : base(player, magic)
        {
        }

        public override MagicCast MagicCast(MapObject target, Point location, MirDirection direction)
        {
            Point center = CurrentLocation;

            ActionList.Add(new DelayedAction(
                SEnvir.Now.AddMilliseconds(500),
                ActionType.DelayMagic,
                Type,
                CurrentMap,
                center));

            return new MagicCast
            {
                Ob = null,
                Direction = MirDirection.Down,
            };
        }

        public override void MagicComplete(params object[] data)
        {
            Map castMap = (Map)data[1];
            Point center = (Point)data[2];

            if (castMap == null || Player.CurrentMap != castMap) return;

            bool train = false;

            foreach (Cell cell in castMap.GetCells(center, 0, 2))
            {
                if (cell?.Objects == null) continue;

                for (int i = cell.Objects.Count - 1; i >= 0; i--)
                {
                    if (i >= cell.Objects.Count) continue;

                    MapObject ob = cell.Objects[i];
                    if (ob.Race != ObjectType.Monster || ob.Dead) continue;
                    if (!Player.CanAttackTarget(ob)) continue;
                    if (Player.Level + 3 < ob.Level) continue;

                    ob.ApplyPoison(new Poison
                    {
                        Type = PoisonType.Paralysis,
                        Owner = Player,
                        TickCount = 1,
                        TickFrequency = TimeSpan.FromSeconds(Magic.Level + 2),
                    });

                    train = true;
                }
            }

            if (train)
                Player.LevelMagic(Magic);
        }
    }
}
