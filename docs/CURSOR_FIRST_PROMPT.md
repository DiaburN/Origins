# FIRST PROMPT FOR CURSOR

Use this once Cursor has opened/cloned `DiaburN/Origins`.

---

You are starting a NEW ORIGINS dungeon/map implementation from zero.

1. Make sure the repository is `DiaburN/Origins`.
2. Checkout branch `map-engine-v1`.
3. Read `CURSOR_START_HERE.md` completely before modifying anything.
4. Then inspect:
   - `docs/MAP_ENGINE_V1.md`
   - `origins/map-engine/themes/zuma/theme.json`
   - `origins/map-engine/themes/zuma/rooms/standard-long-01.json`
   - `origins/map-engine/themes/zuma/rooms/king-room-01.json`
   - `tools/crystal-map-importer/`
   - `.github/workflows/extract-zuma.yml`
5. Treat the existing importer/extraction work as reference tooling, not as a finished game client.
6. Do not use old ORIGINS code or ChatGPT-uploaded ZIPs as a base.
7. Use only the active visual variant `zuma_gray`.
8. Build the first real browser preview under `origins/web-map-prototype/`.

The first milestone contains ONLY:
- one Standard Room used for all normal floors;
- one KingRoom;
- real gray Zuma assets/shapes;
- Standard Room: visible SOUTH entry + visible NORTH exit;
- KingRoom: visible SOUTH entry only, closed North wall, gray altar area;
- separate visual/collision/room metadata;
- Standard/KR preview selector;
- no player, monsters, combat, UI, spells or unrelated systems yet.

Do not approximate the room with CSS rectangles if real extracted assets are available. Do not create a generated room image and use it as implementation. The room must be assembled from reusable real assets.

Before writing large amounts of code, first report:
- what files already exist;
- what asset/extraction output is available;
- the minimum files you will create;
- any blocker that prevents a real asset-based preview.

Then implement the smallest working version, run it, and provide the exact local command/URL needed to preview it.

Stop after Standard Room + KingRoom are visually renderable so they can be approved before gameplay work begins.
