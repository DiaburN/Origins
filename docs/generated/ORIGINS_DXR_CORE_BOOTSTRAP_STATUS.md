# ORIGINS-DxR core bootstrap status

- Gate: **FAIL**
- Origins-DxR source HEAD tested: 827360645528169091d1ddbab221a842ba239d4e
- Zircon expected: cbf1aa919083bc13fc3f23f93772a8ab8370632d
- Zircon actual: cbf1aa919083bc13fc3f23f93772a8ab8370632d
- Runner: Windows / GitHub Actions 1000002689
- UTC: 2026-08-20T00:19:36Z
- Rebuilt database/System.db: 0 bytes

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
| System.db rebuild | failure |
| System.db verify | failure |
| MagicInfo deterministic round-trip | failure |
| Four-class MagicType catalog audit | success |
| Four-class MagicInfo audit | success |
| Zircon magic runtime handler audit | success |
| Runtime entrypoint/config preflight | failure |

## Scope note

This gate proves source bootstrap, compilation, canonical System.db reconstruction/verification, four-class selection wiring and static runtime entrypoint/config presence. It does not claim a successful interactive GUI login on a hosted Actions runner; entering the world additionally requires runtime client data/libraries, server runtime configuration and a writable user database to be staged.

## Failure tail: rebuild

```text
ORIGINS SYSTEM.DB IMPORT: ERROR
System.InvalidOperationException: Library.SystemModels.MapInfo.FireWallCount: property not found in pinned Zircon model.
   at Program.<Main>$(String[] args) in D:\a\Origins\Origins\tools\Origins.Database.Import\Program.cs:line 159
```

## Failure tail: verify

```text
System.db version: <none>
BaseStats: 0
Currencies: 0
Items: 0
Magics: 0
Maps: 0
Monsters: 0
ORIGINS DB PREFLIGHT: FAIL
- System.db does not exist.
- Items collection is empty.
- Maps collection is empty.
- Monsters collection is empty.
- Magics collection is empty.
- BaseStats collection is empty.
- Currencies collection is empty.
- CurrencyType.Gold is missing; current Zircon server startup expects it.
```

## Failure tail: roundtrip

```text
System.db not found: D:\a\Origins\Origins\database\System.db
```

## Failure tail: runtime

```text
missing database/System.db
```
