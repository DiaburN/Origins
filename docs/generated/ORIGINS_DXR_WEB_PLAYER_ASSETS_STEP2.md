# ORIGINS-DxR — Web Player Assets Step 2

- Pipeline gate: **PASS**
- Real Zircon player payload: **BLOCKED_MISSING_ZL**
- Real sprite binding status: **BLOCKED_MISSING_ZL**
- Origins-DxR HEAD tested: 68061a6b10aa10614e5eb106f461a3de43ee9c4d
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
| Bootstrap pinned Zircon | success |
| Generate source-faithful contract | success |
| JavaScript syntax | success |
| Player animation tests | success |
| Pinned PlayerObject audit | success |
| ZL atlas exporter build | success |
| Player payload probe | success |

## Contract totals

- Player animations: **42**
- Magic-to-body-animation cases: **124**
- Player-related Zircon libraries: **137**
- Required `.Zl` present in repository/runtime payload: **0 / 137**

## Source parity audit

| Check | Result | Details |
|---|---|---|
| Generated contract schema | PASS | origins.zircon.web-player-assets.v1 |
| All FrameSet.Players entries | PASS | count=42 |
| Player frames are MirAnimation values | PASS | frames=42, enum=46 |
| Magic animation map extracted | PASS | cases=124 |
| Core body libraries | PASS | M_Hum, M_HumA, WM_Hum, WM_HumA |
| Player layer library families | PASS | libraries=137 |
| Female offset | PASS | 5000 |
| Assassin offset | PASS | 50000 |
| Right-hand offset | PASS | 50 |
| All PlayerObject selector dictionaries extracted | PASS | ArmourList=30, CostumeList=6, WeaponList=52, ShieldList=4, HelmetList=30 |
| Male/female body selectors | PASS | M_Hum / WM_Hum |
| Assassin body selectors | PASS | M_HumA / WM_HumA |
| Assassin dual weapon selectors | PASS | ADL/ADR |
| Costume weapon-hide list | PASS | [6, 7, 8, 9, 10, 11, 12, 13, 16, 17, 18] |
| Web PlayerObject library selection | PASS | body/hair/helmet/weapon/shield/horse selection |
| Pinned DrawFrame formula | PASS | DrawFrame = FrameIndex + CurrentFrame.StartIndex + CurrentFrame.OffSet * (int)Direction; |
| Web DrawFrame formula | PASS | start + local + offset*direction |
| Pinned Player Pushed override | PASS | Player Pushed -> frame 0 |
| Web Player Pushed override | PASS | Player Pushed -> contract frame 0 |
| Action mapping Standing | PASS | pinned PlayerObject + web resolver |
| Action mapping Moving | PASS | pinned PlayerObject + web resolver |
| Action mapping Pushed | PASS | pinned PlayerObject + web resolver |
| Action mapping Attack | PASS | pinned PlayerObject + web resolver |
| Action mapping Mining | PASS | pinned PlayerObject + web resolver |
| Action mapping Fishing | PASS | pinned PlayerObject + web resolver |
| Action mapping Taming | PASS | pinned PlayerObject + web resolver |
| Action mapping RangeAttack | PASS | pinned PlayerObject + web resolver |
| Action mapping Spell | PASS | pinned PlayerObject + web resolver |
| Action mapping Struck | PASS | pinned PlayerObject + web resolver |
| Action mapping Die | PASS | pinned PlayerObject + web resolver |
| Action mapping Dead | PASS | pinned PlayerObject + web resolver |
| Action mapping Harvest | PASS | pinned PlayerObject + web resolver |
| No fabricated direct Show/Hide/Mount/Idle | PASS | Show, Hide, Mount, Idle |
| Pinned attack animation branches | PASS | GetAttackAnimation branches present |
| Web attack animation resolver | PASS | weapon/class conditional resolver present |
| Assassin ArmourShift support | PASS | native shifts + Combat2 carry-over |
| Layer frame composition | PASS | body/hair/helmet/weapon/shield/horse |
| Pinned direction-aware DrawBody order | PASS | weapon/shield before/after body branches present |
| Web direction-aware draw plan | PASS | weapon/shield/body/head depth plan |
| Horse draw-order support | PASS | horse first + dark/royal overlay |
| Exporter reads Zircon Mir3Library | PASS | LibraryEditor.Mir3Library |
| Exporter preserves image offsets | PASS | OffSetX/OffSetY -> manifest |
| Exporter writes PNG atlas | PASS | RGBA atlas pages |
| Browser applies Zircon offsets | PASS | atlas frame offsets used at draw time |
| Browser uses pixel rendering | PASS | nearest/pixel rendering |
| No Crystal runtime fallback | PASS | no Crystal paths or archive runtime references |

## Real payload boundary

The repository does not currently contain the native Zircon player `.Zl` payload. This is not replaced with Crystal or placeholder art. Therefore the importer/exporter pipeline can be validated and compiled now, but a real `M-Hum` sprite cannot honestly be marked imported until the matching `.Zl` files are supplied under the runtime asset source root.

When the payload is present, the same exporter can process `M_Hum` first or `--all-player-libraries` without rewriting the player animation runtime.
