using Library;
using Server.DBModels;
using Server.Envir;
using System;
using System.Drawing;
using System.Linq;
using M = Server.Models.Monsters;

namespace Server.Models.Magics
{
    [MagicType(MagicType.Mirroring)]
    public sealed class Mirroring : MagicObject
    {
        protected override Element Element => Element.None;
        public override bool UpdateCombatTime => false;

        public Mirroring(PlayerObject player, UserMagic magic) : base(player, magic)
        {
        }

        public override MagicCast MagicCast(MapObject target, Point location, MirDirection direction)
        {
            var response = new MagicCast { Ob = null };

            if (CurrentMap.Info.NoPets)
                return response;

            MonsterObject existing = Player.Pets.FirstOrDefault(x =>
                x.MonsterInfo.Flag == MonsterFlag.MirrorImage &&
                !x.Dead &&
                x.Node != null);

            if (existing != null)
            {
                ActionList.Add(new DelayedAction(
                    SEnvir.Now.AddMilliseconds(500),
                    ActionType.DelayMagic,
                    Type,
                    1,
                    existing));

                return response;
            }

            if (!SEnvir.MonsterInfoList.Binding.Any(x => x.Flag == MonsterFlag.MirrorImage))
                return response;

            Map castMap = CurrentMap;
            Point origin = CurrentLocation;
            Point front = Functions.Move(origin, direction);
            response.Locations.Add(front);

            // Crystal levels Mirroring when a new clone is requested, before the delayed spawn.
            Player.LevelMagic(Magic);

            ActionList.Add(new DelayedAction(
                SEnvir.Now.AddMilliseconds(500),
                ActionType.DelayMagic,
                Type,
                0,
                castMap,
                front,
                origin,
                direction));

            return response;
        }

        public override void MagicComplete(params object[] data)
        {
            int phase = (int)data[1];

            if (phase == 1)
            {
                MonsterObject existing = (MonsterObject)data[2];
                if (existing?.Node != null && existing.PetOwner == Player)
                    existing.Die();
                return;
            }

            Map castMap = (Map)data[2];
            Point front = (Point)data[3];
            Point origin = (Point)data[4];
            MirDirection direction = (MirDirection)data[5];

            if (castMap == null) return;
            if (Player.Pets.Any(x => x.MonsterInfo.Flag == MonsterFlag.MirrorImage && !x.Dead && x.Node != null)) return;

            var info = SEnvir.MonsterInfoList.Binding.FirstOrDefault(x => x.Flag == MonsterFlag.MirrorImage);
            if (info == null) return;

            M.MirrorImage mob = new()
            {
                MonsterInfo = info,
                Player = Player,
                Direction = direction,
                Element = Element.None,
                Location = front,
                ExplodeTime = DateTime.MaxValue,
                TameTime = SEnvir.Now.AddDays(365)
            };

            bool spawned = mob.Spawn(castMap, front) || mob.Spawn(castMap, origin);
            if (!spawned) return;

            Player.Pets.Add(mob);
            mob.PetOwner = Player;
        }
    }
}
