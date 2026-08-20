# ORIGINS-DxR core bootstrap status

- Gate: **PASS**
- Origins-DxR source HEAD tested: 22bc7572063d188d0254c840ff3e6b16fb3eea10
- Zircon expected: cbf1aa919083bc13fc3f23f93772a8ab8370632d
- Zircon actual: cbf1aa919083bc13fc3f23f93772a8ab8370632d
- Runner: Windows / GitHub Actions 1000002696
- UTC: 2026-08-20T00:28:41Z
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
| MagicInfo semantic round-trip | success |
| Four-class MagicType catalog audit | success |
| Four-class MagicInfo audit | success |
| Zircon magic runtime handler audit | success |
| Runtime entrypoint/config preflight | success |

## Scope note

This gate proves source bootstrap, compilation, canonical System.db reconstruction/verification, four-class selection wiring and static runtime entrypoint/config presence. It does not claim a successful interactive GUI login on a hosted Actions runner; entering the world additionally requires runtime client data/libraries, server runtime configuration and a writable user database to be staged.
