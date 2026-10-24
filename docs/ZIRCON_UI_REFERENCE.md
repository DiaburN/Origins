# ZIRCON UI REFERENCE — ORIGINS X

**Source of truth for the browser interface.**

Audited against `Suprcode/Zircon` master commit `c6e6804d012734f64f9e3cb0b2f21806b1a8ed5e` (2026-10-21).

## Status vocabulary

- **VERIFIED**: copied from the Zircon C# source: library/index, geometry, control hierarchy or behavior.
- **CURRENT-WRONG**: ORIGINS currently renders an approximation that must be replaced.
- **BLOCKED-ASSET**: behavior is known, but the original graphics library needed for a faithful browser runtime is not present.
- **PENDING-AUDIT**: class exists in `GameScene`, but its complete child-control geometry still needs to be transcribed before implementation.

## Non-negotiable implementation rules

1. No visual coordinates are guessed. Every fixed coordinate must come from Zircon source or from a verified source asset dimension.
2. No static screenshot/preview may replace a layered renderer when Zircon composes the result at runtime.
3. `.Zl` libraries are conversion sources only; browser runtime uses lossless WebP/atlases/manifests.
4. Interface geometry lives in `data/ui/zircon-ui-spec.json`; browser code consumes that data instead of duplicating positions in CSS/JS.
5. `Microsoft Sans Serif` is Zircon's default `Config.FontName`. Default `DXLabel` size is 8F with outline.
6. `DXItemCell` is always 36×36 unless a specific slot explicitly overrides its size.
7. Missing original assets stay empty/disabled. Do not draw a replacement.
8. Heavy character/map runtimes may remain outside GitHub; GitHub keeps code, manifests and compact UI assets.

---

# 1. Core controls

## DXControl — VERIFIED
Source: `Client/Controls/DXControl.cs`

- `DefaultHeight` = height of `Interface[16]`.
- `TabHeight` = height of `Interface[19]`.
- `SmallButtonHeight` = height of `Interface[41]`.
- Core colours:
  - Active tab: white.
  - Inactive tab: RGB(123,105,66).
  - Text: white.
  - Primary: RGB(198,166,99).
  - Row background: RGB(25,20,0).
  - Inactive border: RGB(99,83,50).
  - Window background: RGB(16,8,8).

## DXItemCell — VERIFIED
Source: `Client/Controls/DXItemCell.cs`

- `CellWidth = 36`.
- `CellHeight = 36`.
- Default background transparent, inactive border colour.
- Count label is anchored bottom-right.
- Selection/locked/linked/read-only states are behavior, not separate invented artwork.

## DXTabControl / DXTab — VERIFIED
Source: `Client/Controls/DXTabControl.cs`

- Default tab padding: 1 px.
- `MarginLeft` is supplied by each parent window.
- Tab buttons are laid out by the control, not by arbitrary flex percentages.
- Supports right-aligned tabs and overflow left/right buttons.
- Selected tab is the only tab content drawn normally.
- Minimum tab widths are per-dialog (`40`, `60`, `100`, etc.).

## DXWindow — VERIFIED
Source: `Client/Controls/DXWindow.cs`

DXWindow chrome is assembled from `Interface.Zl`, not from CSS gradients.

Verified Interface pieces:

| role | Interface index |
|---|---:|
| header/top | 0 |
| vertical side | 1 |
| border strip / no-header strip | 2 |
| inner title/header | 3 |
| title corners | 4 / 5 |
| bottom corners | 8 / 9 |
| footer pieces | 10 / 126 |
| top corners | 11 / 12 |
| close button | 15 |
| no-header top corners | 25 / 26 |

The browser must reproduce Zircon's `ClientArea`, header and footer calculations from these image sizes. A precomposed generic brown rectangle is not equivalent.

---

# 2. Global game layout

## Scaling — VERIFIED
Source: `Client/Scenes/GameScene.cs`

