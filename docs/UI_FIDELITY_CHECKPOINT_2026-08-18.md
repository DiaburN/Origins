# ORIGINS — Zircon UI fidelity checkpoint — 2026-08-18

Branch: `origins-game-v1`
Source of truth: current `Suprcode/Zircon` C# + original Zircon `.Zl` artwork.

## Desktop reconstruction status: CLOSED

The source-faithful Zircon desktop reference is complete for the current source snapshot and is now the immutable visual/reference baseline for later ORIGINS product adaptation.

Exact closure evidence:

- Validated ORIGINS baseline SHA: `a3eba357359f1ce95f97020ae68d27792174c8da`
- Zircon source SHA: `cbf1aa919083bc13fc3f23f93772a8ab8370632d`
- GameScene windows: **65/65**
- Nested/transient windows: **15/15**
- Total windows: **80/80**
- Browser-validated GameScene controls: **2674**
- Browser-validated nested controls: **149**
- Browser QA run: `32179172068` — **PASS**
- Browser failures: **0**
- Browser JS errors: **0**
- Chat Options Add/Remove smoke: **PASS**
- Visual Review run: `32179171965` — **PASS**
- Visual Review artifact ID: `9340387728`
- Visual evidence: **80 PNG screenshots + 80 DOM snapshots + offline index**
- All 80 captures manually inspected against the Zircon source-backed reference.
- Source-backed visual discrepancies requiring correction: **0**

The bright green Ranking list panel is intentional and verified against exact Zircon source: `RankingDialog.cs` assigns `RankPanelList.BackColour = Color.Lime`. It must not be normalized away merely because it looks unusual.

Therefore **2674+149 is browser-validated**, not merely source-audited. The promoted manifest encodes `browserValidationPending=false` while generated source inventory remains exactly at that floor. Any later source growth must automatically become pending again until another exact-SHA Chrome promotion.

## Current deterministic/source-backed trees

- Ranking: full current Zircon variant **Interface #211, 576×456**; SearchLine + 11 rows = 12 rows / 72 deterministic controls. RankInfo remains runtime-bound.
- DungeonFinder: 9 rows / 54 controls; InstanceInfo remains runtime-bound.
- Fortune: 9 rows / 90 controls; runtime item/fortune data remains neutral.
- BigMap: 24 NPC + 24 Monster rows, scrollbars and 4-control side shell; live map/NPC/monster data remains neutral.
- Guild: header + 17 member rows = 108 deterministic controls; source helper roots included; live guild/castle/member data neutral.
- GameStore: 215 deterministic controls; no StoreInfo/catalog/currency fabrication.
- Consignment: 135 deterministic controls; 38 ItemType buttons including All; 6 Search + 6 Consign rows.
- Communication: 5 blank received rows / 25 controls.
- Group LFG: 5 neutral rows / 20 controls.
- Currency: tree shell + scrollbar only; headers/items remain runtime-bound.
- Companion: 7 bonus rows / 21 controls plus deterministic source filter controls.
- NPCQuestList: 6 blank visible source rows / 18 controls.
- HelpMenu: 2-control shell only; pages/items remain runtime-bound.
- AutoPotion: 8 rows / 80 controls.
- FilterDrop: 10 source labels + 10 source textboxes; no user configuration invented.
- Belt: hotkey labels are generated dynamically from the real grid and do not belong to the fixed floor.

## Shared fidelity rules locked

- All known GameScene DX types render: **22/22**.
- Nested renderer coverage: **10/10**.
- `DXListBoxItem` rows declared under closed `DXComboBox` remain deferred/hidden until the combo opens.
- Empty auto-size `DXLabel` follows current Zircon `DXLabel.GetSize`: empty text => `Size.Empty`.
- Scrollbar source children with `LibraryFile.None / Index=-1` produce no image element.
- MiniMap `TimeOfDayImage` constructor index 0 is a runtime sentinel; live time-of-day selects the real source index.
- Timer preserves source `GameInter 960..965`, `FrameCount=6`, `333ms`, `Loop=false`; `.Zl` slots 961..964 are legitimately empty and draw nothing.
- Chat Options constructor has 0 tabs; Add creates local source-backed UI and Remove destroys it. No fake tabs enter the manifest.
- PNG artwork never carries burned-in dynamic text; visible runtime/localized text stays in runtime/HTML.

## Runtime-bound data that must remain neutral

Never precreate/fabricate CurrencyTreeHeader/CurrencyItem, Chat Options user tabs, Help pages/items, Magic data-driven tabs/cells, Guild CastleInfo, HorseTame MonsterObject, AutoPathRouteControl, Timer server data, or any player/item/map/NPC/monster/store/quest/rank/fortune/dungeon payload.

## Locked handoff to the next phase

The desktop Zircon reconstruction is closed. Mobile/Archero adaptation may now begin from this baseline, but it must remain a separate product layer:

1. Do not overwrite or simplify the desktop reference to make mobile implementation easier.
2. Product `KEEP / REMOVE / MERGE / MOBILE_REDESIGN / DEFER` decisions belong to the ORIGINS layer, not the source-faithful Zircon reference.
3. Continue to use original source assets and source-backed behavior where retained.
4. Runtime/server/player data remains runtime-bound; do not fabricate it for previews.
5. If the desktop source snapshot changes later, reopen validation only for the changed source floor and require new exact-SHA build, Browser QA and Visual Review evidence.
