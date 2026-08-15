# ORIGINS

Web-first action RPG/MMORPG project using classic Mir source material as a technical/content reference while building a new ORIGINS runtime.

## Authoritative working branch

`origins-game-v1`

This branch integrates the currently approved foundations:
- grey Zuma dungeon/map work;
- Crystal player locomotion;
- Zircon desktop GameInter reconstruction;
- Cursor safety/architecture rules;
- source extraction/import tooling.

Historical branches remain preserved as backups and focused research branches.

## Current playable milestone

Build one integrated browser vertical slice:

`STANDARD Zuma floor -> player walk/run -> NORTH transition -> next floor -> KING_ROOM`

with the real Crystal player locomotion and reconstructed Zircon desktop HUD/windows.

No monsters, combat, spells, networking or mobile UI are required for this first integrated slice.

## Locked visual/game rules

- First dungeon family: `zuma_gray`.
- Normal floors reuse one STANDARD architecture.
- STANDARD entry = SOUTH/bottom.
- STANDARD exit = NORTH/top.
- KING_ROOM entry = SOUTH only; NORTH is closed.
- Keep visual, collision and gameplay layers separate.
- Use real source assets when available; do not replace them with generated/redrawn substitutes.
- Selected GameInter family is Zircon, not Crystal.
- Desktop reference first; mobile adaptation later.

## Start here

Developers/Cursor must read:

1. `CURSOR_START_HERE.md`
2. `docs/MASTER_PROJECT_STATE.md`
3. `docs/CURSOR_IMPLEMENTATION_PLAN.md`

Project rules are also enforced from `.cursor/rules/`.

## Important directories

- `apps/game-web/` — integrated playable web client (next implementation target)
- `apps/zircon-ui-reference/` — Zircon reconstruction/reference harness
- `packages/game-core/` — reusable player movement logic
- `packages/map-engine/` — runtime map/collision package destination
- `packages/gameplay/` — floor/room flow destination
- `packages/rendering/` — renderer/camera destination
- `packages/content/` — runtime manifests destination
- `packages/ui/` — Zircon UI runtime bridge destination
- `origins/map-engine/` — preserved map/theme research and room recipes
- `tools/` — Crystal/Zircon importers and extraction utilities
- `scripts/bootstrap_sources.py` — one-command public source bootstrap

## Public source bootstrap

```bash
python3 scripts/bootstrap_sources.py --all
```

This downloads required public source libraries into local `.source/` and writes generated previews/extractions into `artifacts/`. Those folders are intentionally ignored by Git.

Do not use the previous multipart ChatGPT `WemadeMir2(1).zip`.
