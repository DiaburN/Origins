using Library;
using Library.SystemModels;
using Server.DBModels;
using Server.Envir;
using System.Drawing;
using System.Linq;

namespace Server.Models.Magics
{
    [MagicType(MagicType.SummonShinsu)]
    public class SummonShinsu : MagicObject
    {
        protected override Element Element => Element.None;
        public override bool UpdateCombatTime => false;

        public SummonShinsu(PlayerObject player, UserMagic magic) : base(player, magic) { }

        public override MagicCast MagicCast(MapObject target, Point location, MirDirection direction)
        {
            var response = new MagicCast { Ob = null };
            MonsterInfo info = SEnvir.MonsterInfoList.Binding.FirstOrDefault(x => x.Flag == MonsterFlag.Shinsu);
            if (info == null)
            {
                response.Cast = false;
                return response;
            }

            // Crystal recalls an existing living Shinsu without consuming five amulets again.
            MonsterObject existing = Player.Pets.FirstOrDefault(x => x.MonsterInfo == info && x.Node != null && !x.Dead);
            if (existing != null)
            {
                ActionList.Add(new DelayedAction(SEnvir.Now.AddMilliseconds(500), ActionType.DelayMagic, Type, true, existing));
                return response;
            }

            if (Player.Pets.Count(x => x.Race == ObjectType.Monster && !x.Dead) >= 2 || !Player.UseAmulet(5, 0))
            {
                response.Cast = false;
                return response;
            }

            ActionList.Add(new DelayedAction(
                SEnvir.Now.AddMilliseconds(500),
                ActionType.DelayMagic,
                Type,
                false,
                CurrentMap,
                Functions.Move(CurrentLocation, direction),
                info));

            return response;
        }

        public override void MagicComplete(params object[] data)
        {
            bool recall = (bool)data[1];
            if (recall)
            {
                MonsterObject existing = (MonsterObject)data[2];
                existing?.PetRecall();
                return;
            }

            Map map = (Map)data[2];
            Point location = (Point)data[3];
            MonsterInfo info = (MonsterInfo)data[4];

            if (map == null || info == null || Player.Pets.Count(x => x.Race == ObjectType.Monster && !x.Dead) >= 2) return;

            MonsterObject ob = MonsterObject.GetMonster(info);
            if (ob == null) return;

            ob.PetOwner = Player;
            Player.Pets.Add(ob);
            ob.Master?.MinionList.Remove(ob);
            ob.Master = null;
            ob.Magics.Add(Magic);
            ob.SummonLevel = Magic.Level * 2;
            ob.TameTime = SEnvir.Now.AddDays(365);

            Cell cell = map.GetCell(location);
            if (cell == null || cell.Movements != null || !ob.Spawn(map, location))
                ob.Spawn(CurrentMap, CurrentLocation);

            ob.SetHP(ob.Stats[Stat.Health]);
            Player.LevelMagic(Magic);
        }
    }
}
