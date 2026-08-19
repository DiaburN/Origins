using Library;
using Server.DBModels;
using Server.Envir;
using System;
using System.Drawing;
using System.Linq;

namespace Server.Models.Magics
{
    [MagicType(MagicType.Heal)]
    public sealed class Heal : MagicObject
    {
        protected override Element Element => Element.None;
        public override bool UpdateCombatTime => false;

        public Heal(PlayerObject player, UserMagic magic) : base(player, magic)
        {
        }

        public override MagicCast MagicCast(MapObject target, Point location, MirDirection direction)
        {
            if (target == null || !Player.CanHelpTarget(target)) target = Player;

            var response = new MagicCast { Ob = target };
            response.Targets.Add(target.ObjectID);

            // Crystal snapshots SC at cast time and resolves Healing after 500 ms.
            int healing = Magic.GetPower() + Player.GetSC() * 2 + Player.Level;
            ActionList.Add(new DelayedAction(SEnvir.Now.AddMilliseconds(500), ActionType.DelayMagic, Type, target, healing));
            return response;
        }

        public override void MagicComplete(params object[] data)
        {
            MapObject target = (MapObject)data[1];
            int healing = (int)data[2];

            if (target?.Node == null || target.CurrentMap != CurrentMap || !Player.CanHelpTarget(target)) return;
            if (target.CurrentHP >= target.Stats[Stat.Health]) return;

            BuffInfo pool = target.Buffs.FirstOrDefault(x => x.Type == BuffType.CrystalHealing);
            if (pool == null)
            {
                target.BuffAdd(
                    BuffType.CrystalHealing,
                    TimeSpan.MaxValue,
                    new Stats { [Stat.Healing] = healing },
                    false,
                    false,
                    TimeSpan.FromMilliseconds(600));
            }
            else
            {
                pool.Stats[Stat.Healing] += healing;
            }

            Player.LevelMagic(Magic);
        }
    }
}
