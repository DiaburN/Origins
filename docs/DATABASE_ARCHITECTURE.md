# ORIGINS database architecture

## Verified Zircon runtime

ORIGINS follows the database path that the current Zircon server actually loads, not the older duplicate model project.

`SEnvir.LoadDatabase()` creates `Session(SessionMode.Users)`, then initializes it with:

- the assembly containing `ItemInfo` -> **LibraryCore**
- the assembly containing `AccountInfo` -> **ServerLibrary**

Therefore the ORIGINS database foundation is:

```text
LibraryCore/MirDB            -> database engine
LibraryCore/SystemModels     -> static/game definitions
ServerLibrary/DBModels       -> persistent/player definitions
ServerLibrary/Envir/SEnvir   -> runtime collection wiring
```

The upstream top-level `MirDB/SystemModels` tree is retained only as a legacy/reference path and must not be treated as the current server runtime source.

## Static/game definitions

The current LibraryCore model set includes items, monsters, maps, regions, NPCs, drops, respawns, safe zones, magic, quests, stores, currencies, sets, instances, companions, events, castles, mining, base stats and weapon-craft stats.

## Persistent/player definitions

ServerLibrary DB models include accounts, characters, inventory, user item stats, `UserMagic`, buffs, guilds, mail, auctions, quests, currencies, belts, auto-potions, companions, conquest data and other player/server state.

## Crystal magic integration

Crystal remains a spell content/behaviour reference, never a second database engine.

- `MagicInfo` = authoritative spell definition.
- `UserMagic` = authoritative learned/player spell state.
- `MagicExecutionProfile` = optional ORIGINS metadata describing execution differences only.

Resolution rule:

1. No profile -> execute Zircon native behaviour.
2. Generic profile -> ORIGINS adapter executes with Zircon combat primitives.
3. `SpecialHandler` -> one isolated handler is adapted/ported after the Crystal call path is verified.

We do not duplicate levels, costs, icon, class or base power in the execution profile; those remain in `MagicInfo`.
