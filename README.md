# ORIGINS DxR

Single active development line for ORIGINS MOBILE.

## Foundation

ORIGINS-DxR uses the pinned official `Suprcode/Zircon` codebase as the only gameplay/runtime/database foundation.

- Zircon commit: `cbf1aa919083bc13fc3f23f93772a8ab8370632d`
- Runtime/server/combat: Zircon
- Database/MirDB: Zircon
- Player/movement/action engine: Zircon
- Player magic engine: Zircon
- Active classes: Warrior, Wizard, Taoist, Assassin
- Archer: disabled for current scope
- Monk: disabled for current scope
- Crystal / Crystal-Monk runtime: not present in this branch

The previous Crystal work remains recoverable only from the archive branches and must not be merged into the active DxR runtime.

## Interface — locked

Use only the restored closed Zircon GameInter reconstruction committed at:

`apps/zircon-ui-reference/`

Its reconstruction/audit tooling is committed at:

`tools/zircon-ui-importer/`

Closed baseline:

- 65/65 GameScene windows
- 15/15 nested/transient windows
- 80/80 total windows
- 2674 + 149 browser-validated controls
- Browser QA PASS
- Visual Review PASS

The UI is presentation only. Dynamic player, magic, item, map, NPC and server data comes from the Zircon runtime/database; it is not duplicated as a second gameplay engine in HTML/JS.

## Database — locked clean Zircon baseline

The clean validated Zircon snapshot is committed directly in this branch:

`database/generated/zircon-system/`

Baseline metadata:

- System version: `2026.08.19.1`
- Collections: 77
- Objects: 26348
- MagicInfo rows: 174
- Snapshot SHA-256: `2E465FE3018A8E25588452C9525487CDB617DC189E1FD31EF17ADC47C30C331F`
- Round-trip import validation: success

`Database/System.db` is regenerated from that committed snapshot with the ORIGINS database importer and then reopened/verified. No Crystal database overlay is applied.

## Magic — Zircon only

Native four-class `MagicType` inventory:

`database/magic/zircon-four-class-magic-types.json`

Catalogued enum entries:

- Warrior: 38
- Wizard: 47
- Taoist: 52
- Assassin: 58
- Total: 195

The canonical DB contains 174 real `MagicInfo` rows. Enum entries without a real DB row are not fabricated. Entries explicitly marked upstream `NOT CODED` or `UNUSED` remain inactive.

A spell is accepted as playable only when the pinned Zircon source provides all three pieces:

`MagicType -> MagicInfo -> registered MagicObject handler`

The Magic window in the restored UI reads the actual `MagicInfo` / `UserMagic` runtime state.

## Validation

`.github/workflows/database-foundation.yml` rebuilds and verifies `System.db`, confirms the rebuilt `MagicInfo` collection against the committed clean Zircon snapshot, and audits four-class runtime-handler coverage.

The Zircon UI reconstruction retains its independent source, Browser QA and Visual Review gates.

## Architecture

See `docs/ORIGINS_DXR_ARCHITECTURE.md`.

Map/dungeon work remains documented independently in `docs/MAP_ENGINE_V1.md`.
