# ORIGINS BUILD STATUS

Authoritative branch: `origins-game-v1`

## Integrated in GitHub

- [x] map-engine research/templates/tools
- [x] `zuma_gray` source metadata/room recipes
- [x] Crystal player movement controller
- [x] Crystal locomotion frame resolver/profile
- [x] Crystal player extraction tool + CI
- [x] Zircon `.Zl` extraction tool
- [x] Zircon BC7 UI decoding
- [x] automatic Zircon `GameScene` UI source analyzer
- [x] complete Zircon GameScene registry: **65/65 source-resolved components**
- [x] complete UI reference dependency build: **0 missing public UI libraries**
- [x] validated reference extraction: **449 real PNG assets**
- [x] searchable/category-based Zircon desktop UI reference harness
- [x] explicit renderer policy for **21/21 discovered DX control types**
- [x] source-geometry resolver using parent/child relationships and extracted PNG dimensions/offsets
- [x] deterministic constructor/default-argument geometry resolution
- [x] deterministic `ClientArea`/`Area` geometry resolution
- [x] asset-size-derived geometry (`GetSize(...)`) resolution
- [x] Horse Tame composite geometry recipe from real image bounds
- [x] **742/742 explicit source Locations resolved with 0 suspicious fallbacks**
- [x] zero-fallback geometry regression validation in CI
- [x] Zircon English runtime language extraction: **764 messages**
- [x] **314 UI controls** resolved to real English display text, with original C# expression preserved
- [x] resolved English text drives the reference render and text-dependent sizing
- [x] CI fails if a newly discovered Zircon control type has no renderer policy
- [x] single promoted official Zircon UI build workflow
- [x] simultaneous desktop windows
- [x] desktop focus / z-order
- [x] draggable dialog windows with position persistence
- [x] complete Zircon UI scope document
- [x] owner UI approval/keep-remove matrix
- [x] Zircon public-source CI
- [x] master project state
- [x] Cursor implementation plan
- [x] Cursor persistent rules
- [x] unified public-source bootstrap
- [x] repository ignore/safety policy

## Current UI fidelity pass

The complete source/interface/control inventory is captured. Every currently discovered DX control type has an explicit rendering policy and every explicit `Location` in the current 65-window GameScene inventory resolves without falling back to an invented `(0,0)` coordinate. Runtime-populated lists, maps, item icons, tree rows and live values remain runtime data by design.

- [x] complete GameScene component inventory
- [x] exact `.Zl` source dependency extraction
- [x] image-backed MainPanel reference
- [x] image-backed Character reference foundation
- [x] image-backed Inventory reference foundation
- [x] Magic reference foundation
- [x] image-backed Quest reference foundation
- [x] image-backed Menu reference foundation
- [x] reproduce reusable `DXButton` source skins from `Interface.Zl`
- [x] reproduce `DXTab` / `DXTabControl` chrome policy
- [x] reproduce `DXCheckBox` source skin (`GameInter 161/162`)
- [x] reproduce text/number field border policy
- [x] reproduce scrollbar/list/tree chrome from source indices
- [x] reproduce item grid/cell geometry (`36x36`)
- [x] reproduce combo-box arrow (`GameInter 795`)
- [x] reproduce number-box controls (`GameInter 1010/1011`)
- [x] reproduce sound-bar source assets (`GameInter 4740-4746`)
- [x] explicit policy for all **21/21** currently discovered DX control types
- [x] preserve complete `Point` / `Size` expressions without truncation
- [x] resolve named-control geometry before root `Size`/`DisplayArea` tokens
- [x] resolve forward parent/control references used by the current validation set
- [x] embed asset dimensions and offsets for **8 source libraries**
- [x] extract **764** English Zircon messages
- [x] resolve **314** visible control labels with **0 missing referenced language keys**
- [x] preserve original language expressions as provenance while using real text in rendering
- [x] constructor arguments with default values resolved from actual `GameScene` calls
- [x] MiniMap/BigMap `ClientArea` layout relationships resolved from source
- [x] Milestone `GameInter2.GetSize(500)` dependency resolved from source asset dimensions
- [x] Horse Tame animation/progress geometry derived from real Zircon image bounds
- [x] suspicious explicit source-location fallbacks: **0 / 742**
- [x] multi-window desktop behavior: coexistence, focus/z-order and drag
- [ ] source-derived internal window/button navigation
- [ ] visual owner pass of all 65 GameScene components
- [ ] owner reviews components and updates `docs/ZIRCON_UI_DECISIONS.md`

## Latest validated complete reference build

- workflow run: `31968909610`
- source-resolved windows: `65/65`
- control type render coverage: `21/21`
- parsed controls: `1,014`
- explicit source locations: `742`
- suspicious source-location fallbacks: **`0`**
- English messages parsed: `764`
- controls using resolved English display text: `314`
- unresolved referenced language keys: `0`
- asset-size/metadata libraries: `8`
- missing public UI libraries: `0`
- extracted source PNGs: **`449`**
- JS syntax validation: passed
- zero-fallback geometry validation: passed
- multi-window runtime static validation: passed
- official artifact: `zircon-ui-reference-complete`
- artifact ID: `9269244939`
- artifact SHA256: `40613ef1b0b48f9086a5066846d62261a1510c8a7001261fa0f22d6222de1f16`

## Playable runtime target after desktop UI review

- [ ] create runnable `apps/game-web`
- [ ] establish pinned TS/web workspace + lockfile
- [ ] runtime STANDARD Zuma room
- [ ] runtime KING_ROOM
- [ ] collision map queries
- [ ] integrate existing movement controller
- [ ] render real player idle/walk/run
- [ ] STANDARD NORTH -> next floor SOUTH transition
- [ ] integrate approved Zircon desktop GameInter/HUD
- [ ] integrate approved desktop windows
- [ ] clean browser test with no console errors

## Explicitly later

- final mobile UI adaptation/redesign
- monsters
- combat
- spells
- player attack/hit/death states
- networking/server
- final Focus/FP gameplay decision

Update this checklist as implementation is validated. Do not mark an item complete only because a static preview or source registry exists.
