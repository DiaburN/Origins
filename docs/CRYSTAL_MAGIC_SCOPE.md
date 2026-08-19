# ORIGINS MOBILE — Crystal magic scope

Crystal / Crystal-Monk are the only content and visual sources for spells in this project. Holley/M-Hum/MagicEx assets and spell choreography from the previous project are out of scope.

## Playable class catalogue

ORIGINS must cover every player spell from these classes:

- Warrior — 17
- Wizard — 25
- Taoist — 25
- Assassin — 17
- Archer — 21
- Monk — 9

The base `Suprcode/Crystal` catalogue contributes 105 class spells. The pinned `JevLOMCN/Crystal-Monk` source at commit `381e589e3d7ee736cdf0583c8315c0d144ab058f` contributes the 9 Monk spells, for **114 mandatory playable spells** in total.

The five base Crystal custom spells are tracked separately until class ownership/availability is intentionally assigned. Map-event effects are not player spells and are excluded from the player magic catalogue.

`database/magic/crystal-playable-spells.json` is the authoritative completeness list. A spell may already exist in `System.db` before its runtime handler is finished; runtime readiness is tracked separately. Pending spells use reserved ORIGINS `MagicType` values so they cannot silently execute unrelated Zircon logic.

The catalogue is complete only when the generated playable overlay contains exactly 114 operations with class counts `17/25/25/17/21/9`.