- `UIScale = clamp(Config.UIScalePercent / 100, 1, 3)`.
- `UISize = floor(SceneSize / UIScale)`.
- UI controls use logical UI coordinates; the world/map is not scaled as a UI child.
- Anchored controls are re-anchored on scale/resolution changes.

ORIGINS must keep a logical coordinate space and scale the UI layer as a unit. Do not independently resize individual windows.

## Default anchors — VERIFIED
Source: `GameScene.SetDefaultLocations()`.

- MainPanel: horizontally centered, bottom edge.
- MiniMap: top-right.
- Character: `(0,0)` before saved window settings.
- Inventory: right edge, below MiniMap.
- Magic: right edge, top.
- Communication: centered.
- Belt: immediately above the right side of MainPanel.
- Group: centered together with GroupBag, separated by 4 px.
- Menu: bottom-right, immediately above MainPanel.
- GameStore: centered.
- Quest has no special centered default in the source; saved settings may move it.

---

# 3. MainPanel — VERIFIED
Source: `Client/Scenes/Views/MainPanel.cs`

- Library: `GameInter`.
- Background: `GameInter[50]`.
- Exact size from asset: 1024×68.

Bars:

| control | index | location |
|---|---:|---:|
| Experience frame | 51 | around `(17,3)`, centered from asset size |
| Experience fill | 56 | inside frame, y offset -1 |
| HP | 52 | `(35,22)` |
| MP | 54 | `(35,36)` |
| Focus normal | 58 | `(35,50)` |
| Focus glow | 59 | `(35,50)` when full, alternating by second |

Buttons:

| action | index | location |
|---|---:|---:|
| Character | 82 | `(650,23)` |
| Inventory | 87 | `(689,23)` |
| Magic | 92 | `(728,23)` |
| Quest | 112 | `(767,23)` |
| Mail | 97 | `(806,23)` |
| Belt | 107 | `(845,23)` |
| Group | 102 | `(884,23)` |
| Menu | 117 | `(923,23)` |
| Cash shop | 122 | `(972,16)` |

Alerts:

- `GameInter[240]`: mail / quest available.
- `GameInter[241]`: quest complete.
- Quest complete is moved to the bottom of the quest button when the available alert is also visible.

Stat icons / labels:

| stat | icon | icon location | label location |
|---|---:|---:|---:|
| Class | 70 | `(277,25)` | `(300,20)` |
| Level | 71 | `(277,45)` | `(300,40)` |
| FP | 72 | `(362,25)` | `(385,20)` |
| CP | 73 | `(362,45)` | `(385,40)` |
| AC | 66 | `(445,25)` | `(470,20)` |
| DC | 65 | `(445,45)` | `(470,40)` |
| MAC | 63 | `(531,25)` | `(567,20)` |
| MC | 62 | `(541,45)` | `(567,40)` |
| SC | 64 | `(547,45)` | `(567,40)` |

Labels are 60×16, centered, 8F. MC is visible for Warrior/Wizard; SC for Taoist/Assassin.

Current ORIGINS status: **PARTIAL**. Assets and most coordinates exist, but text raster/vertical metrics and interaction states still need exact comparison.

---

# 4. CharacterDialog — VERIFIED CORE / CURRENT-WRONG PAPERDOLL
Source: `Client/Scenes/Views/CharacterDialog.cs`

- Library: `Interface`.
- Normal background: `Interface[110]`.
- Inspect background: `Interface[115]`.
- Close: `Interface[15]`, top-right.
- Top tab control: location `(0,19)`, `MarginLeft=18`.
- Character/Discipline/Hermit/Crafting content origin: `(0,26)`.

## Name panel

- Panel size: 137×68.
- Location: `(((CharacterTab.Width - 135) / 2) - 5, 51)`.
- Name: 137×20, 9F bold, RGB(222,255,222), centered.
- Guild: y=18, 137×15, RGB(255,255,181).
- Guild rank: y=31, 137×15, RGB(255,206,148).
- **Class and level do not belong in this panel.**

