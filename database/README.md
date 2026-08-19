# ORIGINS DxR Database

ORIGINS-DxR uses the **official pinned Suprcode/Zircon runtime and MirDB model as its only functional database foundation**.

## Authoritative runtime

Pinned upstream commit: `cbf1aa919083bc13fc3f23f93772a8ab8370632d`.

Zircon initializes one `MirDB.Session` with two assemblies:

1. `LibraryCore` — MirDB engine + static/game definitions.
2. `ServerLibrary` — persistent player/server definitions and runtime models.

Runtime layout:

```text
LibraryCore/MirDB            -> DB engine
LibraryCore/SystemModels     -> static definitions -> System.db
ServerLibrary/DBModels       -> persistent definitions -> Users.db
ServerLibrary/Envir/SEnvir   -> server collection wiring
```

## ORIGINS-DxR rules

- Zircon is the single DB engine.
- Zircon is the single server/combat foundation.
- Zircon `System.db` is the canonical starting database.
- Zircon `MagicInfo` is the only active spell-definition model.
- Zircon `UserMagic` is the only persistent player-spell state.
- Zircon `MagicObject` / `[MagicType(...)]` is the only spell execution architecture.
- Active classes are exactly `Warrior`, `Wizard`, `Taoist`, `Assassin`.
- Crystal and Crystal-Monk data, handlers, enums, overlays and database formats are not active in this branch.
- No Archer or Monk rows are introduced while the four-class scope is active.

## Database bootstrap

Use the canonical Zircon database fetchers:

```text
scripts/fetch-zircon-system-db.sh
scripts/fetch-zircon-system-db.ps1
```

They install the candidate Zircon `System.db` without rewriting it. Validate it before ORIGINS-specific changes.

## Magic catalog

`magic/zircon-four-class-magic-types.json` is the source catalog extracted from the pinned Zircon `MagicType` enum. Enum presence alone does not prove a spell is playable; the DB and runtime are verified separately.

## ORIGINS content

Non-magic ORIGINS data may be layered later only through deliberate Zircon-compatible changes. Magic behavior is not replaced by a parallel ORIGINS or Crystal dispatcher.
