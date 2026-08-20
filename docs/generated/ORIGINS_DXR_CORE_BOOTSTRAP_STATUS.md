# ORIGINS-DxR core bootstrap status

- Gate: **FAIL**
- Origins-DxR source HEAD tested: $sourceHead
- Zircon expected: cbf1aa919083bc13fc3f23f93772a8ab8370632d
- Zircon actual: $zirconHead
- Runner: Windows / GitHub Actions 1000002686
- UTC: 2026-08-20T00:10:31Z
- Rebuilt Database/System.db: 0 bytes

| Check | Result |
|---|---|
| Bootstrap pinned Zircon | success |
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
| Four-class MagicType catalog audit | failure |
| Four-class MagicInfo audit | failure |
| Zircon magic runtime handler audit | failure |
| Runtime entrypoint/config preflight | failure |

## Scope note

This gate proves source bootstrap, compilation, canonical System.db reconstruction/verification, four-class selection wiring and static runtime entrypoint/config presence. It does **not** claim a successful interactive GUI login on a hosted Actions runner; entering the world additionally requires the runtime client data/libraries, server runtime configuration and writable user database to be staged.

## Failure tail: magicruntime

```text
Traceback (most recent call last):
  File "D:\a\Origins\Origins\scripts\audit-zircon-four-class-runtime.py", line 231, in <module>
    raise SystemExit(main())
                     ^^^^^^
  File "D:\a\Origins\Origins\scripts\audit-zircon-four-class-runtime.py", line 72, in main
    catalog = json.loads(args.catalog.read_text(encoding="utf-8"))
                         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\hostedtoolcache\windows\Python\3.12.10\x64\Lib\pathlib.py", line 1027, in read_text
    with self.open(mode='r', encoding=encoding, errors=errors) as f:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\hostedtoolcache\windows\Python\3.12.10\x64\Lib\pathlib.py", line 1013, in open
    return io.open(self, mode, buffering, encoding, errors, newline)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
FileNotFoundError: [Errno 2] No such file or directory: 'database\\magic\\zircon-four-class-magic-types.json'
```

## Failure tail: magicdb

```text
Traceback (most recent call last):
  File "D:\a\Origins\Origins\scripts\audit-zircon-four-class-db.py", line 134, in <module>
    raise SystemExit(main())
                     ^^^^^^
  File "D:\a\Origins\Origins\scripts\audit-zircon-four-class-db.py", line 29, in main
    catalog = json.loads(args.catalog.read_text(encoding="utf-8"))
                         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\hostedtoolcache\windows\Python\3.12.10\x64\Lib\pathlib.py", line 1027, in read_text
    with self.open(mode='r', encoding=encoding, errors=errors) as f:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\hostedtoolcache\windows\Python\3.12.10\x64\Lib\pathlib.py", line 1013, in open
    return io.open(self, mode, buffering, encoding, errors, newline)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
FileNotFoundError: [Errno 2] No such file or directory: 'database\\magic\\zircon-four-class-magic-types.json'
```

## Failure tail: runtime

```text
missing Database/System.db
```

## Failure tail: catalog

```text
Traceback (most recent call last):
  File "D:\a\Origins\Origins\scripts\verify-zircon-four-class-magics.py", line 124, in <module>
    raise SystemExit(main())
                     ^^^^^^
  File "D:\a\Origins\Origins\scripts\verify-zircon-four-class-magics.py", line 74, in main
    catalog = json.loads(args.catalog.read_text(encoding="utf-8"))
                         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\hostedtoolcache\windows\Python\3.12.10\x64\Lib\pathlib.py", line 1027, in read_text
    with self.open(mode='r', encoding=encoding, errors=errors) as f:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\hostedtoolcache\windows\Python\3.12.10\x64\Lib\pathlib.py", line 1013, in open
    return io.open(self, mode, buffering, encoding, errors, newline)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
FileNotFoundError: [Errno 2] No such file or directory: 'database\\magic\\zircon-four-class-magic-types.json'
```

## Failure tail: roundtrip

```text
System.db not found: D:\a\Origins\Origins\Database\System.db
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

## Failure tail: rebuild

```text
Snapshot manifest not found: D:\a\Origins\Origins\database\generated\zircon-system\manifest.json
```
