using Library;
using Server.DBModels;
using Server.Envir;
using System.Drawing;

namespace Server.Models.Magics
{
    [MagicType(MagicType.Teleportation)]
    public class Teleportation : MagicObject
    {
        protected override Element Element => Element.None;
        public override bool UpdateCombatTime => false;

        public Teleportation(PlayerObject player, UserMagic magic) : base(player, magic)
        {
        }

        public override MagicCast MagicCast(MapObject target, Point location, MirDirection direction)
        {
            var response = new MagicCast { Ob = null };

            ActionList.Add(new DelayedAction(
                SEnvir.Now.AddMilliseconds(200),
                ActionType.DelayMagic,
                Type));

            return response;
        }

        public override void MagicComplete(params object[] data)
        {
            if (CurrentMap.Info.NoTeleport) return;

            var bindRegion = CurrentMap.Instance?.ReconnectRegion ?? Player.Character.BindPoint?.BindRegion;
            if (bindRegion == null) return;

            if (!Player.Teleport(bindRegion, null, 0)) return;

            Player.LevelMagic(Magic);
        }
    }
}
