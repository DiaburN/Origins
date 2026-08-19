# ORIGINS DxR — Magic

The active magic system is Zircon-only.

## Active classes

- Warrior
- Wizard
- Taoist
- Assassin

No Archer, Monk or Crystal runtime participates in this branch.

## Canonical inputs

1. `database/magic/zircon-four-class-magic-types.json`
   - exact `MagicType` inventory from pinned Zircon source
   - 38 Warrior enum entries
   - 47 Wizard enum entries
   - 52 Taoist enum entries
   - 58 Assassin enum entries
   - 195 enum entries total

2. `database/generated/zircon-system/LibraryCore__Library_SystemModels_MagicInfo.json`
   - exact clean Zircon `MagicInfo` rows from the validated System.db snapshot
   - source for name, icon, description, class, level requirements, experience, costs, delay, power, school and property

3. `ServerLibrary/Models/Magics/**` from pinned Zircon
   - runtime behavior and handlers

4. `UserMagic`
   - per-player learned spell state

## Activation rule

A spell is considered active/playable only when all of the following are true:

- it belongs to Warrior, Wizard, Taoist or Assassin;
- its `MagicType` exists in pinned Zircon;
- a corresponding `MagicInfo` row exists in the clean Zircon snapshot;
- Zircon runtime registers a real handler for that `MagicType`.

Enum-only entries explicitly marked by upstream as `NOT CODED` or `UNUSED` remain catalogued but are not fabricated or replaced.

## UI rule

Use only the restored closed Zircon interface under `apps/zircon-ui-reference/`.

The Magic window keeps its existing Zircon visual behavior and receives its real cells/tabs from runtime `MagicInfo` + `UserMagic`. There is no second spell engine in HTML/JS and there are no Crystal magic trees, Crystal IDs or Crystal spell data.

## Verification

CI must cross-check:

`MagicType -> MagicInfo -> registered MagicObject handler`

and emit the four-class DB/runtime reports before the runtime `System.db` is accepted.
