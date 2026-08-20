# ORIGINS-DxR — native Zircon player runtime audit

- Gate: **PASS**
- Zircon authority: `cbf1aa919083bc13fc3f23f93772a8ab8370632d`
- Frame source: `FrameSet.Players` + Zircon `MirAnimation`/`Functions`; no Crystal frame table.
- Missing direct mappings are reported, not invented.
- Server movement authority: `C.Move -> Player.Move`; there is no required `PlayerObject.Walk()` contract.

| Requested behaviour | Native MirAction | Status | Native animation/behaviour |
|---|---|---|---|
| Standing | Standing | DIRECT | Standing; native Stance/Creep/Horse/DragonRepulse/Channelling state overrides |
| Walking | Moving | DIRECT_VARIANT | Walking; HorseWalking/Creep variants |
| Running | Moving | DIRECT_VARIANT | Running for distance >= 2; HorseRunning when mounted |
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
| Mount | Mount | STATE_DRIVEN | Horse state drives HorseStanding/Walking/Running/Struck; server uses Player.Mount() |
| Fishing | Fishing | DIRECT | FishingCast/FishingWait/FishingReel |
| Taming | Taming | DIRECT | TamingCast/TamingWait |
| Idle | Idle | NO_DIRECT_PLAYER_ANIMATION | DoNextAction falls back to Standing when no queued action |

## Player visual stack

Verified native Body, Hair, Helmet, Weapon1/Weapon2, Shield and Horse libraries/frames, including all eight direction branches and weapon/shield layering.

## Frame-bound effects

Verified native `FrameIndexChanged()` gates for SeismicSlam, CrushingWave, OffensiveBlow, Taming and Fishing, plus user movement/horse timing. Effect/projectile timing remains Zircon-owned.

## Native enum actions without direct PlayerObject animation

Hide, Idle, Mount, Show

`Mount` is state-driven through `Horse`; `Show`, `Hide` and `Idle` are not assigned a direct animation by pinned `PlayerObject.SetAnimation()`. ORIGINS-DxR does not fabricate replacements.
