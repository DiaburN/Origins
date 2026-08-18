# ORIGINS BUILD STATUS

Authoritative branch: `origins-game-v1`
Zircon source of truth: current `Suprcode/Zircon` C# + original `.Zl` artwork.

## Zircon desktop checkpoint — CLOSED 2026-08-18

The desktop reconstruction has completed its exact-SHA source, build, browser and visual validation cycle.

Validated baseline:

- ORIGINS desktop baseline SHA: `a3eba357359f1ce95f97020ae68d27792174c8da`
- Zircon source SHA: `cbf1aa919083bc13fc3f23f93772a8ab8370632d`
- GameScene windows: **65/65**
- Nested/transient windows: **15/15**
- Total browser windows: **80/80 PASS**
- Browser-validated GameScene control floor: **2674**
- Browser-validated nested control floor: **149**
- Browser QA run: `32179172068` — **PASS**
- Browser failures: **0**
- Browser JS errors: **0**
- Chat Options local Add/Remove smoke: **PASS**
- Visual Review run: `32179171965` — **PASS**
- Visual Review artifact ID: `9340387728`
- Visual evidence retained: **80 PNG screenshots + 80 DOM snapshots + offline index**
- Manual review: **80/80 inspected; 0 source-backed visual corrections outstanding**
- Runtime/server/player payloads fabricated for validation: **0**

The control-floor contract is `browserValidationPending=false` while generated source inventory remains exactly `2674+149`. Any later source growth must automatically become pending again until another exact-SHA Chrome promotion.

The visually unusual Lime Ranking panel is source-correct: current Zircon explicitly sets `RankPanelList.BackColour = Color.Lime`. It is retained intentionally.

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

Important runtime-only cases include CurrencyTreeHeader/CurrencyItem, user-created Chat Options tabs, Help pages/items, Magic tabs/cells, Guild CastleInfo, HorseTame MonsterObject, MiniMap/BigMap AutoPathRouteControl, Timer server values and all player/item/map/NPC/monster payloads.

## Fidelity fixes in the validated baseline

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

Exact-SHA status contexts used for closure include `origins/zircon-browser-qa` and `origins/zircon-visual-review`. Empty/unavailable status is never PASS.

## Phase status

- [x] Source-faithful audits reach a complete 65+15 manifest.
- [x] Complete exact artifact builds successfully.
- [x] Chrome Browser QA covers **80/80** windows.
- [x] Chat Options local Add/Remove passes in Chrome.
- [x] Browser-validated control floor promoted to **2674+149**.
- [x] Promoted HEAD revalidated through exact-SHA Browser QA.
- [x] **80/80 visual-review PNGs** captured from the same exact SHA.
- [x] All 80 captures inspected; only source-verified differences are retained.
- [x] Desktop Zircon reconstruction phase closed.

The desktop reference is now a locked baseline. ORIGINS mobile/Archero adaptation may proceed as a separate product layer without modifying the source-faithful desktop reference.
