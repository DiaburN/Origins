# ORIGINS — Zircon UI fidelity checkpoint — 2026-08-18

Branch: `origins-game-v1`
Source of truth: current `Suprcode/Zircon` C# + original Zircon `.Zl` artwork.

This checkpoint records the desktop source-faithful floor. It does not authorize mobile/Archero redesign until the 80-window visual review is complete.

## Browser-validated floor

Exact Chrome evidence exists for:

- ORIGINS SHA: `40d5140805bede9f1c7c5af8c2fb0cefc284856c`
- Zircon source SHA: `cbf1aa919083bc13fc3f23f93772a8ab8370632d`
- Build run: `32175607406`
- Browser QA run: `32175607481`
- Complete build artifact: `9338931478`
- Browser evidence artifact: `9338953250`
- 65 GameScene + 15 nested/transient = **80/80 Chrome PASS**
- **2674 GameScene + 149 nested controls**
- Browser failures: `0`
- Browser JS errors: `0`
- Chat Options Add/Remove smoke: `PASS`

Therefore **2674+149 is browser-validated**, not merely source-audited. The promoted manifest must encode `browserValidationPending=false` while its actual source count stays exactly at that floor. If source growth occurs later, pending must become true again automatically.

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

## Next gate before desktop phase closure

1. Rebuild the promoted HEAD with the validated 2674+149 floor encoded.
2. Obtain exact-SHA Browser QA 80/80 PASS again.
3. Capture 80/80 screenshots through the visual-review workflow from that same SHA.
4. Inspect all captures as QA; verify any suspected discrepancy against Zircon source/`.Zl` before changing code.
5. Close desktop reconstruction only after visual evidence is complete.

Desktop fidelity remains first. Mobile/Archero adaptation is explicitly later.
