# ORIGINS magic source workflow

ORIGINS does **not** import the Crystal database engine.

Magic research uses three distinct sources:

1. **Zircon current runtime/database** — authoritative ORIGINS schema and execution engine.
2. **Crystal current source** — base playable spell catalogue, default `MagicInfo` values and server call paths.
3. **Crystal.Database/Jev + Crystal-Monk** — configured spell values and selected extra/secret skills; read only and never used as the ORIGINS DB format.

## Active ORIGINS spell scope

The active playable spell catalogue contains **119 spells across five classes**:

- Warrior: 21
- Wizard: 28
- Taoist: 27
- Assassin: 19
- Archer: 24

The nine Crystal-Monk Monk skills are retained only under `deferredClasses.Monk` in `crystal-playable-spells.json`. Monk is **not** an active ORIGINS class because its nine-skill source kit is materially incomplete compared with the other classes.

`FastMove` remains a source stub: the pinned Crystal source exposes neither usable `MagicInfo` nor a server handler, so ORIGINS does not invent runtime behavior for it.

## Runtime policy

The comparison against Zircon is deliberately conservative. An identical spell name is never enough to declare compatibility. Each spell is checked against its Crystal server call/completion path and then either mapped to an existing Zircon `MagicObject`, adapted through an override, or implemented through a small Zircon-compatible runtime hook.

Player map-event/custom spell IDs are excluded from the playable catalogue. Crystal-Monk extra skills are included only when they belong to one of the five active classes.

The full numeric `System.db` projection is intentionally separate from source/runtime porting. `database/overlays/70-magics-crystal.json` must not be populated with the complete 119-spell set until the pending runtime patches have been applied and compiled against the pinned Zircon source.

Authoritative audit files:

- `crystal-playable-spells.json` — active/deferred source catalogue.
- `behavior-decisions.json` — manifest for per-class behavior decisions.
- `activation-status.json` — compiled vs source-ported vs source-stub status.
- `final-119-spell-audit.md` — final cross-check and outstanding gates.
