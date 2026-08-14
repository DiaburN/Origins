# ORIGINS DECISION LOG

This file records approved project-level decisions. Do not silently reverse these decisions during implementation.

## 2026-08-14 — New game implementation starts from zero

The new ORIGINS dungeon/game runtime is a fresh implementation. Legacy GameInter/client work and chat-upload archives are not the runtime base.

Existing research/importer files already committed in this repository remain valid and must be preserved.

## 2026-08-14 — GitHub is the canonical project source

Repository: `DiaburN/Origins`
Current development branch: `map-engine-v1`

Cursor and ChatGPT work against the same repository. Changes must be incremental and committed.

## 2026-08-14 — Web-first architecture

The first executable client is `apps/web/`.

Reusable simulation/map/gameplay code belongs in `packages/` so a future mobile client can reuse it without depending on browser UI code.

## 2026-08-14 — Preserve before reorganizing

No existing file or folder may be deleted, renamed or moved merely to make the repository look cleaner.

Runtime code is added to the canonical V1 structure while source-analysis/importer material remains available. Any later migration requires explicit owner approval.

## 2026-08-14 — Dungeon V1 has two base rooms

Normal floors reuse one Standard Room geometry.

Standard Room:
- visible SOUTH entry;
- visible NORTH exit;
- NORTH door locks during encounter and opens after clear.

KingRoom:
- visible SOUTH entry only;
- no NORTH exit;
- closed terminal room;
- altar/landmark in upper area;
- boss arena in center.

## 2026-08-14 — First active visual set is zuma_gray only

Do not mix yellow/tan Zuma or assets from another cave/theme into `zuma_gray`.

The approved visual target is the gray-stone vertical Mir/Archero-style dungeon direction validated in the design conversation.

## 2026-08-14 — First milestone is maps only

Before adding characters, monsters, spells, combat, UI or networking, the project must render the Standard Room and KingRoom correctly from real assets with collision/door metadata separated from the visual layer.
