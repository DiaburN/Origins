# ORIGINS GAME ARCHITECTURE V1

This file defines the canonical project layout for the new ORIGINS implementation.

The project is web-first and must remain portable so a mobile client can reuse the same game-core/content later.

## Canonical repository layout

```text
Origins/
├── .cursor/
│   └── rules/                  # Persistent Cursor project rules
├── apps/
│   └── web/                    # Browser client / playable prototype
│       ├── public/
│       └── src/
│           ├── app/            # bootstrap, routing, scene startup
│           ├── game/           # web integration of reusable game packages
│           └── styles/
├── packages/
│   ├── game-core/              # reusable simulation/state/timing, no UI
│   ├── map-engine/             # rooms, cells, collision, doors, map rendering contracts
│   ├── gameplay/               # floor progression, encounters, dungeon flow
│   ├── content/                # typed game definitions/manifests
│   ├── rendering/              # renderer abstractions/adapters
│   └── shared/                 # small shared types/utilities only
├── assets/
│   ├── source/                 # referenced/extracted source assets; immutable where possible
│   └── game/                   # approved runtime-ready assets
│       └── dungeons/
│           └── zuma_gray/
│               ├── floor/
│               ├── walls/
│               ├── doors/
│               ├── pillars/
│               ├── obstacles/
│               ├── decorations/
│               └── kingroom/
├── origins/
│   └── map-engine/             # current source-analysis/theme recipes; keep intact during migration
├── tools/
│   └── crystal-map-importer/   # asset/map extraction and reference rendering tools
├── tests/                      # cross-package automated tests
└── docs/                       # architecture, decisions, implementation notes
```

## Important migration rule

`origins/map-engine/` and `tools/crystal-map-importer/` already contain valid work from the map research/extraction phase. They must NOT be deleted or rewritten just to match the final runtime tree.

Runtime code should be added under `packages/` and `apps/web/` while the current research/source material remains available as provenance and tooling.

Only move existing material later if the owner explicitly approves a dedicated migration.

## Package responsibilities

### `apps/web`
The executable/browser-facing application. It composes the packages but should not own core dungeon rules.

### `packages/game-core`
Generic game loop/state/timing primitives that should be reusable by web and future mobile clients.

Must not import DOM-specific APIs.

### `packages/map-engine`
Owns:
- cell/grid representation;
- room geometry;
- floor/wall/door placement;
- collision data;
- map markers;
- map runtime state;
- NORTH/SOUTH transition contracts;
- theme validation.

It does NOT own monsters, combat balancing or UI.

### `packages/gameplay`
Owns:
- dungeon floor sequence;
- encounter start/clear state;
- locking/unlocking the NORTH door;
- spawning into the SOUTH entrance on the next floor;
- terminal KingRoom behavior.

### `packages/content`
Declarative data and schemas:
- dungeon definitions;
- room recipes;
- theme manifests;
- later monsters/items/spells.

No renderer logic.

### `packages/rendering`
Draws runtime map data. Keep renderer-specific code separate from map/gameplay data.

### `packages/shared`
Only truly generic shared types/helpers. Do not turn this into a miscellaneous dumping ground.

## Locked Dungeon V1 rules

Active theme: `zuma_gray` only.

### Standard Room
One standard geometry is reused for all normal floors.

- portrait / long vertical room;
- SOUTH visible entrance at bottom center;
- NORTH visible exit at top center;
- left/right perimeter closed;
- NORTH door locks during encounter and opens after clear;
- floor-to-floor transition: NORTH exit of previous floor becomes visible SOUTH entry of the next floor;
- visual variation is allowed only through compatible gray floor details, obstacles, pillars and decoration.

### KingRoom
One terminal KingRoom geometry.

- SOUTH entrance only;
- NO NORTH exit;
- full perimeter closed except SOUTH entrance;
- gray altar/landmark in upper area;
- central boss arena;
- same `zuma_gray` visual family only.

## Asset rules

Every runtime dungeon asset must have provenance and theme metadata.

Never mix:
- `zuma_gray` with tan/yellow Zuma;
- Zuma with another dungeon;
- unrelated Crystal/Mir asset families because they happen to fit geometrically.

Prefer runtime manifests over hardcoded file paths scattered throughout code.

## Change-management rules

- Additive/incremental development first.
- No broad refactors during feature implementation.
- No deletion/rename/move without explicit approval.
- No duplicate engine implementations.
- Every substantial architecture decision goes into `docs/DECISIONS.md`.
- Every completed milestone should leave the project runnable.

## First implementation milestone

Build only:
1. minimal `apps/web` runnable shell;
2. reusable `packages/map-engine` skeleton;
3. `zuma_gray` theme manifest;
4. one Standard Room runtime scene;
5. one KingRoom runtime scene;
6. collision + NORTH/SOUTH door state;
7. simple developer toggle to preview Standard vs KingRoom.

Do NOT add characters, monsters, spells, inventory, UI systems or networking during this milestone.
