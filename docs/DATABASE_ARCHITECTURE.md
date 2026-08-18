# ORIGINS database architecture

## Source of truth

ORIGINS uses Zircon's database split instead of Crystal's database layout.

### Static definitions — Zircon MirDB

Verified upstream models:

- DropInfo
- GuardInfo
- ItemInfo / ItemInfoStat
- MagicInfo
- MapInfo
- MonsterInfo / MonsterInfoStat
- MovementInfo
- NPCInfo
- RespawnInfo
- SafeZoneInfo
- SetInfo / SetInfoStat

### Persistent data — Zircon ServerLibrary/DBModels

Verified upstream models include accounts, characters, auctions, belts, buffs, guilds, mail, refinement, companions, currencies, user drops, user items, UserMagic and UserQuest.

## Crystal magic integration

Crystal is a content/behaviour reference, not a second database engine.

`MagicInfo` remains the spell definition source of truth. `UserMagic` remains the player spell state source of truth. ORIGINS adds an optional `MagicExecutionProfile`, keyed by `MagicInfo.Index`, only for execution differences that Zircon does not already express.

Resolution rule:

1. No execution profile -> run Zircon native magic logic.
2. Profile with a generic execution kind -> run the ORIGINS adapter using Zircon combat primitives.
3. `SpecialHandler` -> call one isolated ORIGINS handler ported/adapted from the verified Crystal behaviour.

This guarantees one database model and one combat engine while allowing Crystal spell variety.
