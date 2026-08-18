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
- The source-faithful Zircon desktop reconstruction is **closed and locked as the baseline**.
- Validated desktop baseline SHA: `a3eba357359f1ce95f97020ae68d27792174c8da`.
- Reconstruct/verify Zircon desktop UI from actual `.Zl` assets and source-code geometry; do not redraw or generate replacements inside the reference harness.
- Dynamic labels/numbers remain runtime text.
- Relevant Zircon UI sources include `GameInter.Zl`, `Interface.Zl`, `GameInter2.Zl`, `MIcon.Zl`, `MiniMapIcon.Zl`, etc.
- Main Zircon HUD source is `Client/Scenes/Views/MainPanel.cs`, using `GameInter #50` as the main panel.
- Current Zircon third resource bar is Focus (`FP` / `Stat.Focus`). ORIGINS has not yet locked its final gameplay meaning. Do not rename or remove it in the desktop reference reconstruction without approval.
- The desktop reference retains the **complete Zircon GameScene UI inventory**. Product removals happen only through the ORIGINS decision matrix after review.
- Source language expressions remain provenance. The reference build may resolve them to real Zircon English strings for sizing/rendering, but must not erase the original expression.
- Mobile/Archero interface work is now authorized as a separate ORIGINS product layer. It must not overwrite the locked desktop reference.

## 3. Authoritative external sources

### Crystal / Mir2
- `Suprcode/Crystal` — parser, movement/frame and client implementation reference.
- `Suprcode/Crystal.Database` — map database/reference, including `Jev/Maps/d501.map` and `d515.map`.
- Public Mir2 Crystal asset mirrors (MirFiles/LOMCN) — source graphics libraries.

### Zircon / Mir3
- `Suprcode/Zircon` — exact current UI class structure, positions, language expressions and library indices.
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
The complete desktop Zircon GameScene reconstruction/reference harness. It is deliberately kept separate from final ORIGINS product decisions and is now the locked source-faithful desktop baseline.

### `apps/game-web/`
Reserved for the integrated playable ORIGINS web client. Product/mobile/Archero adaptation belongs here or in another explicitly approved ORIGINS runtime layer, not in the locked reference harness.

### `tools/`
Importers/extractors, source analyzers, geometry validation and language augmentation. Tools are source pipeline code, not runtime code. Do not delete them after extraction.

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

### UI — validated desktop baseline
- Exact Zircon source snapshot: `cbf1aa919083bc13fc3f23f93772a8ab8370632d`.
- Exact ORIGINS validated desktop baseline: `a3eba357359f1ce95f97020ae68d27792174c8da`.
- Zircon `.Zl` extractor supports the formats required by the current UI data, including DXT1, DXT5, BGRA32, PNG and BC7.
- Automatic parser covers the current `Suprcode/Zircon` GameScene and registered UI source classes.
- Complete GameScene registry: **65/65** source-resolved UI/HUD components.
- Complete nested/transient registry: **15/15**.
- Browser-reviewed viewer inventory: **80/80** windows.
- Current source/browser-validated control floor: **2674 GameScene + 149 nested**.
- GameScene renderer coverage: **22/22** discovered DX types.
- Nested renderer coverage: **10/10** discovered DX types.
- Current source-backed viewer interactions: **21**.
- Browser QA run `32179172068`: **PASS**, 80/80 windows, 0 browser failures, 0 JS errors, Chat Options Add/Remove PASS.
- Visual Review run `32179171965`: **PASS**.
- Visual Review artifact `9340387728`: **80 PNG screenshots + 80 DOM snapshots + offline index**.
- All 80 visual captures were inspected; **0 source-backed visual corrections remain outstanding**.
- Ranking Lime list panel was verified against exact Zircon source and retained intentionally.
- No runtime/server/player data is fabricated to make the reference look populated.
- Searchable/category-based 1024x768 desktop reference harness remains under `apps/zircon-ui-reference/`.
- Active source-geometry renderer: `apps/zircon-ui-reference/app-layout.js`.
- Geometry engine: `apps/zircon-ui-reference/layout-resolver.js`.
- Complete `Point`/`Size` expressions and source-language provenance remain preserved by the source pipeline.
- Source `.Zl` artwork, not screenshots, remains canonical.
- Complete scope documentation: `docs/ZIRCON_UI_FULL_SCOPE.md`.
- Owner review/removal matrix: `docs/ZIRCON_UI_DECISIONS.md`.
- Closure checkpoint: `docs/UI_FIDELITY_CHECKPOINT_2026-08-18.md`.

