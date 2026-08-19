# ORIGINS MOBILE — Crystal magic scope

Crystal / Crystal-Monk are the only content and visual sources for spells in this project. Holley/M-Hum/MagicEx assets and spell choreography from the previous project are out of scope.

## Playable class catalogue

ORIGINS must cover every player spell from these classes:

- Warrior
- Wizard
- Taoist
- Assassin
- Archer
- Monk

The base Crystal catalogue currently contributes 105 class spells (17/25/25/17/21). Monk is mandatory and will be populated from the pinned Crystal-Monk source/database before this catalogue is considered complete.

The five base Crystal custom spells are tracked separately until class ownership/availability is intentionally assigned. Map-event effects are not player spells and are excluded from the player magic catalogue.

`database/magic/crystal-playable-spells.json` is the authoritative completeness list. A spell may exist in the catalogue before its runtime handler is finished; runtime readiness is tracked separately. The catalogue is not complete while `Monk` is empty.
