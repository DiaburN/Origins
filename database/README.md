# ORIGINS Database

ORIGINS keeps Zircon as the authoritative database and server data model.

## Rule

- Static/game definitions come from Zircon `MirDB/SystemModels`.
- Persistent player/server data comes from Zircon `ServerLibrary/DBModels`.
- Crystal does **not** replace either database layer.
- Crystal spell content is mapped onto Zircon `MagicInfo` / `UserMagic`.
- Spell execution differences are stored only in the additive ORIGINS execution profile layer under `database/magic` and `src/Origins.Database/Magic`.

This prevents two competing database or combat engines from existing in ORIGINS.

## Build order

1. Zircon DB core and SystemModels.
2. Zircon ServerLibrary DBModels.
3. Populate ORIGINS static data (items, monsters, maps, NPCs, drops, sets, magic).
4. Populate persistent/player data models (accounts, characters, inventory, guilds, quests, buffs, user magic).
5. Import Crystal spell catalogue into Zircon `MagicInfo`.
6. Add execution profiles only when Crystal behaviour differs from Zircon native behaviour.

See `zircon-model-manifest.json` for the pinned upstream model inventory.