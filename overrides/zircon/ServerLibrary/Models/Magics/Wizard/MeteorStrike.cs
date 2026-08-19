using Library;
using Server.DBModels;
using Server.Envir;
using System.Collections.Generic;
using System.Drawing;

namespace Server.Models.Magics
{
    [MagicType(MagicType.MeteorStrike)]
    public sealed class MeteorStrike : MagicObject
    {
        protected override Element Element => Element.Fire;

        private const int SetupDelay = 500;
        private const int FirstPulseDelay = 1300;
        private const int PulseInterval = 440;
        private const int PulseCount = 5;

        public MeteorStrike(PlayerObject player, UserMagic magic) : base(player, magic)
        {
        }

        public override MagicCast MagicCast(MapObject target, Point location, MirDirection direction)
        {
            var response = new MagicCast { Ob = null };

            Map castMap = CurrentMap;
            Point center = location;
            int castPower = Magic.GetPower() + Player.GetMC();

            foreach (Cell cell in castMap.GetCells(center, 0, 2))
            {
                if (cell == null) continue;
                response.Locations.Add(cell.Location);
            }

            ActionList.Add(new DelayedAction(
                SEnvir.Now.AddMilliseconds(SetupDelay),
                ActionType.DelayMagic,
                Type,
                castMap,
                center,
                castPower,
                -1));

            for (int pulse = 0; pulse < PulseCount; pulse++)
            {
                ActionList.Add(new DelayedAction(
                    SEnvir.Now.AddMilliseconds(FirstPulseDelay + pulse * PulseInterval),
                    ActionType.DelayMagic,
                    Type,
                    castMap,
                    center,
                    castPower,
                    pulse));
            }

            return response;
        }

        public override void MagicComplete(params object[] data)
        {
            Map castMap = (Map)data[1];
            Point center = (Point)data[2];
            int castPower = (int)data[3];
            int pulse = (int)data[4];

            if (castMap == null) return;

            if (pulse < 0)
            {
                Player.LevelMagic(Magic);
                return;
            }

            foreach (Cell cell in castMap.GetCells(center, 0, 2))
            {
                if (cell?.Objects == null) continue;

                for (int i = cell.Objects.Count - 1; i >= 0; i--)
                {
                    if (i >= cell.Objects.Count) continue;

                    MapObject ob = cell.Objects[i];
                    if (ob.Race != ObjectType.Player && ob.Race != ObjectType.Monster) continue;
                    if (!Player.CanAttackTarget(ob)) continue;

                    Player.MagicAttack(new List<MagicType> { Type }, ob, true, null, castPower);
                }
            }
        }

        public override void MagicAttackSuccess(MapObject ob, int damageDealt)
        {
            // Crystal levels MeteorStrike when the field is created, not once per pulse/target.
        }

        public override int ModifyPowerAdditionner(bool primary, int power, MapObject ob, Stats stats = null, int extra = 0)
        {
            power += extra != 0 ? extra : Magic.GetPower() + Player.GetMC();
            return power;
        }
    }
}
