# ORIGINS-DxR — Web Player Assets Step 2

- Pipeline gate: **FAIL**
- Base humans M-Hum + WM-Hum: **UNKNOWN**
- Full Zircon player payload: **UNKNOWN**
- Real base sprite binding status: **BLOCKED_MISSING_ZL**
- Origins-DxR HEAD tested: 80ad8c9fb0fcbbc1cea6a42c3224028e62c635fa
- Zircon authority: cbf1aa919083bc13fc3f23f93772a8ab8370632d

## What is implemented

- `M_Hum` (male) and `WM_Hum` (female) are one paired base-human import profile. They share the same native player animation contract; gender selects only the body library.
- `FrameSet.Players` is generated directly from pinned Zircon source, not transcribed from Crystal.
- All 42 native player animation frame definitions are represented with exact start indices, direction offsets, frame counts, per-frame delays, `Reversed` and `StaticSpeed`.
- `Functions.GetMagicAnimation` cases are generated from pinned source.
- Player action resolver covers the direct native `PlayerObject.SetAnimation` actions and deliberately refuses fabricated direct Show/Hide/Mount/Idle mappings.
- Attack resolver preserves Zircon class/weapon/magic animation choices.
- Assassin armour shifts and body/hair/helmet/weapon/shield/horse frame composition are represented.
- PlayerObject library selectors and direction-aware layer ordering are preserved, including dual weapons, shields and costume weapon-hiding rules.
- `.Zl` exporter uses pinned `LibraryEditor.Mir3Library`, creates transparent PNG atlas pages, and preserves image index + OffSetX/OffSetY.
- `--base-humans` exports M_Hum and WM_Hum together and refuses a partial pair.
- Browser sprite store maps `Male -> M_Hum` and `Female -> WM_Hum` and exposes pair readiness.

## CI

| Check | Result |
|---|---|
| Bootstrap pinned Zircon | success |
| Generate source-faithful contract | success |
| JavaScript syntax | success |
| Player animation + sprite tests | success |
| Pinned PlayerObject audit | failure |
| ZL atlas exporter build | cancelled |
| M-Hum + WM-Hum pair probe | skipped |
| All-player payload probe | skipped |

## Contract totals

- Player animations: **0**
- Magic-to-body-animation cases: **0**
- Player-related Zircon libraries: **0**
- PlayerObject selector entries: **0**
- Base human `.Zl` present: **0 / 0**
- All player `.Zl` present: **0 / 0**

## Base human pair


## Source parity audit

| Check | Result | Details |
|---|---|---|

## Real payload boundary

The source repository defines both native base body libraries as `Data/M-Hum.Zl` and `Data/WM-Hum.Zl`, but those binary payloads are not committed to Origins-DxR. They are never replaced with Crystal or invented art.

As soon as both files exist under `runtime-assets/zircon/Data/`, the exact same `--base-humans` exporter generates the male and female web atlases in one operation. No second female animation implementation is required.
