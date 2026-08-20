# ORIGINS-DxR core bootstrap status

- Gate: **FAIL**
- Origins-DxR source HEAD tested: 6d99b30a66db838fd7b1e0fb3ca9ae51759d4c49
- Zircon expected: cbf1aa919083bc13fc3f23f93772a8ab8370632d
- Zircon actual: cbf1aa919083bc13fc3f23f93772a8ab8370632d
- Runner: Windows / GitHub Actions 1000002691
- UTC: 2026-08-20T00:23:41Z
- Rebuilt database/System.db: 5751925 bytes

| Check | Result |
|---|---|
| Bootstrap pinned Zircon | success |
| Snapshot compatibility | success |
| Snapshot compatibility commit | success |
| No active Crystal build/bootstrap refs | success |
| LibraryCore build | success |
| ServerLibrary build | success |
| Server build | success |
| Client build | success |
| Four class selectors | success |
| Origins DB tools build | success |
| System.db rebuild | success |
| System.db verify | success |
| MagicInfo deterministic round-trip | failure |
| Four-class MagicType catalog audit | success |
| Four-class MagicInfo audit | success |
| Zircon magic runtime handler audit | success |
| Runtime entrypoint/config preflight | success |

## Scope note

This gate proves source bootstrap, compilation, canonical System.db reconstruction/verification, four-class selection wiring and static runtime entrypoint/config presence. It does not claim a successful interactive GUI login on a hosted Actions runner; entering the world additionally requires runtime client data/libraries, server runtime configuration and a writable user database to be staged.

## Failure tail: roundtrip

```text
Library.SystemModels.MilestoneInfoTask: 0 (collection index 0)
Library.SystemModels.MineInfo: 20 (collection index 20)
Library.SystemModels.MonsterEventAction: 0 (collection index 0)
Library.SystemModels.MonsterEventInfo: 0 (collection index 0)
Library.SystemModels.MonsterEventInfoTriggerStat: 0 (collection index 0)
Library.SystemModels.MonsterEventTrigger: 0 (collection index 0)
Library.SystemModels.MonsterInfo: 309 (collection index 359)
Library.SystemModels.MonsterInfoStat: 4117 (collection index 4861)
Library.SystemModels.MovementInfo: 554 (collection index 3048)
Library.SystemModels.NPCAction: 288 (collection index 306)
Library.SystemModels.NPCButton: 338 (collection index 350)
Library.SystemModels.NPCCheck: 430 (collection index 451)
Library.SystemModels.NPCGood: 332 (collection index 867)
Library.SystemModels.NPCInfo: 125 (collection index 140)
Library.SystemModels.NPCPage: 302 (collection index 338)
Library.SystemModels.NPCRequirement: 0 (collection index 0)
Library.SystemModels.NPCType: 73 (collection index 98)
Library.SystemModels.NPCValue: 2 (collection index 2)
Library.SystemModels.PlayerEventAction: 0 (collection index 0)
Library.SystemModels.PlayerEventInfo: 0 (collection index 0)
Library.SystemModels.PlayerEventInfoTriggerStat: 0 (collection index 0)
Library.SystemModels.PlayerEventTrigger: 0 (collection index 0)
Library.SystemModels.QuestInfo: 34 (collection index 62)
Library.SystemModels.QuestRequirement: 58 (collection index 143)
Library.SystemModels.QuestReward: 34 (collection index 141)
Library.SystemModels.QuestTask: 42 (collection index 74)
Library.SystemModels.QuestTaskMonsterDetails: 54 (collection index 97)
Library.SystemModels.RespawnInfo: 1471 (collection index 5749)
Library.SystemModels.SafeZoneInfo: 13 (collection index 44)
Library.SystemModels.SetInfo: 30 (collection index 30)
Library.SystemModels.SetInfoStat: 200 (collection index 214)
Library.SystemModels.StoreInfo: 92 (collection index 136)
Library.SystemModels.SystemDatabaseInfo: 1 (collection index 1)
Library.SystemModels.WeaponCraftStatInfo: 110 (collection index 142)
Library.SystemModels.WorldEventAction: 0 (collection index 0)
Library.SystemModels.WorldEventInfo: 0 (collection index 0)
Library.SystemModels.WorldEventInfoTriggerStat: 0 (collection index 0)
Library.SystemModels.WorldEventTrigger: 0 (collection index 0)
canonical=472E4C143EDDA897262B5956E77252A3CE6F40CF2593C128C427633FA7234600
rebuilt=EA2748AF5D469C2A8E758C2632A284BE888350E2638E8D79A98DABA087047DC7
```