## Equipment cells

| slot | location | size / note |
|---|---:|---|
| Weapon | `(58,122)` | 65×90, hidden interaction region |
| Armour | `(120,123)` | 70×150, hidden interaction region |
| Shield | `(170,170)` | hidden |
| Helmet | `(140,90)` | 35×35, hidden |
| Emblem | `(244,118)` | standard cell |
| HorseArmour | `(283,118)` | standard cell |
| Torch | `(10,196)` | standard cell |
| Necklace | `(10,157)` | standard cell |
| BraceletL | `(244,157)` | standard cell |
| BraceletR | `(283,157)` | standard cell |
| RingL | `(244,196)` | standard cell |
| RingR | `(283,196)` | standard cell |
| Flower | `(244,235)` | standard cell |
| Poison | `(244,274)` | standard cell |
| Amulet | `(283,235)` | 36×75 |
| Shoes | `(10,235)` | 36×75 |
| Costume | `(10,118)` | standard cell |

The background-cell icons are drawn by CharacterDialog's `Draw(cell,index)` logic; they are not arbitrary black boxes.

## Paperdoll renderer — CRITICAL

`CharacterTab_BeforeChildrenDraw()` uses render origin:

```text
x = 130
y = 270
```

This is a **layered renderer**, never a pre-rendered class image.

Verified order/logic:

1. Optional Fame effect.
2. Optional armour exterior effect when armour exists and no costume.
3. Base body from `ProgUse`:
   - male: index `0`
   - female: index `1`
   - special Assassin female hair pre-layer: `ProgUse[1160]` in the documented condition.
4. Equipment from `Equip`:
   - Costume replaces armour body layer; image index = `costume.Info.Image`.
   - Otherwise armour image + armour colour overlay.
   - Weapon image + colour overlay + optional exterior effect.
   - Shield image + colour overlay + optional exterior effect.
5. Head:
   - helmet image/overlay when equipped;
   - otherwise hair from `ProgUse`:
     - Warrior/Wizard/Taoist male: `60 + HairType - 1`
     - Warrior/Wizard/Taoist female: `80 + HairType - 1`
     - Assassin male: `1100 + HairType - 1`
     - Assassin female: `1120 + HairType - 1`

**ORIGINS CURRENT-WRONG:** `character-ui.js` inserts `assets/ui/zircon/characters/<class>-<gender>.webp`. That is only a static preview and must not be used inside CharacterDialog.

**BLOCKED-ASSET:** the repository does not currently contain a browser runtime for `ProgUse.Zl` and `Equip.Zl`. Until those source libraries are supplied/discovered locally and converted, the faithful paperdoll area must remain empty rather than show a geared preview.

## Stats tabs

Stats tab control:
- location `(0,319)` relative to CharacterTab.
- height 120.
- `MarginLeft=21`.
- content y=22.
- minimum tab width 40.

Tabs in order:
`Att`, `Def`, `Wt`, `Oth`, `E.Att`, `E.Adv`, `E.Dis`.

Shared stat layout:
- `yStart=6`.
- left column x=15.
- right column x=168.
- row spacing=22.
- value boxes 100×16, right-aligned.

Attack tab:
- Left: DC, MC, SC, Crit. Damage.
- Right: Accuracy, A. Speed, Luck, Crit. Chance.

Defense, Weight, Other and elemental tabs must be transcribed completely before they are considered implemented.

---

# 5. InventoryDialog — VERIFIED
Source: `Client/Scenes/Views/InventoryDialog.cs`

- Library: `Interface`.
- Background: `Interface[130]`.
- Inventory grid: 6×8 at `(20,39)`, GridPadding=1, border false.
- Cells: 36×36.
- Weight bar: `GameInter[360]` at `(53,355)`.
- Currency title/value 1: y=381.
- Currency title/value 2: y=400.
- Sort: `GameInter[364]` at `(180,384)`.
- Trash: `GameInter[358]` at `(218,384)`.
- Sell mode uses `GameInter[354]` at the same location.
- Wallet hitbox: `(8,380)`, 45×40.

