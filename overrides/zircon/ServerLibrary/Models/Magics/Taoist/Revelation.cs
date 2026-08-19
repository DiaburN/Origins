using Library;
using Server.DBModels;
using Server.Envir;
using System.Drawing;

namespace Server.Models.Magics
{
    [MagicType(MagicType.Revelation)]
    public sealed class Revelation : MagicObject
    {
        protected override Element Element => Element.None;
        public override bool UpdateCombatTime => false;

        public Revelation(PlayerObject player, UserMagic magic) : base(player, magic) { }

        public override MagicCast MagicCast(MapObject target, Point location, MirDirection direction)
        {
            var response = new MagicCast { Ob = target };
            if (target == null || (target.Race != ObjectType.Player && target.Race != ObjectType.Monster))
            {
                response.Ob = null;
                return response;
            }

            response.Targets.Add(target.ObjectID);
            int durationSeconds = Player.GetSC() + Magic.GetPower();
            ActionList.Add(new DelayedAction(SEnvir.Now.AddMilliseconds(500), ActionType.DelayMagic, Type, target, durationSeconds));
            return response;
        }

        public override void MagicComplete(params object[] data)
        {
            MapObject target = (MapObject)data[1];
            int durationSeconds = (int)data[2];

            if (target?.Node == null || target.CurrentMap != CurrentMap) return;
            if (target.Race != ObjectType.Player && target.Race != ObjectType.Monster) return;
            if (SEnvir.Random.Next(4) > Magic.Level || SEnvir.Now < target.CrystalRevelationTime) return;

            target.CrystalRevelationTime = SEnvir.Now.AddSeconds(durationSeconds);
            Player.LevelMagic(Magic);
        }
    }
}
