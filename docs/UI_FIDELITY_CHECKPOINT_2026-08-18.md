# ORIGINS — Zircon UI fidelity checkpoint — 2026-08-18

Branch: `origins-game-v1`
Source of truth: current `Suprcode/Zircon` C# + extracted Zircon artwork.

This checkpoint is additive to `docs/BUILD_STATUS.md`. Do not use it to replace owner approval; it records the current implementation/fidelity floor so later work does not regress already reconstructed source behavior.

## Current source inventory floor

Validated locally against a fresh download of current `Suprcode/Zircon` master:

- 65 GameScene windows.
- 15 nested/transient source windows.
- 80 unique stable viewer IDs.
- 1,634 GameScene controls.
- 143 nested controls.
- 18 direct source-backed window interactions.
- 0 unclassified custom-draw windows in the strict custom-draw audit.
- 7 explicit top-level overflow contracts; no generic overflow whitelist.
- 9 high-value complex source-action contracts in the core audit.
- All `apps/zircon-ui-reference/extra-runtimes/*.js` pass `node --check` in the local fresh-source validation pipeline.

## Fidelity work already locked

### Shared DX control behavior

- `DXWindow` source frame pieces, footer/slim-footer, title/close/chrome and reflow.
- `DXAnimatedControl` frame timing, loop semantics, per-frame source offsets and Index/BaseIndex behavior.
- `DXButton`/indexed source artwork and source text without internal control-name fallbacks.
- `DXCheckBox` source state, ReadOnly behavior, `LabelBoxPadding`, effective `Enabled`, and source custom ReadOnly click support.
- Effective `DXControl.Enabled` follows own `Enabled` plus parent chain and supports real post-constructor source overrides.
- Disabled source controls also receive disabled visual treatment.
- `DXComboBox` source options, selected label, GameInter #795 arrow, ActiveScene list, source selection/hover styling and source-like 14px scrollbar using Interface #44/#46/#45 with Change=15.
- `DXSoundBar` GameInter #4740–#4746, mute, value 0..100, click/wheel/drag.
- Generic `DXVScrollBar` / `DXHScrollBar` Value/Change/Min/Max/VisibleSize, wheel, arrows, track and thumb drag; emits source-scroll events.
- Generic `DXTextBox` / `DXNumberTextBox` local editing with source MaxLength, ReadOnly, effective Enabled and source text-change events.
- Source `Visible`, opacity, PassThrough/IsControl hit testing, tab hierarchy, modal blocking, z-order, moving and source resize behavior.

### Initial HUD / game desktop

- MainPanel source art and complete 9-button / 10-action navigation.
- Belt final constructor state 64x54.
- MiniMap final constructor state 200x200, source buttons/hover and source resize behavior; map content remains runtime-only.
- GroupHealth 150x500, opacity 0, no fabricated members.
- BuffBox 30x30, opacity 0.6, no fabricated buffs.
- Timer 120x100, source egg animation from GameInter 960..965; timer values runtime-only.
- MonsterBox expanded default 186x175 with source expand/collapse behavior.
- MagicBar 646x65 with all 24 deterministic source slots; spell/icon/cooldown data remains runtime-only.

### Reconstructed constructor loops / composites

- AutoPotion: 8 rows / 80 deterministic controls. HP/MP/Enabled and row reorder work locally; linked items and `C.AutoPotionLinkChanged` are never fabricated/executed.
- FilterDrop: 10 source labels + 10 source textboxes. Local Save updates reference `Config.HighlightedItems`; game-chat side effect remains unexecuted.
- Config `DXColourControlPair`: 13 source pairs / 26 actual `DXColourControl` swatches.
- CurrencyTree neutral structure: source border + 14px scrollbar; 0 headers/currencies until real `GameScene.User.Currencies` exist.
- Companion empty-slot deterministic help artwork Interface #99–#102 at source opacity; companion model/bars remain runtime-only.
- NPC custom frame GameInter #380/#381/#382 and special scrollbar assets #385/#387.

### Source-backed window behavior

- Config/Settings: checked-in `Config.cs` defaults, English/Chinese source language list, 5 GameScene dynamic Enabled overrides, Network tab hidden in GameScene, Key Bind source window, local sound state, 13 colour pairs + source picker/reset. Renderer/server effects are annotated but not faked.
- Inventory: neutral Normal mode, 6x8 source grid, Trash visible/Sell hidden, Wallet toggles Currency. Item/currency/weight/server data remains runtime-only.
- Storage: opens Inventory, source filters/clear/sort confirmation and Parts/Storage state; server sort packet not faked.
- Trade: source confirm state and gold modal contract; trading/server state not faked.
- Consignment: source Search/Consign tab state and dependent visibility.
- GameStore: source sort options/default and Hunt/Game Gold local state; catalog/currency data remains runtime-only.
- Communication: source tab backgrounds/visibility, Send draft reset and OnlineState combos; mail/friend/block payloads runtime-only.
- Group: neutral 0 members, AllowGroup=false awaiting server acknowledgement, Remove/Options disabled, Add uses the source nested DXInputWindow, LFG modal source flow and no fabricated LFG rows.
- Guild: true post-`ClearGuild()` no-guild state, CreateTab, Interface #266, Gold selected, 7,500,000 base cost, Create blocked without real user/name. Guild/member/storage/castle data runtime-only.
- Quest: source tabs/composites, tracker Config default true but neutral tracker stays hidden with 0 real tracked quests. Quest/NPC/reward/task data is never invented.
- Character / Inspect: Interface #110 / #115, CharacterTab source default, runtime Discipline/Hermit visibility, runtime identity/equipment/fame/guild/marriage/player preview. Constructor stat zero labels are preserved because they are genuine Zircon defaults.
- Ranking: compact GameScene variant Interface #210, 330x456; selected rank/search/online/inspect information remains runtime-only.
- Currency: runtime user currency rows remain neutral/empty.
- FilterDrop: checked-in empty filters rather than fabricated filter values.
- Exit, Chat, resize behavior and other previously locked direct interactions remain intact.

## Strict source gates

Core source gate:
- `.github/workflows/audit-zircon-source-contracts.yml`

Additive auto-discovered gate:
- `.github/workflows/audit-zircon-supplemental-contracts.yml`
- `tools/zircon-ui-importer/run_supplemental_source_contracts.py`
- New `tools/zircon-ui-importer/supplemental/augment_*.py` are run before all `supplemental/audit_*.py` automatically.

The supplemental gate currently includes strict Ranking, Group, shared scrollbar and shared textbox contracts plus a complete source MouseClick inventory.

## Non-negotiable continuation rules

1. Never fabricate player, map, item, quest, guild, ranking, mail, dungeon, NPC or server-response data into the Zircon reference.
2. Preserve genuine constructor defaults even when they are zero/blank.
3. If a source value is runtime-dependent, keep it neutral and record the source dependency.
4. Reconstruct deterministic constructor loops/composites instead of replacing them with generic placeholders.
5. New custom draws, overflows, constructor loops or local source actions must be classified/implemented rather than silently whitelisted.
6. Keep desktop/source fidelity work on `origins-game-v1`; final ORIGINS mobile/Archero redesign comes only after the desktop reference pass is owner-approved.
