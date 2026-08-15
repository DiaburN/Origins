# ORIGINS Source & Provenance Rules

This document defines the allowed external source families for the current `origins-game-v1` integration branch.

## Forbidden

Do **not** use the multipart `WemadeMir2(1).zip` or split archive parts previously uploaded in ChatGPT.

Do not use screenshots as replacement source artwork when the original library asset is available.

## Crystal / Mir2 — maps and character

### `Suprcode/Crystal`
Purpose:
- map/library behaviour reference;
- player movement/frame layout reference;
- `.Lib` decoding/reference conventions.

### `Suprcode/Crystal.Database`
Purpose:
- real map data/reference.

Current Zuma reference maps:
- `Jev/Maps/d501.map` — normal Zuma floor reference;
- `Jev/Maps/d515.map` — final/KingRoom reference.

### Public Mir2 Crystal asset mirrors
Purpose:
- actual graphical `.Lib` source material referenced by the Crystal content pipeline;
- player `CArmour/00.Lib` locomotion source.

Current automation uses public LOMCN/MirFiles mirror paths. Downloaded upstream libraries are local source cache and should not be committed.

## Zircon / Mir3 — GameInter

### `Suprcode/Zircon`
Purpose:
- exact UI class structure;
- `GameScene` window inventory;
- `MainPanel` positions/indices;
- Character/Inventory/Magic/Quest/Menu geometry;
- `.Zl` container/library behaviour.

### Public Zircon patch mirrors
Purpose:
- actual current `.Zl` graphical libraries.

Current UI libraries include:
- `GameInter.Zl`
- `GameInter2.Zl`
- `Interface.Zl`
- `Equip.Zl`
- `Inventory.Zl`
- `MIcon.Zl`
- `QuestIcons.Zl`
- `MiniMapIcon.Zl`
- `CBIcons.Zl`

## Source vs runtime

Upstream `.Lib` / `.Zl` libraries belong in local `.source/` only.

Generated extraction/reference output belongs in local/CI `artifacts/`.

Only approved runtime-ready subsets should eventually be copied into `assets/game/` with provenance metadata.

Never silently substitute another cave/UI family when an expected asset is missing. Mark it missing and investigate the authoritative source instead.
