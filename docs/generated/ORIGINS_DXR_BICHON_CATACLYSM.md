# ORIGINS-DxR — Bichon Town (0.map) Cataclysm Hub

- Gate: **PASS**
- Origins-DxR HEAD tested: `197c75f231afafe3f41fbfd28a62a1dc9f7648c0`
- Zircon authority: `cbf1aa919083bc13fc3f23f93772a8ab8370632d`
- Source MapInfo: **Index 1 / FileName `0` / Bichon Town**
- Native dimensions: **350 × 350 cells**
- Source SHA-256: `048F2E89ADEB51EB164E2D38852659802BAE5800974876460B3187FF5AB87EC7`
- ORIGINS map SHA-256: `83C6D36556576FDFFFA343892F3205BF31BEE5C3AFEF81293D15A591728978A8`

## Cataclysm geometry

- Official `Town Area` cells preserved: **6275**.
- `Town Area` bbox: `{'x0': 122, 'y0': 156, 'x1': 237, 'y1': 278, 'width': 116, 'height': 123}`.
- Preserve box including native walls/context: `{'x0': 116, 'y0': 150, 'x1': 243, 'y1': 284, 'width': 128, 'height': 135}`.
- Promenade width: **12 cells** beyond the preserve box.
- Coast variation: **±2 cells** at native 2×2 BackTile granularity.
- Zone cell counts: `{'sea': 98680, 'promenade': 6668, 'preserve': 17152}`.

## Native Zircon tiles

- Promenade: `BackFile=1` → `Tiles30c`, `BackImage=758`.
- Promenade selection: dominant non-empty passable ground already used inside Bichon `Town Area`.
- Sea: `BackFile=1` → `Tiles30c`, `BackImage=720`.
- Sea selection: dominant blocked perimeter BackTile sampled from official Zircon maps `1` and `7`; no generated art.

## Native binary / collision guarantees

- Back blocks changed: **24176**.
- Cell records changed: **105348**.
- Original passable cells: **88250**.
- Modified passable cells: **20799**.
- Ocean cells have Zircon movement bits cleared, so the **server blocks movement over water**.
- Promenade cells have Zircon movement bits enabled and Middle/Front clutter removed.
- Width/height, 28-byte header and total binary length are preserved.
- Everything inside the preserve box is left byte-for-byte as in official Bichon.

## Intent

- Bichon is the permanent ORIGINS social/hub city.
- The fortified central city survives the catastrophe.
- Outside the native wall context is a walkable promenade; everything beyond it is ocean.
- Future dungeon/world access comes from a central teleport hub, not overland province exits.

## Next validation boundary

- Native structure/collision is proven here. Real Zircon `.Zl` rendering is the next visual gate before NPC/teleport placement.
