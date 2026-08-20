# ORIGINS-DxR — Web Player Assets Step 2

- Pipeline gate: **FAIL**
- Real Zircon player payload: **UNKNOWN**
- Real sprite binding status: **BLOCKED_MISSING_ZL**
- Origins-DxR HEAD tested: c4c89fbe795904d0774a9e3c89e638e01ac3e230
- Zircon authority: cbf1aa919083bc13fc3f23f93772a8ab8370632d

## What is implemented

- `FrameSet.Players` is generated directly from pinned Zircon source, not transcribed from Crystal.
- All 42 native player animation frame definitions are represented with exact start indices, direction offsets, frame counts, per-frame delays, `Reversed` and `StaticSpeed`.
- `Functions.GetMagicAnimation` cases are generated from pinned source.
- Player action resolver covers the direct native `PlayerObject.SetAnimation` actions and deliberately refuses fabricated direct Show/Hide/Mount/Idle mappings.
- Attack resolver preserves Zircon class/weapon/magic animation choices.
- Assassin armour shifts and body/hair/helmet/weapon/shield/horse frame composition are represented.
- `.Zl` exporter uses pinned `LibraryEditor.Mir3Library`, creates transparent PNG atlas pages, and preserves image index + OffSetX/OffSetY.
- Browser sprite store consumes those atlas manifests and applies the original offsets.

## CI

| Check | Result |
|---|---|
| Bootstrap pinned Zircon | skipped |
| Generate source-faithful contract | skipped |
| JavaScript syntax | skipped |
| Player animation tests | skipped |
| Pinned PlayerObject audit | skipped |
| ZL atlas exporter build | skipped |
| Player payload probe | skipped |

## Contract totals

- Player animations: **0**
- Magic-to-body-animation cases: **0**
- Player-related Zircon libraries: **0**
- Required `.Zl` present in repository/runtime payload: **0 / 0**

## Source parity audit

| Check | Result | Details |
|---|---|---|

## Real payload boundary

The repository does not currently contain the native Zircon player `.Zl` payload. This is not replaced with Crystal or placeholder art. Therefore the importer/exporter pipeline can be validated and compiled now, but a real `M-Hum` sprite cannot honestly be marked imported until the matching `.Zl` files are supplied under the runtime asset source root.

When the payload is present, the same exporter can process `M_Hum` first or `--all-player-libraries` without rewriting the player animation runtime.
