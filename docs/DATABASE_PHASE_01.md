# Database Phase 01 — Foundation

Status: active.

## Completed

- Pinned the official current `Suprcode/Zircon` source at commit `cbf1aa919083bc13fc3f23f93772a8ab8370632d`.
- Matched ORIGINS database project to Zircon's current .NET 10 target.
- Locked the real MirDB engine path (`LibraryCore/MirDB`).
- Locked static models (`LibraryCore/SystemModels`) and persistent models (`ServerLibrary/DBModels`).
- Mirrored the server's real assembly initialization pattern.
- Added typed ORIGINS access for core database domains.
- Added a `System.db` preflight so an empty/incomplete database is rejected before server startup.
- Added CI that installs the exact pinned Zircon revision and builds `Origins.Database`.
- Locked Crystal spell integration to Zircon `MagicObject` instead of a parallel combat engine.

## Next population blocks

Populate/verify in dependency order:

1. currencies + core item definitions
2. base stats + movement
3. maps + regions + safe zones + dungeons/instances
4. monsters + drops + respawns
5. NPCs + stores
6. quests
7. magic definitions (Zircon schema, Crystal catalogue)
8. sets/equipment and remaining systems
9. persistent/user DB verification

Do not seed fake placeholders merely to satisfy startup checks. Each block must use real source data or an explicitly approved ORIGINS replacement.
