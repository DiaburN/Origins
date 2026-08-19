# ORIGINS-DxR database architecture

## Locked source

ORIGINS-DxR is pinned to official `Suprcode/Zircon` commit `cbf1aa919083bc13fc3f23f93772a8ab8370632d` from 2026-08-12.

The current upstream projects target .NET 10.0, so `Origins.Database` targets .NET 10.0 as well.

## Runtime split

`SEnvir.LoadDatabase()` creates the Zircon MirDB session and initializes it with the assemblies containing `ItemInfo` (`LibraryCore`) and `AccountInfo` (`ServerLibrary`).

```text
LibraryCore/MirDB            -> DB engine
LibraryCore/SystemModels     -> System.db definitions
ServerLibrary/DBModels       -> Users.db definitions
ServerLibrary/Envir/SEnvir   -> live server wiring
```

The server reads `System.db` and writes persistent player state to `Users.db`. ORIGINS tooling may inspect/export these structures but must preserve the Zircon schema and index relationships.

## Database domains

The pinned official source already models the domains ORIGINS needs: maps, dungeons/instances, items/stats/sets, monsters/drops/respawns, NPCs, quests, stores/currency, magic, guilds, accounts/characters/inventory, buffs, companions, disciplines, fishing, events, castles, milestones, loot boxes and persistent user state.

We extend these models only where future ORIGINS gameplay genuinely requires a new field. We do not rebuild them in a parallel SQL/JSON runtime schema.

## Native magic architecture

`MagicInfo` is the authoritative spell definition and `UserMagic` is the authoritative learned-spell state.

The active execution path is the one already provided by Zircon:

```text
MagicInfo / UserMagic
        -> MagicType
        -> MagicObject
        -> concrete class marked [MagicType(MagicType.X)]
        -> MagicCast / delayed actions / MagicComplete / buffs / damage
```

`SEnvir.CreateMagic()` discovers concrete Zircon `MagicObject` classes carrying `MagicTypeAttribute`.

ORIGINS-DxR does not add a translation dispatcher or external spell behavior layer. The initial target is faithful reconstruction of the native Warrior, Wizard, Taoist and Assassin spell set present in the canonical Zircon DB/runtime.

Source enum coverage, DB presence and runtime-handler presence are validated as separate gates so an enum-only or upstream `NOT CODED` entry is never presented as a completed spell.
