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
- [x] validated reference extraction: **410 real PNG assets**
- [x] searchable/category-based Zircon desktop UI reference harness
- [x] complete Zircon UI scope document
- [x] owner UI approval/keep-remove matrix
- [x] Zircon public-source CI
- [x] master project state
- [x] Cursor implementation plan
- [x] Cursor persistent rules
- [x] unified public-source bootstrap
- [x] repository ignore/safety policy

## Current UI fidelity pass

The full source/interface inventory is now captured. Do not confuse that with every complex runtime control being visually signed off.

- [x] complete GameScene component inventory
- [x] exact `.Zl` source dependency extraction
- [x] image-backed MainPanel reference
- [x] image-backed Character reference foundation
- [x] image-backed Inventory reference foundation
- [x] Magic reference foundation
- [x] image-backed Quest reference foundation
- [x] image-backed Menu reference foundation
- [ ] reproduce reusable `DXButton` skins/states exactly from `Interface.Zl`
- [ ] reproduce `DXTab` / `DXTabControl` visual states exactly
- [ ] reproduce `DXCheckBox` exactly
- [ ] reproduce text boxes / borders exactly
- [ ] reproduce scrollbars/list boxes exactly
- [ ] reproduce item grids/cells exactly
- [ ] visual pass of all 65 GameScene components
- [ ] owner reviews components and updates `docs/ZIRCON_UI_DECISIONS.md`

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
