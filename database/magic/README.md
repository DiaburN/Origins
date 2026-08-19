# ORIGINS magic source workflow

ORIGINS does **not** import the Crystal database engine.

Magic research uses three distinct sources:

1. **Zircon pinned runtime/database** — authoritative ORIGINS schema and execution engine.
2. **Crystal pinned source** — base playable spell catalogue, default `MagicInfo` values and server call paths.
3. **Crystal.Database/Jev + Crystal-Monk** — configured spell values and selected extra/secret skills; read only and never used as the ORIGINS DB format.

## Active ORIGINS spell scope

The active playable spell catalogue contains **119 spells across five classes**:

- Warrior: 21
- Wizard: 28
- Taoist: 27
- Assassin: 19
- Archer: 24

The nine Crystal-Monk Monk skills are retained only under `deferredClasses.Monk` in `crystal-playable-spells.json`. Monk is **not** an active ORIGINS class because its nine-skill source kit is materially incomplete compared with the other classes.

`FastMove` remains the single source stub. The pinned Crystal source exposes no usable `MagicInfo`/server runtime for it, so ORIGINS preserves the identity without inventing data or behavior.

## Current validated runtime/database state

The full five-class spell runtime now applies and compiles against the pinned Zircon revision.

- **118/118 routed active spells** have exactly one verified `MagicObject` handler registration.
- `LibraryCore` + `ServerLibrary` compile together successfully.
- The final active overlay contains **119 MagicInfo operations**.
- **118** rows are bound to real compiled runtime routes.
- `FastMove` is the only disabled source-stub row.
- **0** runtime placeholders remain pending.
- The final System.db projection rebuilds, verifies and passes audit preflight.
- The existing Users.db smoke round-trips account, character and learned `FireBall` successfully against the final System.db.

Final validated generated database from `ORIGINS System DB` run `32308650321`:

- System version: `2026.08.19.1`
- SHA-256: `7df0446b804b6d95b1b192ae3d32570bb9f9ecbb3d5cb3827ca288cbee11cdbb`
- artifact: `origins-system-db`

The generated overlay applies **119 operations: 90 created, 29 updated, 0 deleted**. Runtime activation reuses 27 native Zircon MagicInfo identities and binds 91 routed spells through ORIGINS mappings; FastMove remains the one source-stub row.

## Runtime policy

The comparison against Zircon is deliberately conservative. An identical spell name is never enough to declare compatibility. Each spell is checked against its Crystal server call/completion path and then either mapped to an existing Zircon `MagicObject`, adapted through an override, or implemented through a small Zircon-compatible runtime hook.

Player map-event/custom spell IDs are excluded from the playable catalogue. Crystal-Monk extra skills are included only when they belong to one of the five active classes. Historical Jev rows that do not represent current playable source identities are retained only as audit evidence and never selected into the active overlay by input order.

Compilation and System.db activation do not imply that every spell has completed in-game visual/behavioral smoke testing. Client effects, mobile UI binding, summon-content dependencies and broader per-class gameplay smoke remain separate phases.

Authoritative audit files:

- `crystal-playable-spells.json` — active/deferred source catalogue.
- `behavior-decisions.json` — manifest for per-class behavior decisions.
- `activation-status.json` — compile, runtime-route, database projection and remaining-validation status.
- `final-119-spell-audit.md` — final cross-check, CI evidence and remaining runtime/client gates.
