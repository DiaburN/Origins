# ORIGINS-DxR — native Zircon player runtime audit

- Gate: **FAIL**
- Zircon authority: `cbf1aa919083bc13fc3f23f93772a8ab8370632d`
- Frame source: `FrameSet.Players` + Zircon `MirAnimation`/`Functions`; no Crystal frame table.
- Missing direct mappings are reported, not invented.

| Requested behaviour | Native MirAction | Status | Native animation/behaviour |
|---|---|---|---|
| Standing | Standing | DIRECT | Standing; Stance/Creep/Horse/DragonRepulse/Channelling overrides by native state |
| Walking | Moving | DIRECT_VARIANT | Walking; HorseWalking/Creep variants |
| Running | Moving | DIRECT_VARIANT | Running when action.Extra[0] >= 2; HorseRunning when mounted |
| Pushed | Pushed | DIRECT | Pushed |
| Attack | Attack | DIRECT | Functions.GetAttackAnimation(class, weapon, magic) |
| RangeAttack | RangeAttack | DIRECT | Combat1 |
| Spell | Spell | DIRECT | Functions.GetMagicAnimation(MagicType) |
| Harvest | Harvest | DIRECT | Harvest |
| Struck | Struck | DIRECT | Struck / HorseStruck |
| Die | Die | DIRECT | Die |
| Dead | Dead | DIRECT | Dead |
| Show | Show | NO_DIRECT_PLAYER_ANIMATION | none in PlayerObject.SetAnimation |
| Hide | Hide | NO_DIRECT_PLAYER_ANIMATION | none in PlayerObject.SetAnimation |
| Mount | Mount | STATE_DRIVEN | UserObject AttemptAction returns; Horse state drives HorseStanding/Walking/Running/Struck |
| Fishing | Fishing | DIRECT | FishingCast/FishingWait/FishingReel |
| Taming | Taming | DIRECT | TamingCast/TamingWait |
| Idle | Idle | NO_DIRECT_PLAYER_ANIMATION | PlayerObject DoNextAction falls back to Standing when no queued action |

## Player visual stack

Verified native libraries/frames for Body, Hair, Helmet, Weapon1/Weapon2, Shield and Horse, including direction-dependent weapon/shield layering.

## Frame-bound effects

Verified `FrameIndexChanged()` gates for native effects including SeismicSlam (frame 4), CrushingWave (frame 4), OffensiveBlow (frame 3), TamingCast (frame 5) and Fishing (frame 1), plus user movement/horse sounds and SeismicSlam screen shake.

## Native enum actions without direct PlayerObject animation

Hide, Idle, Mount, Show

`Mount` is state-driven through `Horse`; `Show`, `Hide` and `Idle` are not assigned a direct animation by pinned `PlayerObject.SetAnimation()`. ORIGINS-DxR does not fabricate replacements.

## Failures

- Server PlayerObject: missing public void Walk(
