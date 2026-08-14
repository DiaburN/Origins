# CURSOR START HERE — ORIGINS MAP ENGINE V1

## Important: this is a NEW build

The dungeon/map system described here is a new ORIGINS implementation and must be built from zero inside this repository. Do not assume any previous ORIGINS client, old GameInter work, chat-upload ZIPs or legacy map prototype is the base.

Repository: `DiaburN/Origins`
Branch for this work: `map-engine-v1`

Before changing code, read:
- `docs/MAP_ENGINE_V1.md`
- `origins/map-engine/themes/zuma/theme.json`
- `origins/map-engine/themes/zuma/rooms/standard-long-01.json`
- `origins/map-engine/themes/zuma/rooms/king-room-01.json`
- `tools/crystal-map-importer/`
- `.github/workflows/extract-zuma.yml`

## Authoritative external sources

Use only these as source/reference material:

1. `Suprcode/Crystal` — Crystal map/library behaviour.
2. `Suprcode/Crystal.Database` — original `.map` files, including Jev maps.
3. `Suprcode/Crystal.MapEditor` — exact rendering/cell behaviour and map-editor conventions.
4. Public Crystal/Mir2 WemadeMir2 libraries fetched by the repository workflow.

Do NOT use any multipart ZIP or other asset archive previously uploaded in ChatGPT.

## Active visual theme

The only active V1 theme is:

`zuma_gray`

Rules:
- gray tiles/shapes only;
- never mix tan/yellow Zuma pieces into gray rooms;
- never mix assets from another dungeon/theme;
- source maps are references for identifying compatible pieces, not geometry that ORIGINS must copy.

## Locked room system

There are only TWO base room geometries for V1.

### A. STANDARD ROOM

Used for every normal floor: `1F`, `2F`, `3F`, etc.

Layout:
- tall portrait room;
- long central playable space;
- closed left/right walls;
- visible SOUTH entrance at bottom center;
- visible NORTH exit door at top center;
- the North door is locked while the encounter is active and opens when the floor is cleared.

Transition rule:
- on F1 the player sees the NORTH door and passes through it;
- on F2 the same transition is represented by the visible SOUTH entry behind the player;
- F2 also has its own NORTH exit;
- this repeats until KR.

Normal floors reuse the same Standard Room base. Variation comes only from safe decoration/obstacle placement, not from changing the base architecture.

### B. KINGROOM

Final room only.

Layout:
- visible SOUTH entrance at bottom center;
- NO north exit;
- top wall fully closed;
- left/right walls closed;
- bottom wall closed except for the South entrance;
- gray Zuma altar/shrine/ritual architecture in the upper area;
- open central boss arena.

KR is terminal. There is no next-room trigger.

## Visual target

The approved direction is a polished gray-stone Mir-style room with an Archero-like vertical composition:
- strong readable perimeter;
- rich Mir/Zuma gray stone detail;
- floor remains visually clean enough for combat readability;
- obstacles/pillars are sparse and deliberate;
- Standard Room feels like a dungeon floor;
- KingRoom feels like the same dungeon but more ceremonial/final.

Do not redesign this into a different art style.

## Phase 01 — first implementation task

Build a REAL asset-based web preview from the extracted `zuma_gray` pieces. Do not generate a fake full-room image and call it implemented.

Target output:

1. `ZUMA_GRAY_STANDARD_ROOM_01`
2. `ZUMA_GRAY_KING_ROOM_01`

The preview must be composed from real extracted map assets/shapes and room data.

For the first proof, keep implementation minimal and inspectable:
- browser runnable;
- separate visual layer from collision/gameplay metadata;
- no player, monsters, spells, UI or combat yet;
- no unrelated systems;
- no premature architecture rewrite.

Suggested project location:

`origins/web-map-prototype/`

Expected minimum output:
- `index.html`
- JS/TS room renderer
- theme/room JSON loader
- asset loader
- Standard/KR toggle
- optional collision debug toggle

## Source extraction

The existing GitHub Action already downloads the required public sources and produces the Zuma extraction/reference artifact. Reuse/fix that pipeline rather than asking the user to provide local Crystal data.

The current map parser/render work already supports the Mir2 2010 data used for the Zuma references. Preserve exact 48x32 cell conventions and Crystal-style source indexing.

## Development rules

- Work incrementally.
- Do not delete working importer/reference code just to reorganize it.
- Do not add characters/combat before the two rooms render correctly.
- Do not mix visual variants.
- Do not hardcode random asset IDs without documenting source library + image index.
- Keep room geometry, visual theme, collision and gameplay markers separate.
- Every reusable shape should eventually retain: `shape_id`, `theme_id`, `source_map`, `source_library`, `source_image`, role, anchor/size and collision.

## First success criterion

Opening the web prototype must allow us to visually inspect:

- one Standard `zuma_gray` floor with SOUTH entrance + NORTH exit;
- one `zuma_gray` KingRoom with SOUTH entrance only + closed North wall + altar area;
- both visibly belonging to exactly the same gray dungeon family.

Stop there for visual approval before adding gameplay.
