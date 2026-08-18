# ORIGINS BUILD STATUS

Authoritative branch: `origins-game-v1`
Zircon source of truth: current `Suprcode/Zircon` C# + original `.Zl` artwork.

## Browser-validated Zircon desktop checkpoint — 2026-08-18

The desktop reconstruction has reached a real Chrome-validated control floor. This is not inferred from source counts: it is backed by an exact-SHA build artifact and an 80-window Browser QA run.

- Browser-validation evidence SHA: `40d5140805bede9f1c7c5af8c2fb0cefc284856c`
- Zircon source SHA used by that build: `cbf1aa919083bc13fc3f23f93772a8ab8370632d`
- Exact build run: `32175607406`
- Browser QA run: `32175607481`
- Exact complete viewer artifact ID: `9338931478`
- Browser QA evidence artifact ID: `9338953250`
- GameScene windows: **65/65**
- Nested/transient windows: **15/15**
- Total windows tested in Chrome: **80/80 PASS**
- Browser-validated GameScene control floor: **2674**
- Browser-validated nested control floor: **149**
- Browser failures: **0**
- Browser JS errors: **0**
- Chat Options local Add/Remove smoke: **PASS**
- Chat Options constructor tabs: **0**; Add creates local source-backed state only; Remove returns to **0**
- Runtime/server/player payloads fabricated for validation: **0**

The control-floor contract is now `browserValidationPending=false` while the generated source inventory remains exactly `2674+149`. Any later source growth must automatically become pending again until another exact-SHA Chrome promotion.

## Current source-faithful reconstruction

- 65 GameScene windows + 15 nested/transient windows = **80** stable viewer windows.
- Current source-backed window interactions: **21**.
- GameScene renderer coverage: **22/22** discovered DX types.
- Nested renderer coverage: **10/10** discovered DX types.
- Ranking current Zircon variant: **Interface #211, 576×456**, 11 ranking rows + SearchLine; rank/player data neutral.
- AutoPotion: **8 rows / 80 controls**.
- Ranking deterministic tree: **12 rows / 72 controls**.
- DungeonFinder deterministic tree: **9 rows / 54 controls**.
- Fortune deterministic tree: **9 rows / 90 controls**.
- BigMap: **24 NPC + 24 Monster rows**, source scrollbars and 4-control side shell; map/NPC/monster payloads neutral.
- Guild: **1 header + 17 member rows / 108 deterministic controls**, plus source root helpers; guild/castle/member runtime payloads neutral.
- GameStore: **215 deterministic controls**, no StoreInfo/catalog/currency fabrication.
- Consignment: **135 deterministic controls**, 38 ItemType buttons and 6+6 source rows, no marketplace payloads.
- Communication: **5 received rows / 25 controls**, no mail data.
- Group LFG: **5 rows / 20 controls**, no LFG server data.
- Currency: deterministic tree shell + scrollbar only; user currency rows runtime-bound.
- Companion: **7 bonus rows / 21 controls** plus source enum filter controls; live companion data neutral.
- NPCQuestList: **6 rows / 18 controls**, blank source state only.
- HelpMenu: deterministic shell only; HelpInfo pages/items runtime-bound.
- FilterDrop: exact **10 labels + 10 textboxes**, with no user filter configuration invented.
- Belt hotkey labels remain resize/grid driven and outside the fixed control floor.

## Source/runtime boundaries locked

The reference must never fabricate player, item, quest, guild, ranking, mail, dungeon, NPC, monster, map, currency, store or server-response data. Runtime-bound structures remain empty/neutral until real runtime data exists.

Important current runtime-only cases include CurrencyTreeHeader/CurrencyItem, user-created Chat Options tabs, Help pages/items, Magic tabs/cells, Guild CastleInfo, HorseTame MonsterObject, MiniMap/BigMap AutoPathRouteControl, Timer server values and all player/item/map/NPC/monster payloads.

## Recent fidelity fixes included in the browser-validated artifact

- Reused-local geometry is replayed from exact lexical initializer offsets and post-assignments.
- Empty auto-size `DXLabel` controls follow Zircon `DXLabel.GetSize`: empty text => `Size.Empty`.
- Disabled scrollbar children with `LibraryFile.None / Index=-1` are not emitted as broken browser images.
- MiniMap time-of-day constructor `GameInter #0` is treated as a runtime sentinel; no fake #0 artwork is requested.
- Timer keeps Zircon's 960..965 / 333ms animation contract while legitimate empty `.Zl` slots 961..964 draw nothing rather than becoming 404 PNGs.
- Chat Options Add is bound by the current source language identity and passes real Chrome Add/Remove smoke.
- All custom-draw sites are classified against current Zircon source; runtime draws stay neutral.

## CI gates

The official build and audits must remain source-faithful; gates are not relaxed to manufacture PASS results.

- `.github/workflows/build-zircon-ui-reference.yml`
- `.github/workflows/audit-zircon-source-contracts.yml`
- `.github/workflows/audit-zircon-supplemental-contracts.yml`
- `.github/workflows/browser-qa-zircon-ui-reference.yml`
- `.github/workflows/publish-zircon-browser-qa-status.yml`
- `.github/workflows/visual-review-zircon-ui-reference.yml`

Commit status context: `origins/zircon-browser-qa`. Empty/unavailable status is never PASS; only exact-SHA Browser QA success is accepted.

## Phase status

- [x] Source-faithful audits reach a complete 65+15 manifest.
- [x] Complete exact artifact builds successfully.
- [x] Chrome Browser QA covers **80/80** windows.
- [x] Chat Options local Add/Remove passes in Chrome.
- [x] Browser-validated control floor promoted to **2674+149** from exact evidence.
- [ ] Run the promoted HEAD through Browser QA again with `browserValidationPending=false` encoded in the artifact.
- [ ] Capture and retain **80/80 visual-review PNGs** from that same promoted SHA.
- [ ] Inspect the 80 captures as QA and correct only source-verified discrepancies.
- [ ] Close the desktop Zircon reconstruction phase.

Do not begin the ORIGINS mobile/Archero adaptation until the visual-review step above is complete. Screenshots are QA evidence only; Zircon source + `.Zl` remain authoritative.