Current ORIGINS status: **PARTIAL**. Background and some labels exist; exact 6×8 `DXItemGrid`, cell states and interactions are not yet reproduced.

---

# 6. BeltDialog — VERIFIED / CURRENT-WRONG
Source: `Client/Scenes/Views/BeltDialog.cs`

Belt is a real `DXWindow`, not a fixed bitmap.

- `HasTitle=false`.
- `HasFooter=false`.
- `HasTopBorder=false`.
- Title/Close hidden.
- Resizable.
- Grid columns/rows are calculated from `ClientArea` using `(DXItemCell.CellWidth - 1)` and `(CellHeight - 1)`.
- Quick-slot labels use 8F italic at `(-2,-1)` inside cells.

**ORIGINS CURRENT-WRONG:** the precomposed 239×54 `belt-frame` is an approximation and must be replaced by exact DXWindow chrome + item cells.

---

# 7. MagicDialog — VERIFIED OUTER STRUCTURE
Source: `Client/Scenes/Views/MagicDialog.cs`

- `DXWindow`, size 419×511.
- Footer disabled, movable, drop shadow.
- Class headers: Interface 160 Warrior, 161 Wizard, 162 Taoist, 163 Assassin at `(0,0)`.
- Background: Interface164 at `(0,66)`.
- TabControl: `(0,40)`, size420×448, MarginLeft56, Padding2.
- Magic cell background: Interface165, 369×54.
- Scroll: Interface60/61/62.
- Magic icon library: `MagicIcon`.
- Level 4 border: `GameInter2`.
- Experience bar: `GameInter2[812]` at `(110,36)`.

School images:

`166/167 Active`, `168/169 Passive`, `170/171 Toggle`, `172/173 Horse`, `174/175 Fire`, `176/177 Ice`, `178/179 Lightning`, `180/181 Wind`, `182/183 Phantom`, `184/185 Holy`, `186/187 Dark`, `188/189 Physical`, `190/191 Atrocity`, `192/193 Kill`, `194/195 Assassination`.

ORIGINS may intentionally redesign skill progression/evolution, but window frame, class header and base geometry remain Zircon-derived unless explicitly changed later.

---

# 8. QuestDialog — VERIFIED SHELL
Source: `Client/Scenes/Views/QuestDialog.cs`

- Background Interface291 normally.
- Interface292 for Milestones.
- Interface293 for Missions.
- TabControl `(0,21)`, size732×459, MarginLeft18.
- Tab content starts y=22.
- Tabs include Current, Available, Completed, Milestone and Mission; some visibility depends on data/state.

Internal quest rows/content: **PENDING-AUDIT** before implementation.

---

# 9. CommunicationDialog — VERIFIED SHELL
Source: `Client/Scenes/Views/CommunicationDialog.cs`

- Main background Interface200.
- TabControl `(0,37)`, size296×340, MarginLeft10.
- Sub-background at `(0,23)`, 296×316:
  - Friends201
  - Received202
  - Send203
  - Blocked204
- Read-mail view uses Interface205.
- Contains friend list/state, received mail, send form/item/gold, read mail and blocked list.

Current ORIGINS status: **INCOMPLETE**; tabs/background alone are not a faithful CommunicationDialog.

---

# 10. Group / GroupBag — VERIFIED

## GroupDialog
Source: `Client/Scenes/Views/GroupDialog.cs`

- Background Interface240.
- Member tab region: `(13,60)`, 214×148.
- Allow-group checkbox anchored right at y=40.
- Add `(35,217)`, 36×36.
- Remove `(81,217)`.
- LFG `(127,217)`.
- Group bag button uses `GameInter[87]` at `(173,217)`.
- LFG headings y=272.
- LFG scrollbar around x=210/y=268, using Interface60/61/62.
- Five visible LFG rows start at y=293, step 21.

