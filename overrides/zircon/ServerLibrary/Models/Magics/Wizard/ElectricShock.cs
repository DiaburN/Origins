using Library;
using Server.DBModels;
using Server.Envir;
using System;
using System.Drawing;
using System.Linq;

using S = Library.Network.ServerPackets;

namespace Server.Models.Magics
{
    [MagicType(MagicType.ElectricShock)]
    public class ElectricShock : MagicObject
    {
        protected override Element Element => Element.None;
        public override bool UpdateCombatTime => false;

        public ElectricShock(PlayerObject player, UserMagic magic) : base(player, magic)
        {
        }

        public override MagicCast MagicCast(MapObject target, Point location, MirDirection direction)
        {
            var response = new MagicCast
            {
                Ob = null
            };

            if (!Player.CanAttackTarget(target) || target?.Race != ObjectType.Monster)
            {
                response.Locations.Add(location);
                return response;
            }

            response.Targets.Add(target.ObjectID);
            ActionList.Add(new DelayedAction(SEnvir.Now.AddMilliseconds(500), ActionType.DelayMagic, Type, target));

            return response;
        }

        public override void MagicComplete(params object[] data)
        {
            MonsterObject ob = (MonsterObject)data[1];

            if (CurrentMap.Info.NoPets) return;
            if (ob?.Node == null || !Player.CanAttackTarget(ob) || ob.CurrentMap != CurrentMap) return;

            // Crystal: level 0/1/2/3 has 1/4, 1/3, 1/2, 1/1 chance to enter the tame attempt.
            if (SEnvir.Random.Next(4 - Math.Min(3, Magic.Level)) > 0)
            {
                if (SEnvir.Random.Next(2) == 0)
                    Player.LevelMagic(Magic);
                return;
            }

            Player.LevelMagic(Magic);

            if (ob.PetOwner == Player)
            {
                ob.ShockTime = SEnvir.Now.AddSeconds(Magic.Level * 5 + 10);
                ob.Target = null;
                return;
            }

            if (SEnvir.Random.Next(2) > 0)
            {
                ob.ShockTime = SEnvir.Now.AddSeconds(Magic.Level * 5 + 10);
                ob.Target = null;
                return;
            }

            if (ob.Level > Player.Level + 2 || !ob.MonsterInfo.CanTame) return;

            if (ob.MonsterInfo.IsBoss)
            {
                if (Config.MaxBossTames <= 0) return;

                int currentBossTames = Player.Pets.Count(x => !x.Dead && x.MonsterInfo != null && x.MonsterInfo.IsBoss);
                if (currentBossTames >= Config.MaxBossTames) return;
            }

            if (SEnvir.Random.Next(Player.Level + 20 + Magic.Level * 5) <= ob.Level + 10)
            {
                if (SEnvir.Random.Next(5) > 0 && ob.PetOwner == null)
                {
                    ob.RageTime = SEnvir.Now.AddSeconds(SEnvir.Random.Next(20) + 10);
                    ob.Target = null;
                }
                return;
            }

            // Crystal Globals.MaxPets is 5, therefore the live-monster cap is level + (5 - 3).
            if (Player.Pets.Count(x => !x.Dead) >= Magic.Level + 2) return;

            int rate = ob.Stats[Stat.Health] / 100;
            if (rate <= 2)
                rate = 2;
            else
                rate *= 2;

            if (SEnvir.Random.Next(rate) != 0) return;

            if (ob.PetOwner != null)
            {
                int hp = Math.Max(1, ob.Stats[Stat.Health] / 10);
                if (hp < ob.CurrentHP)
                    ob.SetHP(hp);

                ob.PetOwner.Pets.Remove(ob);
                ob.PetOwner = null;
                ob.Magics.Clear();
            }
            else if (ob.SpawnInfo != null)
            {
                ob.SpawnInfo.AliveCount--;
                ob.SpawnInfo = null;
            }

            ob.PetOwner = Player;
            Player.Pets.Add(ob);

            ob.Master?.MinionList.Remove(ob);
            ob.Master = null;

            // Crystal default PetSave=false uses a 60 minute tame duration.
            ob.TameTime = SEnvir.Now.AddHours(1);
            ob.Target = null;
            ob.RageTime = DateTime.MinValue;
            ob.ShockTime = DateTime.MinValue;
            ob.Magics.Add(Magic);
            ob.SummonLevel = Magic.Level;
            ob.RefreshStats();

            Player.LogMilestone(MilestoneType.PetTame, 1, monster: ob.MonsterInfo);
            ob.Broadcast(new S.ObjectPetOwnerChanged { ObjectID = ob.ObjectID, PetOwner = Player.Name });
        }
    }
}
