using Library;
using Library.Network;
using Server.DBModels;
using Server.Envir;
using System;
using System.Drawing;
using S = Library.Network.ServerPackets;

namespace Server.Models.Magics
{
    [MagicType(MagicType.Reincarnation)]
    public sealed class Reincarnation : MagicObject
    {
        protected override Element Element => Element.None;
        public override bool UpdateCombatTime => false;

        public Reincarnation(PlayerObject player, UserMagic magic) : base(player, magic) { }

        public override MagicCast MagicCast(MapObject target, Point location, MirDirection direction)
        {
            var response = new MagicCast { Ob = target };
            PlayerObject deadTarget = target as PlayerObject;

            if (deadTarget == null || !deadTarget.Dead || Player.ActiveReincarnation || Player.ReincarnationReady)
            {
                response.Cast = false;
                response.Ob = null;
                return response;
            }

            // Crystal requires one Revival Amulet (shape 3).
            if (!Player.UseAmulet(1, 3))
            {
                response.Cast = false;
                return response;
            }

            response.Targets.Add(deadTarget.ObjectID);

            int castMilliseconds = Math.Abs(((Magic.Level + 1) * 1000) - 9000); // 8/7/6/5 sec
            DateTime castEnd = SEnvir.Now.AddMilliseconds(castMilliseconds);

            Player.ActiveReincarnation = true;
            Player.ReincarnationReady = true;
            Player.ReincarnationTarget = deadTarget;
            Player.ReincarnationExpireTime = castEnd.AddSeconds(5);
            deadTarget.ReincarnationHost = Player;

            // Keep the caster occupied for the Crystal channel duration.
            if (Player.ActionTime < castEnd)
                Player.ActionTime = castEnd;

            // Crystal consumes the amulet even if this initial success roll fails.
            if (SEnvir.Random.Next(30) <= (1 + Magic.Level) * 10)
            {
                ActionList.Add(new DelayedAction(castEnd, ActionType.DelayMagic, Type, deadTarget));
            }

            return response;
        }

        public override void MagicComplete(params object[] data)
        {
            PlayerObject deadTarget = (PlayerObject)data[1];

            if (!Player.ActiveReincarnation || !Player.ReincarnationReady ||
                Player.ReincarnationTarget != deadTarget || deadTarget?.Node == null || !deadTarget.Dead)
                return;

            // Crystal completion asks the dead target to accept or cancel. The request window
            // remains open until ReincarnationExpireTime (cast end + 5 sec).
            deadTarget.Enqueue(new S.ReincarnationRequest());
            Player.LevelMagic(Magic);
        }
    }
}
