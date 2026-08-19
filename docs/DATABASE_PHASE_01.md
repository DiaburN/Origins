# Database Phase 01 — Zircon Foundation

Status: active.

## Completed

- Pinned official `Suprcode/Zircon` at `cbf1aa919083bc13fc3f23f93772a8ab8370632d` (2026-08-12).
- Matched ORIGINS-DxR to Zircon's current .NET 10 target.
- Locked `LibraryCore/MirDB`, `LibraryCore/SystemModels`, `ServerLibrary/DBModels`, and the real `SEnvir.LoadDatabase()` wiring.
- Added typed access to core DB domains.
- Added `System.db` preflight checks.
- Added CI builds against the exact upstream commit.
- Added a read-only verifier CLI for candidate `System.db` files.
- Added scripts to fetch/extract the canonical Zircon `Database.7z` into the local ignored `Database/` folder.
- Locked the active spell foundation to Zircon `MagicType` + `MagicInfo` + `MagicObject` + `UserMagic`.
- Limited the current player-class scope to Warrior, Wizard, Taoist and Assassin.

## Population order

1. canonical Zircon `System.db`
2. base stats + movement
3. maps + regions + safe zones + dungeons/instances
4. monsters + drops + respawns
5. NPCs + stores
6. quests
7. native four-class magic verification
8. sets/equipment and remaining static systems
9. persistent/user DB verification

## Gate

Before using a downloaded or migrated `System.db`:

```bash
dotnet run --project tools/Origins.Database.Verify/Origins.Database.Verify.csproj -- ./Database
```

Do not seed fake placeholders merely to satisfy startup checks. A candidate database must pass against the pinned current Zircon assemblies before ORIGINS-DxR treats it as a usable base.