## GroupBagDialog
Source: `Client/Scenes/Views/GroupLootDialogs.cs`

- Background Interface246.
- 6×6 visible item grid at `(20,39)`.
- Weight bar GameInter360 `(53,280)`.
- Weight label `(53,276)`, 196×16.
- Mode/filter around y=306/325.
- Share GameInter364 `(218,309)`.
- Options `(178,309)`.
- Anchors next to GroupDialog with 4 px separation.

---

# 11. MenuDialog and its submenu graph — VERIFIED
Source: `Client/Scenes/Views/MenuDialog.cs`

- Background Interface279.
- Width 152 from source geometry.
- Seven 100-wide buttons at x=26:
  - Settings y=40 → ConfigBox.
  - Help y=70 → HelpBox.
  - Guild y=100 → GuildBox.
  - Storage y=130 → StorageBox.
  - Ranking y=160 → RankingBox.
  - Companion y=190 → CompanionBox.
  - Leave y=220 → ExitBox.

A faithful Menu implementation is not complete until these child windows exist.

## ConfigBox — VERIFIED SHELL
Source: `Client/Controls/DXConfigWindow.cs`

- Interface282.
- TabControl `(0,37)`, size357×365, MarginLeft10.
- Tabs: Graphics, Sound, Game, Network, UI.
- UI tab includes UI scale/font controls.

## HelpBox — VERIFIED SHELL
Source: `Client/Scenes/Views/HelpDialog.cs`

- GameInter9300.
- Help menu `(13,70)`.
- Content `(178,68)`, 535×312.
- Menu buttons GameInter9310/9311; spacer 9315.
- Content/tabs are populated from HelpInfo DB data.

## GuildBox — VERIFIED SHELL
Source: `Client/Scenes/Views/GuildDialog.cs`

- Interface260, explicit size456×556.
- Main tab control `(0,39)`, 456×464, MarginLeft15.
- Background Interface261 at `(0,23)`, 456×440.
- Tabs/views: Create, Home, Member, Storage, War, Style, Castle; visibility is state/permission dependent.

## StorageBox — VERIFIED SHELL
Source: `Client/Scenes/Views/StorageDialog.cs`

- Interface121.
- Storage/Parts tabs.
- TabControl `(0,61)`, size410×420, MarginLeft10.
- Storage grid starts `(19,11)`; visible height 10.
- Parts grid 10 columns; visible 10 rows.
- Opening Storage also opens Inventory in Zircon.

## RankingBox — VERIFIED CORE
Source: `Client/Scenes/Views/RankingDialog.cs`

- Interface210 normal / 211 full ranking.
- Normal size330×456; full576×456.
- Full ranking includes an inspect panel that uses the same layered character rendering concept as CharacterDialog.

## CompanionBox — VERIFIED CORE
Source: `Client/Scenes/Views/CompanionDialog.cs`

- Interface141.
- Main TabControl starts `(0,38)`.
- Companion display point `(90,140)`.
- Buttons Bonus/Filter/Bag at y=263.
- Equipment cells and bars are explicitly positioned in source.
- Subviews: Bonus, Filter, Bag.

## ExitBox — VERIFIED
Source: `Client/Scenes/Views/ExitDialog.cs`

- Interface281, modal.
- Back-to-select button `(61,45)`, width130.
- Exit button `(61,55+DefaultHeight)`, width130.

---

# 12. GameStoreDialog — VERIFIED CORE
Source: `Client/Scenes/Views/GameStoreDialog.cs`

- Background Interface310.
- Folder tree `(10,38)`, 170×305.
- Sort label near x185/y38; sort combo `(270,41)` width108.
- Search box `(385,42)` width132; Search button `(530,40)` width68.
- Item list `(199,67)`, 409×432.
- Currency title `(10,354)`, 172×20.
- Currency amount `(14,375)`, 164×18.
- Recharge `(10,410)`, 172×27.
- Currency toggle `(10,438)`, 172×27.
- Top items `(614,65)`, 174×425; title `(614,37)`.

