# ORIGINS magic source workflow

ORIGINS does **not** import the Crystal database engine.

Magic research uses three distinct sources:

1. **Zircon current runtime/database** — authoritative ORIGINS schema and execution engine.
2. **Crystal current source** — `Spell` enum, default `MagicInfo` values and server call paths.
3. **Crystal.Database/Jev** — optional configured spell-value source; read only and never used as the ORIGINS DB format.

Generated source catalog:

```text
Suprcode/Crystal @ pinned commit
 -> Shared/Enums.cs::Spell
 -> Envir.FillMagicInfoList()
 -> Envir.UpdateMagicInfo()
 -> crystal-source-catalog.json
```

The comparison against Zircon is deliberately conservative. An identical spell name produces only `name_match_needs_behavior_check`; it is **not** automatically marked compatible. Unmatched Crystal names are not automatically added to `MagicInfo`.

Player map-event spell IDs are excluded from MagicDialog. Archer spells remain catalogued but deferred because current Zircon exposes only Warrior, Wizard, Taoist and Assassin player classes. Crystal custom spells are retained as candidates and reviewed one by one.

Only after a spell has a verified behavior decision may `database/overlays/70-magics-crystal.json` be changed.
