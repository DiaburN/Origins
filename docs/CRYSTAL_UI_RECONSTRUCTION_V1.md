# CRYSTAL UI RECONSTRUCTION V1

## Goal

Reconstruct the desktop Crystal gameplay interface exactly from the public Crystal client source and its public `.Lib` artwork before any mobile redesign.

This is NOT a visual redesign and must not use generated or invented UI art.

## Source of truth

- `Suprcode/Crystal/Client/MirScenes/GameScene.cs`
- `Suprcode/Crystal/Client/MirScenes/Dialogs/*.cs`
- `Suprcode/Crystal/Client/MirGraphics/MLibrary.cs`
- public Crystal patch UI libraries (`Prguse.Lib`, `Prguse2.Lib`, `Title.Lib`, plus other libraries only when a Crystal source dialog actually references them)

## Reference resolution

V1 reconstruction target: **1024 × 768**.

The desktop reconstruction is preserved as a reference build. Mobile adaptation comes later as a separate composition layer.

## GameScene interface inventory

GameScene creates the following gameplay UI/dialog classes:

- MainDialog
- ChatDialog
- ChatControlBar
- InventoryDialog
- CharacterDialog
- BeltDialog
- StorageDialog
- CraftDialog
- MiniMapDialog
- InspectDialog
- OptionDialog
- MenuDialog
- NPCDialog / NPCGoods / NPCDrop / NPCAwake
- HelpDialog
- KeyboardLayoutDialog
- NoticeDialog
- MountDialog
- FishingDialog / FishingStatusDialog
- GroupDialog
- GuildDialog / GuildTerritoryDialog
- Hero dialogs and panels
- BigMapDialog
- TrustMerchantDialog
- CharacterDuraPanel / DuraStatusDialog
- TradeDialog / GuestTradeDialog
- SocketDialog
- SkillBarDialog (two bars)
- ChatOptionDialog / ChatNoticeDialog
- QuestList / QuestDetail / QuestTracking / QuestDiary
- RankingDialog
- Mail dialogs
- Intelligent Creature dialogs
- RefineDialog
- Relationship / Friend / Memo / Mentor dialogs
- GameShopDialog
- ReportDialog
- Item renting dialogs
- Buff dialogs
- Timer / Compass / Roll controls

No class is to be replaced by a made-up equivalent.

## Reconstruction order

### Stage A — always-visible gameplay HUD

- MainDialog
- HP/MP orb draw
- EXP/weight bars
- Main HUD buttons
- ChatDialog
- ChatControlBar
- BeltDialog
- MiniMapDialog
- Dura/Buff controls where visible

### Stage B — main player windows

- Inventory
- Character
- Status
- State
- Skills
- Quest diary/tracking
- Options
- Menu
- BigMap
- Group
- Guild
- Mail
- Trade

### Stage C — contextual/secondary windows

NPC, crafting, storage, refine, renting, relationships, mentor, pets/creatures, fishing, hero, shop, reports and other GameScene dialogs.

## Implementation rules

1. Every background/button image is extracted from the exact Crystal library + image index referenced by source.
2. Every control position starts from the exact `Location = new Point(...)` in Crystal source.
3. Dynamic text is HTML/runtime text, not burned into PNGs.
4. Hover/pressed states use the exact `Index/HoverIndex/PressedIndex` images.
5. No generated UI image may be used as a substitute.
6. The source Zuma map is only the background behind the UI reference; it is not part of the interface reconstruction.
7. All reconstruction code stays isolated on branch `crystal-ui-v1` until approved.

## Current implementation

`apps/crystal-ui-reference/` is an interactive DOM reconstruction. The GitHub Action `build-crystal-ui-reference.yml` downloads the public Crystal libraries, extracts only required UI indices and emits a self-contained artifact.

The first interactive snapshot includes real-source implementations of:
- MainDialog
- ChatDialog
- ChatControlBar
- BeltDialog
- MiniMapDialog
- InventoryDialog
- CharacterDialog Character/Status/State/Skill pages

Remaining GameScene dialogs will be added incrementally without replacing the approved base.
