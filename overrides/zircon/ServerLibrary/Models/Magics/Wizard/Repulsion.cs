using Library;
using Server.DBModels;
using Server.Envir;
using System;
using System.Drawing;

namespace Server.Models.Magics
{
    [MagicType(MagicType.Repulsion)]
    public class Repulsion : MagicObject
    {
        protected override Element Element => Element.None;
        public override bool UpdateCombatTime => false;

        public Repulsion(PlayerObject player, UserMagic magic) : base(player, magic)
        {
        }

        public override MagicCast MagicCast(MapObject target, Point location, MirDirection direction)
        {
            var response = new MagicCast
            {
                Ob = null
            };

            var delay = SEnvir.Now.AddMilliseconds(500);

            for (MirDirection d = MirDirection.Up; d <= MirDirection.UpLeft; d++)
            {
                Cell cell = CurrentMap.GetCell(Functions.Move(CurrentLocation, d));
                ActionList.Add(new DelayedAction(delay, ActionType.DelayMagic, Type, cell, d));
            }

            return response;
        }

        public override void MagicComplete(params object[] data)
        {
            Cell cell = (Cell)data[1];
            MirDirection direction = (MirDirection)data[2];

            if (cell?.Objects == null) return;

            for (int i = cell.Objects.Count - 1; i >= 0; i--)
            {
                MapObject ob = cell.Objects[i];

                // ORIGINS rule: player push skills do not repel other players.
                if (ob.Race != ObjectType.Monster) continue;
                if (!Player.CanAttackTarget(ob) || ob.Level >= Player.Level) continue;
                if (SEnvir.Random.Next(20) >= 6 + Magic.Level * 3 + Player.Level - ob.Level) continue;

                int distance = 1 + Math.Max(0, Magic.Level - 1) + SEnvir.Random.Next(2);

                if (ob.Pushed(direction, distance) <= 0) continue;

                Player.LevelMagic(Magic);
                break;
            }
        }
    }
}
