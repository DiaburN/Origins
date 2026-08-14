# ORIGINS

Official repository of ORIGINS.

ORIGINS is a web-first action RPG/MMORPG project rebuilt around vertical room-based dungeons inspired by the visual language and content structure of classic Mir games.

## Current phase

**MAP ENGINE V1 — caves/dungeons only.**

No player, combat, UI, monsters or spells are part of this first milestone. The first goal is to build coherent cave rooms from one visual theme at a time.

## Locked map rule

Each dungeon theme is a closed visual set. Floors, walls, corners, doors, obstacles, decorations and KingRoom pieces must all belong to the same cave/theme.

Standard progression:

`BOTTOM ENTRY -> LONG CENTRAL PLAY AREA -> TOP DOOR -> NEXT FLOOR -> ... -> KINGROOM`

The final floor is a **KingRoom**, where special pieces such as an altar, throne, portal or boss decoration may be used, but only if they belong to the same dungeon theme.

Different floors can be visually differentiated with floor decorations and gameplay obstacles while preserving the same cave identity.

See `docs/MAP_ENGINE_V1.md` for the design specification.
