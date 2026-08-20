# ORIGINS-DxR — Web Runtime Step 1

- Gate: **PASS**
- Origins-DxR HEAD tested: 3ba24c1277925b1916984b2f1bd62b87e7c7bf1a
- Zircon authority: cbf1aa919083bc13fc3f23f93772a8ab8370632d
- Client target: browser / mobile web
- Runtime mode: `PREVIEW_LOCAL` (not server-authoritative yet)

## CI

| Check | Result |
|---|---|
| Bootstrap pinned Zircon | success |
| JavaScript syntax | success |
| Runtime unit tests | success |
| Pinned source audit | success |
| Static HTTP smoke | success |

## Runtime contract

- Dedicated app: `apps/origins-web-runtime/`.
- Closed UI reference remains separate at `apps/zircon-ui-reference/`.
- Fixed simulation step: 60 Hz.
- Keyboard: WASD/arrows.
- Touch: eight directional controls.
- Camera follows the preview PlayerObject.
- MirDirection and MirAction values are audited against pinned Zircon `LibraryCore/Enum.cs`.
- Browser does not open `System.db` or `Users.db` directly.
- No Crystal runtime dependency.
- No WebSocket/gameplay authority is fabricated in Step 1.
- The PLAYER marker is diagnostic only; real Zircon frames enter in Step 2/4.

## Source audit checks

| Check | Result | Details |
|---|---|---|
| Pinned MirDirection source | PASS | [('Up', 0), ('UpRight', 1), ('Right', 2), ('DownRight', 3), ('Down', 4), ('DownLeft', 5), ('Left', 6), ('UpLeft', 7)] |
| Pinned MirAction source | PASS | [('Standing', 0), ('Moving', 1), ('Pushed', 2), ('Attack', 3), ('RangeAttack', 4), ('Spell', 5), ('Harvest', 6), ('Struck', 7), ('Die', 8), ('Dead', 9), ('Show', 10), ('Hide', 11), ('Mount', 12), ('Mining', 13), ('Fishing', 14), ('Taming', 15), ('Idle', 16)] |
| Web MirDirection parity | PASS | [('Up', 0), ('UpRight', 1), ('Right', 2), ('DownRight', 3), ('Down', 4), ('DownLeft', 5), ('Left', 6), ('UpLeft', 7)] |
| Web MirAction parity | PASS | [('Standing', 0), ('Moving', 1), ('Pushed', 2), ('Attack', 3), ('RangeAttack', 4), ('Spell', 5), ('Harvest', 6), ('Struck', 7), ('Die', 8), ('Dead', 9), ('Show', 10), ('Hide', 11), ('Mount', 12), ('Mining', 13), ('Fishing', 14), ('Taming', 15), ('Idle', 16)] |
| Pinned source commit declared | PASS | cbf1aa919083bc13fc3f23f93772a8ab8370632d |
| Fixed simulation step | PASS | 1/60 second |
| Preview PlayerObject model | PASS | present |
| Browser render loop | PASS | requestAnimationFrame |
| Canvas game surface | PASS | present |
| Eight-way touch input | PASS | diagonal controls present |
| No Crystal runtime dependency | PASS | no Crystal token in active Step 1 runtime |
| Browser does not open MirDB files | PASS | no direct DB paths in runtime |
| No fake network authority in Step 1 | PASS | WebSocket deliberately absent until transport step |
| Preview-only mode explicit | PASS | PREVIEW_LOCAL visible in runtime |

## What this PASS proves

A browser runtime exists and can execute a deterministic local PlayerObject preview with the native Zircon action/direction contract. It does **not** yet prove real map rendering, native sprite rendering, WebSocket transport, server-authoritative movement, combat or login.

Next approved runtime block: **Step 2 — Zircon asset pipeline**.
