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
- maps
- magic definitions
- item definitions + stats
- monster definitions + stats + drops + respawns
- buffs
- quests

### `player`
Persistent account/character state:
- accounts
- characters
- persistent/base stat allocations
- learned magic state (`level`, `experience`, key sets, cooldown)
- unique item instances + inventory/equipment/storage slot placement
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

## Assets

Images/sprites are not stored as blobs in PostgreSQL. Definitions store source/library/index references and the runtime resolves them to approved assets under `assets/game/`.

## Source authority

Initial spell content is generated from pinned public sources:
- base five classes: `Suprcode/Crystal`
- Monk: `JevLOMCN/Crystal-Monk`

The database keeps source repository/path/commit provenance for imported definitions.

## Local database

```bash
cd packages/database
docker compose up -d
```

The CI workflow `.github/workflows/validate-data-foundation.yml` performs the authoritative automated validation: it starts PostgreSQL 16, applies migrations, imports the six classes and all 114 selected Crystal/Crystal-Monk spells, and tests the Zircon-style learned/unlearned `UserMagic` lifecycle.

## Migration order

1. `migrations/0001_core.sql`
2. `migrations/0002_zircon_crystal_extensions.sql`
3. `seeds/0001_classes.sql`
4. generated spell seed from `tools/data-foundation/`

Do not edit an already deployed migration to change production data. Add the next numbered migration instead.