## 6. What is and is not considered complete

### Complete as a source/reference foundation
- complete Zircon GameScene component inventory: **65/65**;
- complete nested/transient inventory: **15/15**;
- exact source-class resolution for the current registered inventory;
- public `.Zl` dependency extraction for the reference set;
- BC7-capable Zircon UI extraction;
- explicit renderer coverage for all currently discovered GameScene and nested DX control types (**22/22 + 10/10**);
- source geometry resolution at the current validated floor;
- source PNG dimensions and source-language provenance in the derived reference manifest;
- exact-SHA Chrome validation of **80/80** windows;
- exact-SHA Chat Options Add/Remove validation;
- exact-SHA visual evidence for **80/80** windows;
- manual inspection of all 80 captures with no source-backed correction remaining;
- browser-validated control floor **2674+149**;
- desktop Zircon source-faithful reconstruction phase **CLOSED**.

### Still requires product/runtime work
- final ORIGINS `KEEP / REMOVE / MERGE / MOBILE_REDESIGN / DEFER` product decisions;
- live runtime data inside lists, trees, minimap/map, inventory contents, item icons, names and values;
- behavior/runtime integration for events, callbacks and modals that depend on actual game/server state;
- final STANDARD room runtime renderer;
- final KING_ROOM runtime renderer;
- collision integration between room recipes and movement;
- actual player sprite layering inside the final web runtime;
- mobile/Archero-adapted interface;
- monsters/combat/spells/networking/server.

Do not claim that every dynamic Zircon server behavior has been implemented merely because its desktop source UI is reconstructed. Runtime-populated content stays runtime-bound. The locked desktop harness is a reference baseline; final ORIGINS product behavior is implemented separately.

## 7. Development safety

- Never delete, move or rename existing files merely to reorganize the repository.
- Never replace working modules with a new framework without explicit approval.
- Add new code in the documented destination and integrate incrementally.
- Keep source/importer/reference/runtime concerns separated.
- Prefer small, reversible commits.
- Every implementation task must finish with a changed-files summary and test result.
- Do not remove a Zircon reference window because ORIGINS later chooses not to use it; record that decision in `docs/ZIRCON_UI_DECISIONS.md`.
- Do not convert unresolved/runtime data into hard-coded payloads merely to make a preview look complete.
- Do not modify the locked desktop reference merely to simplify a mobile/Archero redesign.

## 8. Next integrated milestone

The desktop Zircon fidelity phase is complete. Begin the ORIGINS product/mobile/Archero adaptation as a separate layer while retaining the locked desktop reference for comparison.

The next playable milestone should combine:
1. the approved same-theme elongated dungeon-room direction (STANDARD + KING_ROOM);
2. real Crystal player locomotion and 8-direction state handling;
3. collision and SOUTH/NORTH transition logic;
4. the locked Zircon desktop HUD/reference as the functional source for product decisions;
5. explicit `KEEP / REMOVE / MERGE / MOBILE_REDESIGN / DEFER` decisions for the first playable slice;
6. a mobile-friendly ORIGINS presentation built without fabricating runtime/server data.

Desktop reference corrections are reopened only when a real Zircon source/asset discrepancy is demonstrated or the chosen Zircon source snapshot changes.
