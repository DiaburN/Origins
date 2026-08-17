# ORIGINS BUILD STATUS

Authoritative branch: `origins-game-v1`

## Integrated in GitHub

- [x] map-engine research/templates/tools
- [x] `zuma_gray` source metadata/room recipes
- [x] Crystal player movement controller + locomotion extraction
- [x] Zircon `.Zl` extraction + BC7 decoding
- [x] automatic Zircon `GameScene` UI source analyzer
- [x] complete Zircon GameScene registry: **65/65 source-resolved components**
- [x] nested/transient Zircon DXWindow inventory: **15/15 source-reconstructed windows**
- [x] total desktop source coverage under review: **80 windows**
- [x] 0 missing public Zircon UI libraries
- [x] **578 real extracted PNG assets**, including indexed button states and deterministic animation ranges
- [x] explicit renderer policy for **21/21 discovered GameScene DX control types**
- [x] nested renderer coverage **10/10 discovered nested DX control types**
- [x] searchable/category-based desktop reference harness
- [x] real Zircon English language extraction: **764 messages**
- [x] **483 visible controls** resolved to real English text
- [x] source-backed direct window interactions: **14**
- [x] simultaneous windows, focus/z-order and dragging
- [x] Quest custom tabs and **76** static composite children
- [x] Guild helper-built tabs and **50** static composite children
- [x] Magic **16** runtime school templates, without invented active schools
- [x] Settings `DXConfigSection` automatic layout reconstructed from source
- [x] Character/Equip source preview corrected against Zircon
- [x] Character male/female static bodies extracted from `ProgUse #0/#1`
- [x] Character/Equip preview source anchor locked to **`(130,270)`**
- [x] Character hidden Weapon/Armour/Shield/Helmet hit-zones respect `DXItemCell.Hidden`
- [x] Character visible slot artwork uses Zircon source Interface indices
- [x] nested `DXKeyBindWindow` reconstructed and linked from Settings
- [x] `KeyBindTree` custom control expanded to its real `DXVScrollBar`
- [x] `DXColourPicker` reconstructed and opened by `DXColourControl`
- [x] `DXMessageBox` three source button variants preserved: `OK`, `YesNo`, `Cancel`
- [x] `DXInputWindow` runtime message/caption/value contract preserved
- [x] `DXItemAmountWindow` runtime `item.Count` / Change contract preserved
- [x] Colour Picker palette explicitly marked runtime texture; no fake palette artwork
- [x] source-faithful `DXAnimatedControl` frame runtime bundled into the official viewer
- [x] deterministic animation frame ranges promoted automatically into extraction refs
- [x] current Horse Tame `LassoAnimation` contract locked to Zircon source
- [x] current Timer `_eggTimer` index-driven contract locked to Zircon source
- [x] `DXTextBox` / `DXNumberTextBox` focus, editable/read-only, password, max-length and numeric behavior reproduced
- [x] `DXVScrollBar` / `DXHScrollBar` state, wheel, buttons, track and thumb drag reproduced when source values are deterministic
- [x] `DXListBox` neutral empty state uses source scrollbar geometry and no fabricated rows
- [x] `DXTreeControl` neutral empty state uses Interface `59/60/61/62`, 21px rows, 2px row offset and no fabricated placeholder text
- [x] `DXItemGrid` corrected to Zircon **35px shared-line cell step**, 36×36 cells, `GridPadding`, `VisibleHeight` and `ScrollValue`
- [x] standalone `DXItemCell` Hidden/fixed/selected/locked/hover visual-state behavior reproduced without fabricating item data
- [x] `DXButton` generated/indexed artwork tint reproduced: normal `217/255`, hover/pressed white, disabled `51/255`, plus source 1px pressed offset
- [x] repository/Cursor safety rules, bootstrap and master implementation docs

## Geometry / source fidelity

The GameScene reference is source-derived. Runtime-populated rows, item data, maps, messages and player-specific values remain runtime data by design and are not fabricated.

