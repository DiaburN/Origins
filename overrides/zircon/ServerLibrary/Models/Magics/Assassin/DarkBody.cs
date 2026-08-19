using Library;
using Library.SystemModels;
using Server.DBModels;
using Server.Envir;
using System;
using System.Drawing;
using System.Linq;

namespace Server.Models.Magics
{
    [MagicType(MagicType.DarkBody)]
    public sealed class DarkBody : MagicObject
    {
        protected override Element Element => Element.None;
        public override bool UpdateCombatTime => false;

        public DarkBody(PlayerObject player, UserMagic magic) : base(player, magic) { }

        public override MagicCast MagicCast(MapObject target, Point location, MirDirection direction)
        {
            var response = new MagicCast { Ob = target };

            if (target == null)
            {
                response.Cast = false;
                response.Ob = null;
                return response;
            }

            MonsterInfo info = SEnvir.MonsterInfoList.Binding.FirstOrDefault(x => x.MonsterName == "AssassinClone");
            if (info == null)
            {
                response.Cast = false;
                return response;
            }

            // Crystal toggles an existing living AssassinClone off instead of summoning another.
            MonsterObject existing = Player.Pets.FirstOrDefault(x => x.MonsterInfo == info && x.Node != null && !x.Dead);
            if (existing != null)
            {
                existing.SetHP(0);
                return response;
            }

            MonsterObject clone = MonsterObject.GetMonster(info);
            if (clone == null)
            {
                response.Cast = false;
                return response;
            }

            clone.PetOwner = Player;
            clone.Target = target;
            clone.Direction = direction;
            clone.SummonLevel = Magic.Level * 2;
            clone.TameTime = SEnvir.Now.AddDays(365);
            Player.Pets.Add(clone);

            if (!clone.Spawn(CurrentMap, CurrentLocation))
            {
                Player.Pets.Remove(clone);
                response.Cast = false;
                return response;
            }

            if (!Player.Buffs.Exists(x => x.Type == BuffType.DarkBody))
                Player.LevelMagic(Magic);

            double durationSeconds = (Player.GetAC() + (Magic.Level + 1) * 5) * 0.5D;
            Player.BuffAdd(BuffType.DarkBody, TimeSpan.FromSeconds(durationSeconds), new Stats(), true, false, TimeSpan.Zero);

            return response;
        }
    }
}
