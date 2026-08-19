# ORIGINS DxR Database

ORIGINS-DxR uses Zircon as the only database/runtime foundation.

## Active source

The committed canonical snapshot is:

`database/generated/zircon-system/`

It is the clean Zircon `System.db` export validated by round-trip import on 2026-08-19:

- system version: `2026.08.19.1`
- collections: `77`
- objects: `26348`
- snapshot SHA-256: `2E465FE3018A8E25588452C9525487CDB617DC189E1FD31EF17ADC47C30C331F`
- import result: success

The runtime binary is regenerated from that snapshot with `Origins.Database.Import`; it is not rebuilt from any Crystal overlay.

## Active classes

Only these classes are active for the current game phase:

- Warrior
- Wizard
- Taoist
- Assassin

Archer and Monk are out of scope for this branch.

## Magic source

Magic data comes only from native Zircon:

- `LibraryCore/Enum.cs` -> `MagicType`
- `Library.SystemModels.MagicInfo` -> names, levels, cost, cooldown, power, school, property, icon and description
- `ServerLibrary/Models/Magics/**` -> runtime handlers
- `UserMagic` -> learned spell state

The clean `MagicInfo` collection is committed at:

`database/generated/zircon-system/LibraryCore__Library_SystemModels_MagicInfo.json`

No Crystal magic overlay, Crystal handler, Crystal numeric projection or Crystal database migration is permitted in Origins-DxR.

## Build runtime System.db

After bootstrapping the pinned Zircon source:

```bash
dotnet run --project tools/Origins.Database.Import/Origins.Database.Import.csproj -- \
  database/generated/zircon-system \
  Database
```

Then verify it:

```bash
dotnet run --project tools/Origins.Database.Verify/Origins.Database.Verify.csproj -- ./Database ./Backup
```

The generated runtime file is `Database/System.db`.

## Editing policy

Do not edit the canonical Zircon snapshot in place just to change game content. Future ORIGINS-native changes belong in explicit ORIGINS overlays or later native code/database changes, while the clean snapshot remains the recovery baseline.