- [x] temporal C# post-initializer assignment pass with reused-local scope
- [x] **398** GameScene temporal post assignments applied
- [x] **387** GameScene `Location` assignments recovered that the flat parser previously missed
- [x] inline C# geometry mutations such as `y += rowSpacing` executed in source order
- [x] C# preprocessor directives ignored as non-executable tokens during layout parsing
- [x] **1,389 / 1,389** explicit GameScene source Locations resolve with **0 suspicious fallbacks**
- [x] **133** explicit nested/transient source Locations captured; current protected floor `>=78`
- [x] all controls without direct `Location` are source-classified
- [x] **81** controls intentionally without constructor Location audited
- [x] **0 UNKNOWN unplaced controls**
- [x] unplaced classifications: Event `13`, Method `53`, Tab auto-layout `5`, List auto-layout `2`, Default origin `4`, Runtime-data layout `3`, Detached nested window `1`
- [x] build fails if a control without Location has no source-backed explanation
- [x] build fails if GameScene explicit Location coverage drops below **1,389**
- [x] build fails if nested explicit Location coverage drops below **78**
- [x] constructor/default-argument geometry resolution
- [x] `ClientArea` / `Area` relationships
- [x] named-control / parent-child geometry
- [x] extracted PNG dimensions and offsets embedded for 8 source libraries
- [x] `GetSize(...)` asset-size relationships
- [x] Horse Tame real-image-bound geometry
- [x] original source expressions retained as provenance where transformed

## Character / Equip validation

The older generated preview that visually centred the player is **not authoritative**.

Zircon source `CharacterDialog.CharacterTab_BeforeChildrenDraw` uses:

- male base: `ProgUse #0`
- female base: `ProgUse #1`
- source anchor: **`x=130, y=270`** inside `CharacterTab`
- male extracted metadata: `84×178`, offset `(-22,-123)`
- female extracted metadata: `80×182`, offset `(-22,-122)`

Equipment/hair layers are player/item runtime data and are not invented in the neutral reference state.

## GameScene UI coverage

- [x] MainPanel / HUD
- [x] Belt / Chat / MiniMap / BigMap
- [x] Character / Inspect
- [x] Inventory
- [x] Magic foundation + dynamic school templates
- [x] Quest / Tracker / Milestone
- [x] Group / GroupHealth
- [x] Guild / GuildMember
- [x] Storage
- [x] Trade / Communication / Consignment / GameStore
- [x] Ranking / Companion
- [x] Menu / Settings / Help / Exit
- [x] NPC dialog families (repair/refine/quest/crafting/socket/etc.)
- [x] Fishing / FishingCatch / HorseTame
- [x] remaining GameScene windows from the canonical **65/65** registry

## Nested / transient source UI coverage

All **15/15** currently referenced Client DXWindow subclasses outside direct GameScene fields are source-reconstructed:

- [x] `DXColourPicker`
- [x] `DXInputWindow`
- [x] `DXItemAmountWindow`
- [x] `DXKeyBindWindow`
- [x] `DXMessageBox`
- [x] `GroupLFGInputWindow`
- [x] `MarketPlaceHistoryDialog`
- [x] `ActivationDialog`
- [x] `ChangePasswordDialog`
- [x] `NewAccountDialog`
- [x] `NewCharacterDialog`
- [x] `RequestActivationKeyDialog`
- [x] `RequestResetPasswordDialog`
- [x] `ResetPasswordDialog`
- [x] `SelectDialog`

Runtime values are represented as runtime contracts rather than sample/fake game data.

## Interaction / state fidelity already implemented

