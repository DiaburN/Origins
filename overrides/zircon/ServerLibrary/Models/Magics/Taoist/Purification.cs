using Library;
using Server.DBModels;
using Server.Envir;
using System.Drawing;

namespace Server.Models.Magics
{
    [MagicType(MagicType.Purification)]
    public class Purification : MagicObject
    {
        protected override Element Element => Element.None;
        public override bool UpdateCombatTime => false;

        public Purification(PlayerObject player, UserMagic magic) : base(player, magic) { }

        public override MagicCast MagicCast(MapObject target, Point location, MirDirection direction)
        {
            if (target == null || !Player.CanHelpTarget(target)) target = Player;

            var response = new MagicCast { Ob = target };
            response.Targets.Add(target.ObjectID);

            // Crystal Purification consumes no amulet and resolves after 500 ms.
            ActionList.Add(new DelayedAction(SEnvir.Now.AddMilliseconds(500), ActionType.DelayMagic, Type, target));
            return response;
        }

        public override void MagicComplete(params object[] data)
        {
            MapObject target = (MapObject)data[1];
            if (target?.Node == null || target.CurrentMap != CurrentMap || !Player.CanHelpTarget(target)) return;

            // Crystal: Random.Next(4) <= magic level.
            if (SEnvir.Random.Next(4) > Magic.Level) return;

            // Zircon's friendly Purify removes its registered negative buffs and poisons.
            // Crystal then clears the entire poison list, including delayed/parasite-style entries.
            Player.Purify(target);
            target.PoisonList.Clear();

            Player.LevelMagic(Magic);
        }
    }
}
