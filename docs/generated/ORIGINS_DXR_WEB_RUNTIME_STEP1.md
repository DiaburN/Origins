# ORIGINS-DxR — Web Runtime Foundation

- Gate: **PASS**
- Origins-DxR HEAD tested: `2218ff5a4499928b90551ea3d5d19f367d349577`
- Zircon authority: `cbf1aa919083bc13fc3f23f93772a8ab8370632d`
- Runtime mode: `PREVIEW_LOCAL` (server-authoritative transport is a later vertical-slice step).

## CI

| Check | Result |
|---|---|
| Bootstrap pinned Zircon | success |
| JavaScript syntax | success |
| Runtime unit tests | success |
| Pinned source audit | success |
| Static HTTP smoke | success |

## Runtime contract

- Dedicated runtime: `apps/origins-web-runtime/`; the closed Zircon UI reference remains separate.
- Fixed 60 Hz simulation with keyboard and touch movement.
- `MirDirection` and `MirAction` remain audited against pinned Zircon.
- Real M-Hum/WM-Hum atlases are consumed through the sprite store when present.
- Player visual composition now resolves native body/hair/helmet/weapon1/weapon2/shield/horse libraries, frame indices and direction-dependent draw order.
- Normal W/W/T body banks use the Zircon +5000 stride; Assassin bodies use +3000 and animation-specific `ArmourShift` values, including Fishing +80.
- Browser does not open `System.db`/`Users.db` and no Crystal runtime fallback exists.

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

## Boundary

- This PASS validates the browser runtime and visual-composition contracts. It does not claim server-authoritative movement, a real map, combat, or login.
- Asset availability is audited separately; a correct requested frame can still be an upstream empty slot.
