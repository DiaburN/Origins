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
- Reconstruct Zircon desktop UI first from actual `.Zl` assets and source-code geometry.
- Do not redraw or generate replacements for Zircon UI during reconstruction.
- Dynamic labels/numbers remain runtime text.
- Relevant Zircon UI sources include `GameInter.Zl`, `Interface.Zl`, `GameInter2.Zl`, `MIcon.Zl`, `MiniMapIcon.Zl`, etc.
- Main Zircon HUD source is `Client/Scenes/Views/MainPanel.cs`, using `GameInter #50` as the main panel.
- Current Zircon third resource bar is Focus (`FP` / `Stat.Focus`). ORIGINS has not yet locked its final gameplay meaning. Do not rename or remove it in the desktop reference reconstruction without approval.
- The desktop reference must retain the **complete Zircon GameScene UI inventory**. Product removals happen only through the ORIGINS decision matrix after review.

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
The complete desktop Zircon GameScene reconstruction/reference harness. It is deliberately kept separate from final ORIGINS product decisions.

### `apps/game-web/`
Reserved for the integrated playable ORIGINS web client. Cursor will implement the playable runtime here.

### `tools/`
Importers/extractors and source analyzers. Tools are source pipeline code, not runtime code. Do not delete them after extraction.

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
- Real Crystal `CArmour/00` extraction tool/workflow.

### UI
- Zircon `.Zl` extractor with DXT1, DXT5, BGRA32, PNG and BC7 decoding required by the current UI data.
- Automatic parser of the current `Suprcode/Zircon` `GameScene` and registered UI source classes.
- Complete GameScene registry: **65/65 source-resolved UI/HUD components** in the validated CI build.
- No missing public UI libraries in the validated complete build.
- Validated complete build extracted **410 real source PNGs** required by the current reference set.
- Searchable/category-based 1024x768 desktop reference harness under `apps/zircon-ui-reference/`.
- Exact image-backed reconstruction foundation for MainPanel and major image-backed dialogs plus source-driven reusable `DXWindow` reconstruction for the rest.
- Complete scope documentation: `docs/ZIRCON_UI_FULL_SCOPE.md`.
- Owner review/removal matrix: `docs/ZIRCON_UI_DECISIONS.md`.

Validated CI reference build:
- workflow: `Build complete Zircon UI reference`
- GameScene source entries: `65`
- source-resolved: `65/65`
- missing public UI libraries: `0`
- extracted PNGs: `410`

## 6. What is and is not considered complete

### Complete as a source/reference foundation
- complete Zircon GameScene component inventory;
- current source-class resolution for every registered GameScene component;
- public `.Zl` dependency extraction for the reference set;
- BC7-capable Zircon UI extraction;
- navigable desktop catalog foundation for reviewing the full interface.

### Still requires visual/product approval or runtime integration
- pixel-level review of every complex source-driven Zircon dialog against its C# runtime behavior;
- final ORIGINS `KEEP / REMOVE / MERGE / MOBILE_REDESIGN / DEFER` decisions;
- final STANDARD room runtime renderer;
- final KING_ROOM runtime renderer;
- collision integration between room recipes and movement;
- actual player sprite layering inside the final web runtime;
- mobile-adapted interface;
- monsters/combat/spells/networking/server.

Do not claim that every dynamic Zircon window behavior has been ported into ORIGINS merely because its source and graphical reference are reconstructed. The reference is intentionally separated from final game implementation.

## 7. Development safety

- Never delete, move or rename existing files merely to reorganize the repository.
- Never replace working modules with a new framework without explicit approval.
- Add new code in the documented destination and integrate incrementally.
- Keep source/importer/reference/runtime concerns separated.
- Prefer small, reversible commits.
- Every implementation task must finish with a changed-files summary and test result.
- Do not remove a Zircon reference window because ORIGINS later chooses not to use it; record that decision in `docs/ZIRCON_UI_DECISIONS.md`.

## 8. Next integrated milestone

Continue validating the complete Zircon desktop reference window-by-window, while preparing the browser-playable vertical slice in `apps/game-web` that combines:
1. the approved grey Zuma room;
2. the real Crystal player locomotion;
3. collision and SOUTH/NORTH transition logic;
4. the reconstructed Zircon desktop HUD;
5. the approved Zircon windows required for the first playable slice.

No mobile redesign should begin until the desktop reference and initial keep/remove decisions are approved.
