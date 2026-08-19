# ORIGINS MOBILE — Crystal magic scope

Crystal / Crystal-Monk are the only content and visual sources for spells in this project. Holley/M-Hum/MagicEx assets and spell choreography from the previous project are out of scope.

## Playable class catalogue

The authoritative playable catalogue is the union of base Crystal plus the playable additions present in the pinned Crystal-Monk fork:

- Warrior — 21 (17 base + 4 Crystal-Monk variants/secrets)
- Wizard — 28 (25 base + 3 Crystal-Monk variants/secrets)
- Taoist — 27 (25 base + 2 Crystal-Monk variants/secrets)
- Assassin — 19 (17 base + 2 Crystal-Monk variants/secrets)
- Archer — 24 (21 base + 3 Crystal-Monk variants/secrets)
- Monk — 9

Total: **128 mandatory playable spells**.

Sources are pinned to `Suprcode/Crystal` commit `0e315fe327192afe52c3d7357ddd1f5b7e26c5b8` and `JevLOMCN/Crystal-Monk` commit `381e589e3d7ee736cdf0583c8315c0d144ab058f`.

The 14 non-Monk additions from Crystal-Monk are: `CounterAttack1`, `ProtectionField1`, `EntrapSwordSecret`, `ImmortalSkin1`, `GreateFireBallSecret`, `Bisul`, `StormEscape1`, `HealingCircle2`, `Healing2`, `FlashDash2`, `MoonMist2`, `ElementalBarrier1`, `DelayedExplosion2`, and `NapalmShot2`.

The nine Monk spells are: `JiBenGunFa`, `LuoHanGunFa`, `JinGangGunFa`, `DaMoGunFa`, `XiangLongGunFa`, `Taunt`, `TianLeiZhen`, `ShiBuYiSha`, and `LuoHanZhen`.

The five base Crystal custom spells remain tracked separately until class ownership/availability is intentionally assigned. Map-event effects are not player spells and are excluded from the player magic catalogue.

`database/magic/crystal-playable-spells.json` is the authoritative completeness list. A spell may already exist in `System.db` before its runtime handler is finished; runtime readiness is tracked separately. Pending spells use reserved ORIGINS `MagicType` values so they cannot silently execute unrelated Zircon logic.

The catalogue is complete only when the generated playable overlay contains exactly 128 operations with class counts `21/28/27/19/24/9`.
