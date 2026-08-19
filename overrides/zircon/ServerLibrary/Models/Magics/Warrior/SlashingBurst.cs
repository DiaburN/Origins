using Library;
using Library.Network.ServerPackets;
using Server.DBModels;
using Server.Envir;
using System.Collections.Generic;
using System.Drawing;

namespace Server.Models.Magics
{
    [MagicType(MagicType.SlashingBurst)]
    public sealed class SlashingBurst : MagicObject
    {
        protected override Element Element => Element.None;
        public override bool IgnoreAccuracy => true;

        public SlashingBurst(PlayerObject player, UserMagic magic) : base(player, magic)
        {
        }

        public override MagicCast MagicCast(MapObject target, Point location, MirDirection direction)
        {
            var response = new MagicCast { Ob = null, Direction = direction };

            Map castMap = CurrentMap;
            Point origin = CurrentLocation;
            int damage = Player.GetDC() + Magic.GetPower();

            ActionList.Add(new DelayedAction(
                SEnvir.Now.AddMilliseconds(500),
                ActionType.DelayMagic,
                Type,
                castMap,
                origin,
                direction,
                damage));

            Point destination = Functions.Move(origin, direction, 2);
            Cell cell = castMap.GetCell(destination);
            if (cell == null) return response;

            if (cell.Objects != null)
            {
                for (int i = cell.Objects.Count - 1; i >= 0; i--)
                {
                    if (cell.Objects[i].Blocking)
                        return response;
                }
            }

            Player.CurrentCell = cell.GetMovement(Player);
            Player.RemoveAllObjects();
            Player.AddAllObjects();

            Player.Broadcast(new ObjectDash
            {
                ObjectID = Player.ObjectID,
                Direction = direction,
                Location = origin,
                Distance = 2,
                Magic = Type,
            });

            return response;
        }

        public override void MagicComplete(params object[] data)
        {
            Map castMap = (Map)data[1];
            Point origin = (Point)data[2];
            MirDirection direction = (MirDirection)data[3];
            int damage = (int)data[4];

            if (castMap == null) return;

            Cell hitCell = castMap.GetCell(Functions.Move(origin, direction));
            if (hitCell?.Objects == null) return;

            bool train = false;

            for (int i = hitCell.Objects.Count - 1; i >= 0; i--)
            {
                if (i >= hitCell.Objects.Count) continue;
                MapObject ob = hitCell.Objects[i];
                if (!Player.CanAttackTarget(ob)) continue;

                Player.Attack(ob, new List<MagicType> { Type }, true, damage);
                train = true;
            }

            if (train)
                Player.LevelMagic(Magic);
        }

        public override int ModifyPowerAdditionner(bool primary, int power, MapObject ob, Stats stats = null, int extra = 0)
        {
            return extra > 0 ? extra : power + Magic.GetPower();
        }

        public override void AttackComplete(MapObject target)
        {
            // Crystal trains once for the delayed burst cell, not once per target.
        }
    }
}
