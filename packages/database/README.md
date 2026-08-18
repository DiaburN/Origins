# ORIGINS Data Foundation V1

PostgreSQL persistence layer for the ORIGINS runtime.

The logical model follows the useful separation already present in Zircon:
- system/content definitions (`MagicInfo`, `ItemInfo`, `MonsterInfo`, quests, buffs, respawns);
- user-owned state (`CharacterInfo`, `UserMagic`, `UserItem`, character quests/buffs);
- server/runtime behavior remains outside the database.

The physical storage is PostgreSQL rather than Zircon's MirDB format so the same schema can serve web/mobile clients through the ORIGINS server.

## Schemas

### `content`
Canonical game definitions shared by every player:
- classes
- maps / regions / dungeon definitions
- magic definitions
- item definitions + flat stats
- per-class equipment progression and equip restrictions
- item sets / future set bonuses / item-triggered buffs
- upstream source provenance
- monster definitions + stats + drops + respawns + magics
- buffs
- NPCs / shops
- quests / rewards
- currencies
- summons

### `player`
Persistent account/character state:
- accounts
- characters
- persistent/base stat allocations
- learned magic state (`level`, `experience`, key sets, cooldown)
- unique item instances + inventory/equipment/storage slot placement
- currencies
- pets/summons
- buffs
- quest progress

A magic that has not been learned is represented by the absence of a `player.character_magics` row. This mirrors Zircon's `CharacterInfo.Magics` / `UserMagic` association and maps directly to the ORIGINS MagicDialog locked state.

### `gameplay`
Durable gameplay/audit records:
- dungeon runs
- combat sessions
- ordered combat events
- monster kills

Live monsters, projectiles, hit timing and moment-to-moment combat are authoritative in server memory. PostgreSQL stores durable state and important events; it is not queried for every animation frame/projectile step.

### `economy`
Persistent trading state:
- auction/consignment listings
- market transactions
- generic item transaction audit

Class restrictions apply only to EQUIPPING. A character may still loot, own, inventory, storage, trade, sell or auction another class's item unless an independent bind/transfer rule forbids it.

## Assets

Images/sprites are not stored as blobs in PostgreSQL. Definitions store source/library/index references and the runtime resolves them to approved assets under `assets/game/`.

## Source authority

### Magics
Initial spell content is generated from pinned public sources:
- base five classes: `Suprcode/Crystal`
- Monk: `JevLOMCN/Crystal-Monk`

### Items and class equipment
The item RUNTIME follows Zircon's model (`ItemInfo`, `UserItem`, `ItemEffect`, `BuffIcon`, set logic, inventory/equipment, durability, repair, storage, trade and consignment behavior).

The initial CLASS EQUIPMENT progression is intentionally source-faithful Crystal content:
- Warrior / Wizard / Taoist / Assassin / Archer: class-specific equipment from `Suprcode/Crystal.Database` (`Jev/Server.MirDB`).
- Monk: class-specific equipment from a Crystal-Monk-compatible source when an authoritative source database is available.
- generic/non-class equipment, consumables and special items: Zircon catalogue/import phase.

For imported Crystal class equipment:
- keep the original source item identity and name;
- keep the original required class and requirement amount/type;
- import flat core combat stats only (`AC`, `MAC`, `DC`, `MC`, `SC`, `Accuracy`, `Agility`, `HP`, `MP`);
- do not invent set bonuses, Crit, Attack Speed or other ORIGINS balance extras;
- preserve every additional Crystal source stat in metadata so it may be opted into later without losing provenance;
- use the Zircon-style ORIGINS runtime for equip/storage/trade/auction/effects.

This lets ORIGINS start with Crystal's real class progression and later append new ORIGINS sets for every class using the same data contract.

`content.equipment_progression` answers which equipment exists for each class/family and the maximum source level currently covered. `content.item_set_definitions` / `item_set_members` preserve Crystal `ItemSet` membership. `content.item_set_bonuses` exists for future explicit bonuses but the importer does not fabricate any.

The database keeps source repository/path/commit provenance for imported definitions.

## Local database

```bash
cd packages/database
docker compose up -d
```

The CI workflow `.github/workflows/validate-data-foundation.yml` performs the authoritative automated validation: it starts PostgreSQL 16, applies migrations, imports the six classes and 114 selected Crystal/Crystal-Monk spells, reads the pinned Jev `Server.MirDB`, imports class-specific Crystal equipment with original names/requirements/flat stats, validates class-only EQUIP rules without blocking possession/storage/trade/auction, and tests the Zircon-style learned/unlearned `UserMagic` lifecycle.

## Migration order

1. `migrations/0001_core.sql`
2. `migrations/0002_zircon_crystal_extensions.sql`
3. `seeds/0001_classes.sql`
4. `migrations/0003_item_class_overlays.sql`
5. generated spell seed from `tools/data-foundation/`
6. `migrations/0004_item_equip_class_rules.sql`
7. `migrations/0005_world_content_and_progression.sql`
8. `migrations/0006_class_combat_and_equipment_contract.sql`
9. `migrations/0007_equipment_persistence_enforcement.sql`
10. `migrations/0008_market_and_item_possession_contract.sql`
11. `migrations/0009_equipment_progression_and_zircon_runtime.sql`
12. generated Crystal equipment seed from `tools/data-foundation/extract_crystal_equipment.py`

Do not edit an already deployed migration to change production data. Add the next numbered migration instead.
