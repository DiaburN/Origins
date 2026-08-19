using Library;
using Server.DBModels;
using Server.Envir;
using System;
using System.Drawing;

namespace Server.Models.Magics
{
    [MagicType(MagicType.PetEnhancer)]
    public sealed class PetEnhancer : MagicObject
    {
        protected override Element Element => Element.None;
        public override bool UpdateCombatTime => false;

        public PetEnhancer(PlayerObject player, UserMagic magic) : base(player, magic) { }

        public override MagicCast MagicCast(MapObject target, Point location, MirDirection direction)
        {
            var response = new MagicCast { Ob = target };

            if (target == null || target.Race != ObjectType.Monster || !Player.CanHelpTarget(target))
            {
                response.Cast = false;
                response.Ob = null;
                return response;
            }

            response.Targets.Add(target.ObjectID);
            int durationSeconds = Magic.GetPower() + Player.GetSC();
            ActionList.Add(new DelayedAction(SEnvir.Now.AddMilliseconds(500), ActionType.DelayMagic, Type, target, durationSeconds));
            return response;
        }

        public override void MagicComplete(params object[] data)
        {
            MapObject target = (MapObject)data[1];
            int durationSeconds = (int)data[2];
            if (target?.Node == null || target.Race != ObjectType.Monster || !Player.CanHelpTarget(target)) return;

            int dc = 2 + target.Level * 2;
            int ac = 4 + target.Level;

            Stats stats = new Stats
            {
                [Stat.MinDC] = dc,
                [Stat.MaxDC] = dc,
                [Stat.MinAC] = ac,
                [Stat.MaxAC] = ac,
            };

            target.BuffAdd(BuffType.PetEnhancer, TimeSpan.FromSeconds(durationSeconds), stats, true, false, TimeSpan.Zero);
            Player.LevelMagic(Magic);
        }
    }
}
