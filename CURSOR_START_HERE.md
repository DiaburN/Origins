# CURSOR START HERE — ORIGINS GAME V1

Repository: `DiaburN/Origins`
Authoritative branch: `origins-game-v1`

## STOP: read before editing

This branch already integrates the approved map, character-movement and Zircon-UI foundations. Do not search old chats for implementation instructions and do not switch to the historical feature branches to build the game.

Before modifying anything, read in this exact order:

1. `.cursor/rules/00-project-safety.mdc`
2. `.cursor/rules/10-game-architecture.mdc`
3. `.cursor/rules/20-origins-runtime-decisions.mdc`
4. `docs/MASTER_PROJECT_STATE.md`
5. `docs/CURSOR_IMPLEMENTATION_PLAN.md`
6. `docs/GAME_ARCHITECTURE_V1.md`
7. `docs/MAP_ENGINE_V1.md`
8. `docs/CHARACTER_MOVEMENT_V1.md`
9. `docs/ZIRCON_UI_RECONSTRUCTION.md`

If an older document conflicts with `docs/MASTER_PROJECT_STATE.md`, the master state wins.

## Repository safety

Do not delete, rename, move, replace or broadly refactor existing project files/folders without explicit owner approval.

Do not clean up `origins/`, `tools/`, reference apps or old documentation merely because the new runtime uses other folders. They preserve source provenance and working research.

Do not commit `.source/`, generated `artifacts/`, upstream `.Lib` files or upstream `.Zl` files.

## What this project currently uses

### Dungeon/map
- coherent grey Zuma family (`zuma_gray`);
- STANDARD room for all normal floors;
- SOUTH entrance + NORTH exit;
- KING_ROOM has SOUTH entrance only and a closed NORTH wall.

### Character
- existing `packages/game-core/src/character-movement` controller;
- Crystal/Mir 8-direction locomotion;
- standing + walk + run;
- exact source frame/offset logic;
- do not rewrite the controller just because a framework offers its own movement helper.

### Interface
- Zircon desktop UI is the selected GameInter family;
- use exact `.Zl` source assets and Zircon source-code geometry/indices;
- Crystal GameInter is no longer the selected UI;
- keep Zircon Focus/FP in the desktop reconstruction until the owner decides its final ORIGINS function;
- do not redesign for mobile yet.

## Sources

Allowed:
- `Suprcode/Crystal`
- `Suprcode/Crystal.Database`
- public Mir2 Crystal asset mirrors
- `Suprcode/Zircon`
- public Zircon patch mirrors

Forbidden:
- previous multipart ChatGPT `WemadeMir2(1).zip`
- generated replacement UI/map art when original source assets exist

## First task

Follow `docs/CURSOR_IMPLEMENTATION_PLAN.md` and build the integrated runtime in `apps/game-web`.

The first playable scene must combine:
- grey Zuma STANDARD room;
- real Crystal player idle/walk/run;
- deterministic collision;
- NORTH floor transition and SOUTH next-floor spawn;
- Zircon desktop MainPanel;
- Character, Inventory, Magic, Quest and Menu windows.

Also provide a debug route/switch for KING_ROOM.

Do not implement monsters, combat, spells, networking or mobile UI in this task.

## Source bootstrap

Run:

```bash
python3 scripts/bootstrap_sources.py --all
```

This uses public sources and produces local generated assets/reference material.

## Completion contract

When finished, report:
- install command;
- run command;
- local URL;
- files created;
- files modified;
- tests performed/results;
- known issues;
- explicit confirmation that no unrelated existing file was deleted/moved/renamed.

Stop after the integrated vertical slice is runnable and await visual/gameplay review.
