using Library.SystemModels;
using MirDB;
using Server.DBModels;

namespace Origins.Database.Runtime;

/// <summary>
/// Typed access to the core Zircon collections ORIGINS will use first.
/// Additional upstream collections remain available through Session.GetCollection&lt;T&gt;().
/// </summary>
public sealed class ZirconDatabaseCatalog
{
    public Session Session { get; }

    public DBCollection<MapInfo> Maps => Session.GetCollection<MapInfo>();
    public DBCollection<InstanceInfo> Instances => Session.GetCollection<InstanceInfo>();
    public DBCollection<DungeonInfo> Dungeons => Session.GetCollection<DungeonInfo>();
    public DBCollection<SafeZoneInfo> SafeZones => Session.GetCollection<SafeZoneInfo>();
    public DBCollection<MovementInfo> Movements => Session.GetCollection<MovementInfo>();
    public DBCollection<MapRegion> MapRegions => Session.GetCollection<MapRegion>();

    public DBCollection<ItemInfo> Items => Session.GetCollection<ItemInfo>();
    public DBCollection<SetInfo> Sets => Session.GetCollection<SetInfo>();
    public DBCollection<CurrencyInfo> Currencies => Session.GetCollection<CurrencyInfo>();
    public DBCollection<StoreInfo> Stores => Session.GetCollection<StoreInfo>();

    public DBCollection<MonsterInfo> Monsters => Session.GetCollection<MonsterInfo>();
    public DBCollection<RespawnInfo> Respawns => Session.GetCollection<RespawnInfo>();
    public DBCollection<DropInfo> Drops => Session.GetCollection<DropInfo>();

    public DBCollection<NPCInfo> Npcs => Session.GetCollection<NPCInfo>();
    public DBCollection<QuestInfo> Quests => Session.GetCollection<QuestInfo>();
    public DBCollection<MagicInfo> Magics => Session.GetCollection<MagicInfo>();

    public DBCollection<AccountInfo> Accounts => Session.GetCollection<AccountInfo>();
    public DBCollection<CharacterInfo> Characters => Session.GetCollection<CharacterInfo>();
    public DBCollection<UserItem> UserItems => Session.GetCollection<UserItem>();
    public DBCollection<UserMagic> UserMagics => Session.GetCollection<UserMagic>();
    public DBCollection<UserQuest> UserQuests => Session.GetCollection<UserQuest>();
    public DBCollection<BuffInfo> Buffs => Session.GetCollection<BuffInfo>();
    public DBCollection<GuildInfo> Guilds => Session.GetCollection<GuildInfo>();

    public ZirconDatabaseCatalog(Session session)
    {
        Session = session ?? throw new ArgumentNullException(nameof(session));
    }
}