Current ORIGINS status: **INCOMPLETE**.

---

# 13. MiniMap / BigMap — VERIFIED BEHAVIOR, BLOCKED-ASSET

## MiniMapDialog
Source: `Client/Scenes/Views/MiniMapDialog.cs`

- DXWindow, black background, no footer, close hidden.
- Default 200×200; large 300×300.
- Actual map art comes from `LibraryFile.MiniMap`, `Index = MapInfo.MiniMap`.
- If MiniMap index <= 0, height collapses to 32 and resize is disabled.
- ClientArea is inflated by 6 for its map panel.
- Size: GameInter132.
- Transparency: GameInter130/131.
- BigMap: GameInter137.
- Three buttons stack on the right and only become visible while hovering.

`3.map` / Sabuk-Prov has MiniMap index 145 in the user's `System.db`.

**BLOCKED-ASSET:** `MiniMap.Zl` has not been supplied/discovered in ORIGINS, so the map interior must stay empty rather than be faked.

## BigMapDialog
Source: `Client/Scenes/Views/BigMapDialog.cs`

- DXWindow with footer, drop shadow.
- Side panel width220; gap6.
- Max map display roughly 740×520.
- Uses the same MiniMap image source.
- Side panel has NPC/Monster tabs and map controls.

---

# 14. Other GameScene UI systems — master checklist

These are all actual GameScene UI fields and must not be silently omitted from the long-term port. `VERIFIED-SHELL` means its main source class has been located; `PENDING-AUDIT` means child geometry still needs transcription before implementation.

| system | source / status |
|---|---|
| Caption | `CaptionDialog` — PENDING-AUDIT |
| FilterDrop | `FilterDropDialog` — PENDING-AUDIT |
| ChatTextBox | `ChatTextBox` — PENDING-AUDIT |
| ChatOptions | `ChatOptionsDialog` — PENDING-AUDIT |
| NPC main | `NPCDialog` — PENDING-AUDIT |
| NPC goods | `NPCGoodsDialog` — PENDING-AUDIT |
| NPC repair | `NPCRepairDialog` — PENDING-AUDIT |
| NPC refinement stone | `NPCRefinementStoneDialog` — PENDING-AUDIT |
| NPC refine | `NPCRefineDialog` — PENDING-AUDIT |
| NPC refine retrieve | `NPCRefineRetrieveDialog` — PENDING-AUDIT |
| NPC quest list | `NPCQuestListDialog` — PENDING-AUDIT |
| NPC quest | `NPCQuestDialog` — PENDING-AUDIT |
| Adopt companion | `NPCAdoptCompanionDialog` — PENDING-AUDIT |
| Companion storage | `NPCCompanionStorageDialog` — PENDING-AUDIT |
| Wedding ring | `NPCWeddingRingDialog` — PENDING-AUDIT |
| Item fragment | `NPCItemFragmentDialog` — PENDING-AUDIT |
| Accessory upgrade/level/reset | respective NPC dialogs — PENDING-AUDIT |
| Master refine | `NPCMasterRefineDialog` — PENDING-AUDIT |
| Roll | `NPCRollDialog` — PENDING-AUDIT |
| Group loot vote | `GroupLootVoteDialog` — PENDING-AUDIT |
| Group health | `GroupHealthDialog` — PENDING-AUDIT |
| Buff | `BuffDialog` — PENDING-AUDIT |
| AutoPotion | `AutoPotionDialog` — PENDING-AUDIT |
| Inspect | `CharacterDialog(true)` — layered renderer required |
| Consignment | `ConsignmentDialog` — PENDING-AUDIT |
| DungeonFinder | `DungeonFinderDialog` — PENDING-AUDIT |
| Trade | `TradeDialog` — PENDING-AUDIT |
| GuildMember | `GuildMemberDialog` — PENDING-AUDIT |
| QuestTracker | `QuestTrackerDialog` — PENDING-AUDIT |
| MilestoneAchieved | `MilestoneAchievedDialog` — PENDING-AUDIT |
| Monster | `MonsterDialog` — PENDING-AUDIT |
| MagicBar | `MagicBarDialog` — PENDING-AUDIT |
| EditCharacter | `EditCharacterDialog` — PENDING-AUDIT |
| FortuneChecker | `FortuneCheckerDialog` — PENDING-AUDIT |
| WeaponCraft | `NPCWeaponCraftWindow` — PENDING-AUDIT |
| AccessoryRefine | `NPCAccessoryRefineDialog` — PENDING-AUDIT |
| Socket | `NPCSocketDialog` — PENDING-AUDIT |
| SocketCombine | `NPCSocketCombineDialog` — PENDING-AUDIT |
| Currency | `CurrencyDialog` — VERIFIED-SHELL: DXWindow client 227×(7×43+1), category tree |
| Timer | `TimerDialog` — PENDING-AUDIT |
| Bundle | `BundleDialog` — PENDING-AUDIT |
| LootBox | `LootBoxDialog` — PENDING-AUDIT |
| CraftingRecipe | `CraftingRecipeDialog` — PENDING-AUDIT |
| CraftingProgress | `CraftingProgressDialog` — PENDING-AUDIT |
| Fishing | `FishingDialog` — PENDING-AUDIT |
| FishingCatch | `FishingCatchDialog` — PENDING-AUDIT |
| HorseTame | `HorseTameDialog` — PENDING-AUDIT |

