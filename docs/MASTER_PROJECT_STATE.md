# ORIGINS — MASTER PROJECT STATE

Authoritative integration branch: `origins-game-v1`

This document is the current source of truth for the playable ORIGINS prototype. Cursor, Codex, human developers and future automation must read this file before implementing runtime changes.

## 1. Working model

GitHub is the project master. Chat conversations are not implementation sources.

Historical development branches are preserved and must not be deleted:
- `map-engine-v1`
- `character-movement-v1`
- `zircon-ui-v1`
- `crystal-ui-v1` (reference only; Crystal GameInter is no longer the selected UI)

All new integrated work belongs on `origins-game-v1` until a later milestone explicitly replaces it.

## 2. Locked product direction

### World / dungeon
- Web first, mobile adaptation later.
- Dungeon flow inspired by Archero: elongated vertical combat rooms.
- First theme: `zuma_gray`.
- Use a single coherent grey Zuma visual language. Do not mix unrelated cave themes.
- Normal floors reuse one STANDARD room architecture.
- Standard floor entry: SOUTH/bottom.
- Standard floor exit: NORTH/top.
- When entering F2/F3/etc., the SOUTH entrance remains visually readable behind the player.
- KING_ROOM has only the SOUTH entrance and a closed perimeter; no NORTH progression door.
- KING_ROOM may use a same-theme landmark/altar/boss focal area.
- Gameplay, collision and visual layers remain separate.

### Character
- Crystal/Mir locomotion is the source reference for the player body.
- 8 directions: N, NE, E, SE, S, SW, W, NW.
- Idle/Standing: 4 frames per direction.
- Walk: 6 frames per direction.
- Run: 6 frames per direction.
- Walk = 1 logical cell.
- Run = 2 logical cells with intermediate collision checks.
- Grid/collision position is authoritative; rendering is smoothly interpolated.
- On a floor transition the player spawns just inside SOUTH, facing NORTH.
- Do not implement combat animation by inventing frame layouts. Attack/spell/hit/death are later states layered onto the same state machine.

### Game interface
- Selected UI reference: `Suprcode/Zircon`, not Crystal GameInter.
- Reconstruct Zircon desktop UI first from actual `.Zl` assets and source-code positions.
- Do not redraw or generate replacements for Zircon UI during reconstruction.
- Dynamic labels/numbers remain runtime text.
- Relevant Zircon UI sources include `GameInter.Zl`, `Interface.Zl`, `GameInter2.Zl`, `MIcon.Zl`, `MiniMapIcon.Zl`, etc.
- Main Zircon HUD source is `Client/Scenes/Views/MainPanel.cs`, using `GameInter #50` as the main panel.
- Current Zircon third resource bar is Focus (`FP` / `Stat.Focus`). ORIGINS has not yet locked its final gameplay meaning. Do not rename or remove it in the desktop reference reconstruction without approval.

## 3. Authoritative external sources

### Crystal / Mir2
- `Suprcode/Crystal` — parser, movement/frame and client implementation reference.
- `Suprcode/Crystal.Database` — map database/reference, including `Jev/Maps/d501.map` and `d515.map`.
- Public Mir2 Crystal asset mirrors (MirFiles/LOMCN) — source graphics libraries.

### Zircon / Mir3
- `Suprcode/Zircon` — exact current UI class structure, positions and library indices.
- Public Zircon patch mirrors (MirFiles/LOMCN) — `.Zl` UI libraries.

### Forbidden source
- Do not use the multipart `WemadeMir2(1).zip` previously uploaded in ChatGPT.
- Do not use screenshots as source artwork when the corresponding original library asset exists.

## 4. Repository layers

### `origins/`
Research/content recipes and map-theme metadata. Preserve it.

### `packages/`
Reusable runtime logic. Currently contains player movement under `packages/game-core`.

### `apps/zircon-ui-reference/`
A reconstruction/reference harness. It is not the final ORIGINS game runtime.

### `apps/game-web/`
Reserved for the integrated playable ORIGINS web client. Cursor will implement the first runtime here.

### `tools/`
Importers/extractors. Tools are source pipeline code, not runtime code. Do not delete them after extraction.

### `.source/`
Local-only downloaded source libraries. Must not be committed by default.

### `artifacts/`
Generated previews/extracted assets for local validation or CI artifacts. Do not treat generated output as canonical source.

### `assets/game/`
Approved runtime-ready assets copied/normalized from the extraction pipeline. This should contain only what the playable game actually needs.

## 5. Current implemented foundations

### Map
- Crystal Mir map readers/import tools.
- Zuma map recipes and source report.
- STANDARD and KING_ROOM templates.
- Public-source automated extraction workflow.

### Movement
- `CharacterMovementController`.
- 8-way direction helpers.
- Crystal locomotion animation profile and resolver.
- real Crystal `CArmour/00` extraction tool/workflow.

### UI
- Zircon `.Zl` extractor.
- Zircon UI public-source workflows.
- Navigable desktop UI reference harness.
- MainPanel, Character, Inventory, Magic, Quest and Menu reconstruction foundation.

## 6. Not yet considered complete

Do not claim the following are finished yet:
- final STANDARD room runtime renderer;
- final KING_ROOM runtime renderer;
- collision integration between room recipes and movement;
- actual player sprite layering inside the final web runtime;
- complete Zircon `GameScene` window set;
- mobile-adapted interface;
- monsters/combat/spells/networking/server.

## 7. Development safety

- Never delete, move or rename existing files merely to reorganize the repository.
- Never replace working modules with a new framework without explicit approval.
- Add new code in the documented destination and integrate incrementally.
- Keep source/importer/reference/runtime concerns separated.
- Prefer small, reversible commits.
- Every implementation task must finish with a changed-files summary and test result.

## 8. Next integrated milestone

Build one browser-playable vertical slice in `apps/game-web` that combines:
1. the approved grey Zuma room;
2. the real Crystal player locomotion;
3. collision and SOUTH/NORTH transition logic;
4. the reconstructed Zircon desktop HUD;
5. clickable Zircon Character, Inventory, Magic, Quest and Menu windows.

No monsters, combat, spells or mobile adaptation are required for this first integrated slice.
