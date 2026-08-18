# ORIGINS database architecture

## Locked source

ORIGINS is pinned to the official `Suprcode/Zircon` commit `cbf1aa919083bc13fc3f23f93772a8ab8370632d` from 2026-08-12.

The current upstream projects target .NET 10.0, so `Origins.Database` targets .NET 10.0 as well.

## Runtime split

`SEnvir.LoadDatabase()` creates `Session(SessionMode.Users)` and initializes it with the assemblies containing `ItemInfo` (`LibraryCore`) and `AccountInfo` (`ServerLibrary`).

```text
LibraryCore/MirDB            -> DB engine
LibraryCore/SystemModels     -> System.db definitions
ServerLibrary/DBModels       -> Users.db definitions
ServerLibrary/Envir/SEnvir   -> live server wiring
```

The server reads `System.db` and writes persistent player state to `Users.db`. ORIGINS tooling may use `SessionMode.Both` when editing both sides.

The current `Session` also versions `System.db` through `SystemDatabaseInfo` and avoids unnecessary rewrites when there are no changes.

## Database domains now present upstream

The current official source already models the domains ORIGINS needs: maps, dungeons/instances, items/stats/sets, monsters/drops/respawns, NPCs, quests, stores/currency, magic, guilds, accounts/characters/inventory, buffs, companions, disciplines, fishing, events, castles, milestones, loot boxes and persistent user state.

We extend these models only where ORIGINS gameplay genuinely requires new fields. We do not rebuild them in a parallel SQL/JSON schema.

## Crystal spells

`MagicInfo` remains the authoritative spell definition and `UserMagic` remains the authoritative learned spell state.

The current Zircon server already has an extensible spell runtime:

```text
MagicInfo / UserMagic
        -> MagicType
        -> MagicObject
        -> concrete class marked [MagicType(MagicType.X)]
        -> MagicCast / delayed actions / MagicComplete / buffs / damage
```

`SEnvir.CreateMagic()` discovers concrete `MagicObject` classes carrying `MagicTypeAttribute`. Therefore ORIGINS will integrate Crystal spell behaviour inside this native mechanism instead of creating a second handler/dispatcher engine.

For each Crystal spell:

1. Reuse an existing Zircon `MagicObject` unchanged when behaviour matches.
2. Adapt/derive a Zircon handler when behaviour is close.
3. Port only the missing Crystal behaviour into a new Zircon `MagicObject` when necessary.

The JSON execution-profile file is only an audit map recording which decision was made; it is not runtime combat logic.