No `PENDING-AUDIT` system should be recreated from memory or visual guesswork.

---

# 15. ORIGINS current technical debt found by this audit

1. **Character paperdoll is wrong:** static class/gender WebP instead of ProgUse + Equip layered composition.
2. **Character stat tabs are approximated:** CSS scales a 60px tab to 40px; Zircon's tab system must generate the correct width using its button pieces, not squash a finished sprite.
3. **Character equipment cells are mostly absent as controls.** Background artwork alone is not equivalent to `DXItemCell` hitboxes/state.
4. **Belt is wrong:** fixed precomposed frame instead of resizable DXWindow + item-cell grid.
5. **MiniMap frame is approximate:** should be a DXWindow assembled from Interface pieces; actual map image is blocked by missing `MiniMap.Zl`.
6. **Menu is not complete:** Settings/Help/Guild/Storage/Ranking/Companion/Exit child dialogs must exist before Menu is considered implemented.
7. **Communication, Quest, Group and Store are shells only.** Their child controls need exact source transcription.
8. **The UI currently duplicates geometry across CSS/JS.** Move verified geometry into `data/ui/zircon-ui-spec.json`.
9. **Player runtime only supports one body manifest.** It needs a shared layered appearance renderer for world player, CharacterDialog and Inspect/Ranking where appropriate.
10. **No ProgUse/Equip browser runtime exists in repo.** Add a converter/runtime before rendering the faithful Character paperdoll.

---

# 16. Reconstruction order

Do not work on all windows visually at once. Implement shared primitives first so later windows become mechanical.

1. `DXWindow` browser primitive from exact Interface indices and source size rules.
2. `DXButton` + `DXTabControl` + `DXItemCell` primitives.
3. MainPanel exact labels/bars/buttons.
4. Shared layered `CharacterAppearanceRenderer` (ProgUse/Equip/effects).
5. CharacterDialog all tabs + all equipment cells + stats.
6. InventoryDialog + BeltDialog.
7. MenuDialog and every child: Config, Help, Guild, Storage, Ranking, Companion, Exit.
8. Communication + Group/GroupBag + Quest.
9. MiniMap/BigMap after `MiniMap.Zl` is available.
10. GameStore.
11. Remaining GameScene checklist, each only after its source class is audited.

Every completed row must move from `PENDING-AUDIT` / `CURRENT-WRONG` to `VERIFIED-IMPLEMENTED` only after a source comparison.