- [x] multiple windows can coexist
- [x] drag and z-order/focus
- [x] 14 direct source-derived visibility links
- [x] Menu -> Settings / Help / Guild / Storage / Ranking / Companion / Exit
- [x] MiniMap -> BigMap
- [x] Settings -> Key Bind
- [x] colour swatch -> Colour Picker
- [x] `DXNumberBox` decrement/increment + min/max/change behavior
- [x] `DXSoundBar` mute/value/click/drag behavior using 4740-4746
- [x] Guild review states outside game UI
- [x] MessageBox review variants outside game UI
- [x] MessageBox OK/Yes/No/Cancel + keyboard dismissal in the reference runtime
- [x] `DXInputWindow` editable value field + Confirm/Cancel/Enter/Escape behavior
- [x] ItemAmount does not invent `item.Count`; neutral review preserves source initial `Value=1`
- [x] ItemAmount Confirm closes without fabricating item quantity data
- [x] Colour Picker RGB boxes update the selected swatch; runtime-only palette texture is not fabricated
- [x] Colour Picker Select/Cancel behavior wired
- [x] `DXAnimatedControl` timing uses `AnimationDelay / FrameCount`, source frame offsets and Loop semantics
- [x] deterministic source scrollbars are interactive; runtime-data list/tree scrollbars remain neutral rather than inventing row counts
- [x] source `DXButton` artwork state/tint and pressed motion reproduced independently from label text

## Latest validated official build

- workflow run: **`32065223098`**
- commit: **`7e1bae015b22911dd35617e707b3ee2736f4ff7b`**
- canonical GameScene windows: **`65/65`**
- nested/transient windows: **`15/15`**
- total source window coverage: **`80`**
- GameScene parsed/renderable controls: **`1,460`**
- nested parsed/renderable controls: **`143`**
- temporal GameScene post assignments: **`398`**
- recovered GameScene Locations: **`387`**
- explicit GameScene Locations: **`1,389`**, fallbacks `0`
- explicit nested Locations: **`133`**
- controls without direct Location: **`81`**, UNKNOWN `0`
- English messages: `764`
- controls using resolved English text: **`483`**
- unresolved referenced language keys: `0`
- direct source window interactions: `14`
- GameScene DXTabControls: `15`
- static/renderable tabs: `50`
- Quest composite children: `76`
- Guild composite children: `50`
- Magic dynamic templates: `16`
- GameScene render type coverage: **`21/21`**
- nested render type coverage: **`10/10`**
- indexed GameScene controls audited: **`399`**
- indexed nested controls audited: **`6`**
- render audit issue groups: **`0`**
- missing public UI libraries: `0`
- extracted source PNGs: **`578`**
- official artifact: `zircon-ui-reference-complete`
- artifact ID: **`9299639955`**
- artifact SHA256: **`8bbd5d09453dfdb8c0065b59a5b250b4b0163f0fc9899ede9d4848d742a89198`**
- JS syntax validation: passed
- zero-fallback geometry validation: passed
- zero-UNKNOWN placement audit: passed
- official CI: **passed**

## Current QA phase

Source window coverage and placement are strongly validated. The active pass remains **visual/render fidelity** across all 80 windows: exact skin type, real indexed artwork, hidden/visible semantics, clipping, control state and source-driven runtime behavior.

- [x] audit every currently discovered GameScene + nested control type for renderer coverage
- [x] audit current literal `LibraryFile + Index` controls and extract required source artwork
- [x] audit deterministic `DXAnimatedControl` ranges and extract their frames
- [x] correct repeated source-control behaviors for textboxes, scrollbars, list/tree neutral states, item grids/cells and buttons
- [ ] reproduce remaining explicit `DXLabel` formatting only where source colors/styles are deterministically available
- [ ] finish `DXComboBox` source showing/selection behavior without fabricating runtime options
- [ ] eliminate any remaining generic renderer where Zircon defines real artwork/chrome
- [ ] review every one of the 80 source windows in the reference harness
- [ ] correct any visual discrepancy found against Zircon source/assets
- [ ] finish complex actions that are more than direct visibility/toggle behavior
- [ ] populate Magic schools only when actual player/magic runtime data is available
- [ ] owner marks KEEP / REMOVE / MERGE / MOBILE_REDESIGN in `docs/ZIRCON_UI_DECISIONS.md`

Do **not** mark the desktop UI owner-approved until that visual pass is complete.

## Playable runtime target after desktop UI approval

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

Update this checklist only from validated source/build evidence. Static generated previews are never authoritative.
