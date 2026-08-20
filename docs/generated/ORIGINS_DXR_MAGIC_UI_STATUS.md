# ORIGINS-DxR — Magic UI authority contract

- Gate: **PASS**
- Zircon authority: `cbf1aa919083bc13fc3f23f93772a8ab8370632d`
- Canonical MagicInfo rows visible to presentation: **174**
- Browser role: **presentation only**; no spell-key mutation, no gameplay packet enqueue.
- Native Zircon role: class/school filtering, ItemRequired, learned state, experience, SpellSet 1–4, Spell01–24, duplicate-key eviction, icon update and cooldown authority.

| Class | MagicInfo rows |
|---|---:|
| Warrior | 32 |
| Wizard | 42 |
| Taoist | 47 |
| Assassin | 53 |

## Verified native contracts

- `MagicDialog.CreateTabs()` uses Zircon `Globals.MagicInfoList` and the current `MapObject.User` class/magics.
- `MagicCell` reads `MagicInfo.Icon/Name/NeedLevel/Experience` and native `ClientUserMagic` state.
- `MagicCell.Image_KeyDown` owns key assignment and removes duplicate keys across Set1/Set2/Set3/Set4 before sending `C.MagicKey`.
- `MagicBarDialog` owns 24 SpellKey slots, four spell sets, second-row visibility, school borders and cooldown display.

## ORIGINS browser reference rule

`apps/zircon-ui-reference/zircon-magic-runtime.js` may render canonical MagicInfo/player state for visual QA, but it is explicitly rejected by this gate if it starts writing Set1Key..Set4Key, NextCast/ToggleTime, or gameplay packets.
