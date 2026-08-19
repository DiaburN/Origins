using Library;
using Server.DBModels;
using System;
using System.Drawing;

namespace Server.Models.Magics
{
    [MagicType(MagicType.UltimateEnhancer)]
    public sealed class UltimateEnhancer : MagicObject
    {
        protected override Element Element => Element.None;
        public override bool UpdateCombatTime => false;

        public UltimateEnhancer(PlayerObject player, UserMagic magic) : base(player, magic) { }

        public override MagicCast MagicCast(MapObject target, Point location, MirDirection direction)
        {
            var response = new MagicCast { Ob = target };
            if (target?.Node == null || !Player.CanHelpTarget(target) || !Player.UseAmulet(1, 0))
            {
                response.Cast = false;
                response.Ob = null;
                return response;
            }

            response.Targets.Add(target.ObjectID);

            int durationSeconds = Player.GetSC() * 4 + (Magic.Level + 1) * 50;
            int value = Player.Stats[Stat.MaxSC] >= 5 ? Math.Min(8, Player.Stats[Stat.MaxSC] / 5) : 1;

            Stats stats = new Stats();
            if (target.Race == ObjectType.Monster)
            {
                stats[Stat.MaxDC] = value;
            }
            else if (target is PlayerObject playerTarget)
            {
                switch (playerTarget.Class)
                {
                    case MirClass.Warrior:
                    case MirClass.Assassin:
                        stats[Stat.MaxDC] = value;
                        break;
                    case MirClass.Wizard:
                    case MirClass.Archer:
                        stats[Stat.MaxMC] = value;
                        break;
                    case MirClass.Taoist:
                        stats[Stat.MaxSC] = value;
                        break;
                    default:
                        response.Cast = false;
                        return response;
                }
            }

            target.BuffAdd(BuffType.UltimateEnhancer, TimeSpan.FromSeconds(durationSeconds), stats, true, false, TimeSpan.Zero);
            Player.LevelMagic(Magic);
            return response;
        }
    }
}
