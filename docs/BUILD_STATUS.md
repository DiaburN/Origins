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
- [x] **853 explicit source Locations resolved with 0 suspicious fallbacks**
- [x] zero-fallback geometry regression validation in CI
- [x] Zircon English runtime language extraction: **764 messages**
- [x] **374 UI controls** resolved to real English display text, with original C# expression preserved
- [x] resolved English text drives the reference render and text-dependent sizing
- [x] CI fails if a newly discovered Zircon control type has no renderer policy
- [x] single promoted official Zircon UI build workflow
- [x] simultaneous desktop windows
- [x] desktop focus / z-order
- [x] draggable dialog windows with position persistence
- [x] source-backed direct window interactions: **14 MouseClick links extracted from Zircon**
- [x] Menu internal navigation validated: Settings / Help / Guild / Storage / Ranking / Companion / Exit
- [x] static captured DXTab selected-state/content switching
- [x] Quest custom tab instances imported: **5**
- [x] Quest static composite contents imported: **76 controls**
- [x] Guild helper-built tab instances imported: **7**
- [x] Guild static composite contents imported: **50 controls**
- [x] Magic source tab templates imported: **16**, visibility remains runtime/data-driven
- [x] complete Zircon UI scope document
- [x] owner UI approval/keep-remove matrix
- [x] Zircon public-source CI
- [x] master project state
- [x] Cursor implementation plan
- [x] Cursor persistent rules
- [x] unified public-source bootstrap
- [x] repository ignore/safety policy

## Current UI fidelity pass

The complete source/interface/control inventory is captured. Every currently discovered DX control type has an explicit rendering policy and every explicit `Location` currently emitted into the 65-window GameScene reference resolves without falling back to an invented `(0,0)` coordinate. Runtime-populated lists, maps, item icons, tree rows and live values remain runtime data by design.

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
- [x] resolve **374** visible control labels with **0 missing referenced language keys**
- [x] preserve original language expressions as provenance while using real text in rendering
- [x] constructor arguments with default values resolved from actual `GameScene` calls
- [x] MiniMap/BigMap `ClientArea` layout relationships resolved from source
- [x] Milestone `GameInter2.GetSize(500)` dependency resolved from source asset dimensions
- [x] Horse Tame animation/progress geometry derived from real Zircon image bounds
- [x] suspicious explicit source-location fallbacks: **0 / 853**
- [x] multi-window desktop behavior: coexistence, focus/z-order and drag
- [x] direct source-derived internal window/button navigation: **14 validated links**
- [x] static/renderable tab runtime: **15 DXTabControls / 50 tabs**
- [x] Quest visible initial tabs: Current / Available / Milestone; Completed and Mission retained hidden per source
- [x] Quest constructor-defined contents: Current `23`, Available `23`, Completed `23`, Milestone `7`
- [x] Quest Mission explicitly runtime-only; no fabricated Mission content
- [x] Guild initial source state: Create tab visible in `noGuild` state; other tabs retained with runtime visibility provenance
- [x] Guild constructor/helper-defined contents: Create `17`, Home `18`, Member `1`, Storage `8`, Style `6`
- [x] Guild War and Castle explicitly runtime/data-only in current source inventory; no fabricated content
- [x] Magic dynamic tab artwork/state templates: **16 schools/cases**, no active-school state invented
- [ ] reference-only Guild state selector (`noGuild` / `hasGuild` / `ownsCastle`) outside game HUD
- [ ] runtime Magic school population from actual player/magic data
- [ ] complex source actions beyond direct window visibility
- [ ] visual owner pass of all 65 GameScene components
- [ ] owner reviews components and updates `docs/ZIRCON_UI_DECISIONS.md`

## Latest validated complete reference build

- workflow run: `31970717601`
- source-resolved windows: `65/65`
- control type render coverage: `21/21`
- parsed/renderable controls: **`1,152`**
- explicit source locations: **`853`**
- suspicious source-location fallbacks: **`0`**
- English messages parsed: `764`
- controls using resolved English display text: **`374`**
- unresolved referenced language keys: `0`
- source-backed direct window interactions: **`14`**
- DXTabControls: `15`
- static/renderable tabs: `50`
- Quest composite children: **`76`**
- Guild composite children: **`50`**
- Guild children by tab: Create `17`, Home `18`, Member `1`, Storage `8`, War `0`, Style `6`, Castle `0`
- Magic dynamic tab templates: `16`
- asset-size/metadata libraries: `8`
- missing public UI libraries: `0`
- extracted source PNGs: **`449`**
- JS syntax validation: passed
- zero-fallback geometry validation: passed
- multi-window runtime static validation: passed
- source-interaction validation: passed
- custom-tab source validation: passed
- Quest/Guild composite validation: passed
- official artifact: `zircon-ui-reference-complete`
- artifact ID: `9269712848`
- artifact SHA256: `86036d14fc49b644b7240e73e8236cfd45332d744f67cc5dbc0eed35ffd08243`

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
