# CURSOR IMPLEMENTATION PLAN — ORIGINS GAME V1

Branch: `origins-game-v1`

This is the execution order for Cursor. Do not improvise a new architecture and do not start by deleting/reorganizing files.

## Mandatory reading order

1. `.cursor/rules/00-project-safety.mdc`
2. `.cursor/rules/10-game-architecture.mdc`
3. `.cursor/rules/20-origins-runtime-decisions.mdc`
4. `docs/MASTER_PROJECT_STATE.md`
5. `docs/GAME_ARCHITECTURE_V1.md`
6. `docs/MAP_ENGINE_V1.md`
7. `docs/CHARACTER_MOVEMENT_V1.md`
8. `docs/ZIRCON_UI_RECONSTRUCTION.md`
9. this file

If any old document contradicts `MASTER_PROJECT_STATE.md`, the master state wins.

## Goal

Create a local browser-playable ORIGINS vertical slice using the already researched/imported source material. The first goal is integration and validation, not a full MMORPG.

## Phase 0 — Safety and inventory

Before changing code:
- confirm branch is `origins-game-v1`;
- run `git status`;
- inventory existing `apps`, `packages`, `origins`, `tools`, `docs`;
- do not remove anything;
- do not modify reference/importer code unless integration genuinely requires it.

## Phase 1 — Workspace/runtime skeleton

Create the minimum workspace needed to run `apps/game-web`.

Requirements:
- TypeScript.
- Browser runtime.
- Deterministic game update loop separated from rendering.
- Renderer behind an adapter boundary.
- Pin dependency versions and commit the lockfile.
- Do not couple `packages/game-core` to DOM/browser APIs.

Preferred folder responsibilities:

`apps/game-web`
- bootstraps the browser app;
- input adapters;
- scene composition;
- development/debug panel only when useful.

`packages/game-core`
- player state and movement;
- no DOM imports.

`packages/map-engine`
- cells, collision, rooms, doors/transitions.

`packages/rendering`
- sprites/layers/camera/render transforms.

`packages/gameplay`
- floor flow and room transition orchestration.

`packages/content`
- manifests/config data loaded by runtime.

`packages/ui`
- Zircon desktop UI reconstruction/runtime bridge.

Do not move existing `packages/game-core/src/character-movement`; import it from the new workspace.

## Phase 2 — Asset bootstrap

Use public authoritative sources only.

Run:

```bash
python3 scripts/bootstrap_sources.py --all
```

The script should populate local `.source/` and generated `artifacts/` without committing huge upstream libraries.

Required generated material:
- Zuma reference/extracted assets;
- Crystal player locomotion frames;
- Zircon GameInter/Interface/MIcon extracted assets.

Do not use the old ChatGPT multipart ZIP.

## Phase 3 — Map runtime

Implement `packages/map-engine` using the existing room/theme JSON as source content.

For first slice:
- one `STANDARD` room;
- one `KING_ROOM`;
- STANDARD has SOUTH entrance and NORTH exit;
- KING_ROOM has SOUTH entrance only;
- collision mask is separate from visible artwork;
- player cannot pass through walls/pillars/closed doors;
- camera must not shrink the player merely to show the whole room.

Desktop first. Keep camera abstraction ready for mobile portrait later.

## Phase 4 — Player locomotion integration

Use the existing `CharacterMovementController` rather than rewriting it.

Connect:
- input adapter -> movement intent;
- movement controller -> collision query;
- movement snapshot -> renderer;
- animation resolver -> Crystal player frame.

Validate:
- idle all 8 directions;
- walking all 8 directions;
- running all 8 directions;
- blocked movement still turns naturally;
- run cannot skip an intermediate blocked cell;
- standard SOUTH spawn faces NORTH;
- NORTH exit triggers floor transition;
- new floor spawns at SOUTH;
- KING_ROOM has no NORTH transition.

## Phase 5 — Zircon desktop GameInter

Use `apps/zircon-ui-reference` and `tools/zircon-ui-importer` as reference/source pipeline, not as a reason to invent new UI.

First runtime-visible UI:
- MainPanel / `GameInter #50`;
- HP;
- MP;
- Focus (keep as Zircon reference for now);
- EXP;
- Character button;
- Inventory button;
- Magic button;
- Quest button;
- Mail button placeholder/disabled if not implemented;
- Belt toggle;
- Group button placeholder/disabled if not implemented;
- Menu;
- Cash Shop placeholder/disabled if not implemented;
- minimap frame/content;
- chat area/input;
- belt slots.

Clickable windows required in first slice:
- Character (`Interface #110`);
- Inventory (`Interface #130`);
- Magic (`Interface #160-164` structure);
- Quest (`Interface #291+`);
- Menu (`Interface #279`).

Important:
- use real Zircon artwork/geometry;
- labels/numbers are runtime text;
- do not burn ORIGINS-specific dynamic text into PNGs;
- do not mobile-redesign yet.

## Phase 6 — Integrated test scene

The default development route should open one scene containing:
- grey Zuma STANDARD room;
- real Crystal player;
- Zircon desktop HUD;
- movement enabled;
- window buttons functional;
- NORTH/SOUTH room transition demonstration.

Also expose an easy debug switch to enter KING_ROOM.

No monsters are required yet.

## Phase 7 — Verification

Required checks before reporting completion:
- clean fresh install works;
- dev server starts with one documented command;
- no missing asset 404s;
- no console exceptions during normal movement/window toggling;
- no destructive repository changes;
- character does not cross blocked cells;
- transition cycle STANDARD -> next STANDARD works;
- KING_ROOM remains closed at NORTH;
- all first-slice Zircon buttons open/close the correct window.

## Required completion report from Cursor

Return:
1. exact command used to install;
2. exact command used to run;
3. local URL;
4. files created;
5. files modified;
6. confirmation that no unrelated files were deleted/moved/renamed;
7. test results;
8. known remaining issues.

Do not continue into monsters, combat, spells, networking or mobile UI without a new approved task.
