# ORIGINS — COMPLETE ZIRCON GAMEINTER SCOPE

Branch: `origins-game-v1`

## Decision

ORIGINS keeps a **complete desktop reconstruction of Zircon's in-game GameScene UI** as the visual/source reference. We do not remove Zircon windows while reconstructing. Product decisions about what ORIGINS keeps, hides, merges or redesigns happen only after the complete reference can be inspected.

This reference is not the final mobile layout. Mobile adaptation is a later layer built from the approved desktop reference.

## Authoritative source

- Source code: `Suprcode/Zircon`
- In-game registry: `Client/Scenes/GameScene.cs`
- UI source classes: `Client/Scenes/Views/**` plus reusable controls in `Client/Controls/**`
- Library map: `LibraryCore/Libraries.cs`
- Current public graphical data: matching Zircon patch `.Zl` files from the public LOMCN/MirFiles mirror.

No AI-generated replacement artwork is valid for this reference.

## Complete GameScene registry

The current source creates 65 registered in-game UI/HUD components in the ORIGINS reference inventory, including `MainPanel`.

### Persistent / HUD
- MainPanel
- BeltBox
- MiniMapBox
- GroupHealthBox
- BuffBox
- TimerBox
- QuestTrackerBox
- MonsterBox
- MagicBarBox

### Character / inventory / magic
- CharacterBox
- InspectBox
- InventoryBox
- MagicBox
- CompanionBox
- EditCharacterBox
- StorageBox

### Maps / gameplay / quests
- BigMapBox
- QuestBox
- MilestoneAchievedBox
- DungeonFinderBox
- FishingBox
- FishingCatchBox
- HorseTameBox

### Communication / social
- ChatTextBox
- ChatOptionsBox
- CommunicationBox
- GroupBox
- GuildBox
- GuildMemberBox
- RankingBox

### Trade / economy
- TradeBox
- GameStoreBox
- ConsignmentBox
- CurrencyBox
- BundleBox
- LootBoxBox

### System
- MenuBox
- ConfigBox
- HelpBox
- CaptionBox
- FilterDropBox
- ExitBox
- AutoPotionBox

### NPC / service windows
- NPCBox
- NPCGoodsBox
- NPCRepairBox
- NPCRefinementStoneBox
- NPCRefineBox
- NPCRefineRetrieveBox
- NPCQuestListBox
- NPCQuestBox
- NPCAdoptCompanionBox
- NPCCompanionStorageBox
- NPCWeddingRingBox
- NPCItemFragmentBox
- NPCAccessoryUpgradeBox
- NPCAccessoryLevelBox
- NPCAccessoryResetBox
- NPCMasterRefineBox
- NPCRollBox
- FortuneCheckerBox
- NPCWeaponCraftBox
- NPCAccessoryRefineBox
- NPCSocketBox
- NPCSocketCombineBox

The machine-readable list lives in:

`apps/zircon-ui-reference/game-scene-windows.js`

## Reconstruction pipeline

The build no longer relies on a manually maintained list of a few image indices.

1. GitHub Actions checks out the current `Suprcode/Zircon` source.
2. `tools/zircon-ui-importer/build_ui_source_spec.py` parses `GameScene` and each registered UI class.
3. It records source class, base class, default visibility/location expressions, root LibraryFile/Index/Size properties and declarative child controls.
4. It records the `.Zl` image IDs referenced by those controls.
5. `build_full_reference_assets.py` downloads only those public `.Zl` libraries and extracts the required PNGs.
6. `apps/zircon-ui-reference/` renders a navigable desktop catalog at 1024x768.
7. Unresolved C# expressions remain explicitly unresolved; the renderer must never fabricate an image index or source library.

## Validation philosophy

There are two levels of reconstruction:

- **Exact image-backed:** the source class uses a concrete `.Zl` image/index and the viewer displays that exact art.
- **Source-driven reusable-control:** Zircon builds the window from reusable `DXWindow`, label, list, tab, grid and button controls. The viewer reconstructs those from the source specification and the common Interface library.

When a layout expression depends on runtime dimensions/data, the source expression is preserved instead of pretending a guessed coordinate is original.

## Approval workflow

1. Keep the complete Zircon reference intact.
2. Inspect every group in the desktop catalog.
3. Mark ORIGINS decisions separately: `KEEP`, `REMOVE`, `MERGE`, `MOBILE_REDESIGN`, `DEFER`.
4. Do not modify the reference to represent those product choices.
5. Build final ORIGINS UI under `packages/ui/` and `apps/game-web/` from the approved decisions.

This lets us always compare ORIGINS against the untouched Zircon reference.
