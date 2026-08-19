# ORIGINS DxR

Active development line for ORIGINS MOBILE.

## Foundation

ORIGINS-DxR is rebuilt on the pinned official `Suprcode/Zircon` codebase.

- Zircon commit: `cbf1aa919083bc13fc3f23f93772a8ab8370632d`
- Runtime/server/combat: Zircon
- Database/MirDB: Zircon
- Player magic engine: Zircon
- Initial classes: Warrior, Wizard, Taoist, Assassin
- Archer: disabled for current scope
- Monk: disabled for current scope

The previous experimental Crystal migration is not part of this branch. It remains recoverable in dedicated archive branches.

## Interface

The approved ORIGINS GameInter remains the visual/client shell and must be integrated without redesigning or repositioning approved UI pieces.

Consolidated interface source package:

`Origins_GameInter_Navegable_v1.0_MINIMAP_CONTROLES_BAJADOS.zip`

The interface is presentation; Zircon remains authoritative for gameplay, database, combat and spell behavior.

## Database

Canonical Zircon `System.db` is fetched through:

```text
scripts/fetch-zircon-system-db.sh
scripts/fetch-zircon-system-db.ps1
```

Four-class magic source catalog:

`database/magic/zircon-four-class-magic-types.json`

## Architecture

See `docs/ORIGINS_DXR_ARCHITECTURE.md`.

Map/dungeon work remains documented independently in `docs/MAP_ENGINE_V1.md`.
