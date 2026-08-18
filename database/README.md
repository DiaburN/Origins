# ORIGINS Database

ORIGINS uses the **official current Suprcode/Zircon runtime** as its database foundation.

## Authoritative runtime

Pinned upstream commit: `cbf1aa919083bc13fc3f23f93772a8ab8370632d` (2026-08-12).

The current Zircon server initializes one `MirDB.Session` with two assemblies:

1. `LibraryCore` — MirDB engine + static/game definitions.
2. `ServerLibrary` — persistent player/server definitions and runtime models.

Runtime layout:

```text
LibraryCore/MirDB            -> DB engine
LibraryCore/SystemModels     -> static definitions -> System.db
ServerLibrary/DBModels       -> persistent definitions -> Users.db
ServerLibrary/Envir/SEnvir   -> server collection wiring
```

## ORIGINS rules

- Zircon remains the single DB engine.
- Zircon remains the single server/combat foundation.
- Crystal database formats are not imported.
- Crystal spell content is mapped into Zircon `MagicInfo` and player spell state stays in Zircon `UserMagic`.
- Spell execution is implemented through Zircon's existing `MagicObject` classes and `[MagicType(...)]` registration. We do not create a second spell engine.
- A Crystal-derived handler is added only when a spell cannot be represented by an existing/derived Zircon `MagicObject`.

## Files

- `zircon-model-manifest.json` — pinned official model trees.
- `zircon-runtime-collections.json` — collections actually wired by the current server.
- `runtime-layout.json` — `System.db` / `Users.db` behavior.
- `magic/execution-profiles.json` — integration audit metadata only; not a second runtime dispatcher.
