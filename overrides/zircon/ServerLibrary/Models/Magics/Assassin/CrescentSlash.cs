using Library;
using Server.DBModels;
using Server.Envir;
using System;
using System.Drawing;

namespace Server.Models.Magics
{
    [MagicType(MagicType.CrescentSlash)]
    public sealed class CrescentSlash : MagicObject
    {
        protected override Element Element => Element.None;

        public CrescentSlash(PlayerObject player, UserMagic magic) : base(player, magic) { }

        public override MagicCast MagicCast(MapObject target, Point location, MirDirection direction)
        {
            var response = new MagicCast { Ob = null };
            response.Locations.Add(CurrentLocation);

            int basePower = Player.GetDC();
            if (SEnvir.Random.Next(100) <= Player.Stats[Stat.Accuracy])
                basePower += basePower;

            int power = Magic.GetPower() + basePower;
            int attackDelay = Globals.AttackDelay - Player.Stats[Stat.AttackSpeed] * Globals.ASpeedRate;
            attackDelay = Math.Max(800, attackDelay);

            ActionList.Add(new DelayedAction(
                SEnvir.Now.AddMilliseconds(attackDelay),
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
            MirDirection direction = (MirDirection)data[3];
            int power = (int)data[4];
            if (map != CurrentMap) return;

            MirDirection back = Functions.ShiftDirection(direction, 4);
            MirDirection backLeft = Functions.ShiftDirection(back, -1);
            MirDirection backRight = Functions.ShiftDirection(back, 1);
            bool trained = false;

            for (int i = 0; i < 8; i++)
            {
                MirDirection d = (MirDirection)i;
                if (d == back || d == backLeft || d == backRight) continue;

                Cell cell = map.GetCell(Functions.Move(origin, d));
                if (cell?.Objects == null) continue;

                for (int o = cell.Objects.Count - 1; o >= 0; o--)
                {
                    MapObject ob = cell.Objects[o];
                    if (ob?.Node == null || !Player.CanAttackTarget(ob)) continue;

                    int damage = power - ob.GetAC();
                    if (damage <= 0)
                    {
                        ob.Blocked();
                        continue;
                    }

                    if (ob.Attacked(Player, damage, Element.None, true, false, false, true) > 0)
                        trained = true;
                }
            }

            if (trained)
                Player.LevelMagic(Magic);
        }
    }
}
