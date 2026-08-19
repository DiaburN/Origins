# Zircon UI reconstruction for ORIGINS

## Status

This branch reconstructs the current public `Suprcode/Zircon` desktop UI from its real source code and matching current public `.Zl` data files. It is a reference implementation for ORIGINS. Mobile adaptation must happen only after this desktop reference has been visually approved.

## Non-negotiable rules

- Do not generate, redraw or invent Zircon UI artwork.
- Do not mix Crystal UI artwork into the Zircon GameInter.
- Source geometry comes from `Suprcode/Zircon` (`LibraryFile`, `Index`, `Location`, `Size`, visibility and control hierarchy).
- Source artwork comes from the matching current Zircon patch data.
- Dynamic text and runtime values are rendered separately; they are not burned into extracted PNG assets.
- Preserve source library/index provenance for every extracted image.
- Do not delete or replace the existing Crystal, map-engine or character-movement work.

## Authoritative UI libraries

Zircon maps these files through `LibraryCore/Libraries.cs`:

- `GameInter.Zl`
- `GameInter2.Zl`
- `Interface.Zl`
- `Equip.Zl`
- `Inventory.Zl`
- `MIcon.Zl`
- `QuestIcons.Zl`
- `MiniMapIcon.Zl`
- `CBIcons.Zl`

The build workflow downloads the current public files from the LOMCN/MirFiles Zircon patch mirror. The repository does not vendor the raw client data.

## MainPanel source layout

`Client/Scenes/Views/MainPanel.cs`:

- background: `GameInter #50`, 1024x68
- experience frame: `#51`, fill `#56`
- HP: `#52`, `(35,22)`
- MP: `#54`, `(35,36)`
- Focus: `#58`, full glow `#59`, `(35,50)`
- Character: `#82`, `(650,23)`
- Inventory: `#87`, `(689,23)`
- Magic: `#92`, `(728,23)`
- Quest: `#112`, `(767,23)`
- Mail: `#97`, `(806,23)`
- Belt: `#107`, `(845,23)`
- Group: `#102`, `(884,23)`
- Menu: `#117`, `(923,23)`
- Cash shop: `#122`, `(972,16)`

The extracted `#50` width establishes the 1024px desktop reference width.

## Primary source windows

- Character: `Interface #110` (`#111` Hermit, `#112` Discipline; inspect uses `#115`).
- Inventory: `Interface #130`.
- Magic: reusable `DXWindow` plus `Interface #160-163` class header and `#164` body.
- Quest: `Interface #291-293`.
- Menu: `Interface #279`.
- MiniMap: reusable `DXWindow`, 200x200 default / 300x300 large.
- Belt: reusable resizable `DXWindow`, maximum 10 cells.
- Chat: two default transparent `ChatTab` areas plus `ChatTextBox` when input is active.

## GameScene window inventory

The reconstruction must retain coverage for every user-facing window instantiated by `GameScene`, including:

MainPanel, Menu, Config, Help, Caption, Inventory, Character/Inspect, FilterDrop, Exit, ChatTextBox, Belt, ChatOptions, NPC and NPC service dialogs, MiniMap, BigMap, Magic, Group, GroupHealth, Buff, Storage, AutoPotion, Ranking, GameStore, Consignment, DungeonFinder, Communication/Mail, Trade, Guild/GuildMember, Quest/QuestTracker/Milestone, Companion, Monster, MagicBar, EditCharacter, FortuneChecker, Currency, Timer, weapon/accessory/socket crafting, fishing, horse tame, Bundle and LootBox.

## Reconstruction phases

1. Exact default gameplay HUD.
2. Primary HUD-opened windows.
3. Remaining `GameScene` dialogs.
4. Interactions/state changes and responsive reference harness.
5. Only after approval: ORIGINS mobile GameInter derived from this reference.
