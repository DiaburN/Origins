# ORIGINS — ZIRCON UI APPROVAL MATRIX

This file records ORIGINS product decisions **after** reconstructing the complete Zircon GameScene interface.

The untouched reference remains under `apps/zircon-ui-reference/`. Never delete a Zircon reference window because ORIGINS later decides not to use it.

Allowed decisions:
- `PENDING` — not reviewed by owner yet.
- `KEEP` — keep the Zircon concept/art/layout as a base.
- `REMOVE` — ORIGINS does not need this feature/window.
- `MERGE` — combine its function with another ORIGINS window later.
- `MOBILE_REDESIGN` — feature stays but mobile layout will differ.
- `DEFER` — keep reference but do not implement in first playable slice.

| Zircon GameScene component | ORIGINS decision | Notes |
|---|---|---|
| MainPanel | PENDING | Desktop reference preserved |
| MenuBox | PENDING | |
| ConfigBox | PENDING | |
| HelpBox | PENDING | |
| CaptionBox | PENDING | |
| InventoryBox | PENDING | |
| CharacterBox | PENDING | |
| FilterDropBox | PENDING | |
| ExitBox | PENDING | |
| ChatTextBox | PENDING | |
| BeltBox | PENDING | |
| ChatOptionsBox | PENDING | |
| NPCBox | PENDING | |
| NPCGoodsBox | PENDING | |
| NPCRepairBox | PENDING | |
| NPCRefinementStoneBox | PENDING | |
| NPCRefineBox | PENDING | |
| NPCRefineRetrieveBox | PENDING | |
| NPCQuestListBox | PENDING | |
| NPCQuestBox | PENDING | |
| NPCAdoptCompanionBox | PENDING | |
| NPCCompanionStorageBox | PENDING | |
| NPCWeddingRingBox | PENDING | |
| NPCItemFragmentBox | PENDING | |
| NPCAccessoryUpgradeBox | PENDING | |
| NPCAccessoryLevelBox | PENDING | |
| NPCAccessoryResetBox | PENDING | |
| NPCMasterRefineBox | PENDING | |
| NPCRollBox | PENDING | |
| MiniMapBox | PENDING | |
| BigMapBox | PENDING | |
| MagicBox | PENDING | |
| GroupBox | PENDING | |
| GroupHealthBox | PENDING | |
| BuffBox | PENDING | |
| StorageBox | PENDING | |
| AutoPotionBox | PENDING | |
| InspectBox | PENDING | |
| RankingBox | PENDING | |
| GameStoreBox | PENDING | |
| ConsignmentBox | PENDING | |
| DungeonFinderBox | PENDING | |
| CommunicationBox | PENDING | |
| TradeBox | PENDING | |
| GuildBox | PENDING | |
| GuildMemberBox | PENDING | |
| QuestBox | PENDING | |
| QuestTrackerBox | PENDING | |
| MilestoneAchievedBox | PENDING | |
| CompanionBox | PENDING | |
| MonsterBox | PENDING | |
| MagicBarBox | PENDING | |
| EditCharacterBox | PENDING | |
| FortuneCheckerBox | PENDING | |
| NPCWeaponCraftBox | PENDING | |
| NPCAccessoryRefineBox | PENDING | |
| NPCSocketBox | PENDING | |
| NPCSocketCombineBox | PENDING | |
| CurrencyBox | PENDING | |
| TimerBox | PENDING | |
| BundleBox | PENDING | |
| LootBoxBox | PENDING | |
| FishingBox | PENDING | |
| FishingCatchBox | PENDING | |
| HorseTameBox | PENDING | |

## Approval rule

Only the project owner changes `PENDING` to a product decision. A developer may add technical notes, but must not decide that a Zircon feature is unnecessary on their own.
