# ORIGINS Map Engine V1

## Goal

Build original ORIGINS dungeons with a vertical, room-based action flow inspired by Archero while using coherent Mir-style cave art and data.

The first milestone is map construction only.

## Standard room geometry

Rooms are predominantly vertical and elongated.

- Entry is at the bottom.
- Walkable cells occupy the central play area.
- Solid cave walls bound the left and right sides.
- A bottom wall/entrance closes the lower edge.
- A top wall contains the exit door.
- Clearing the room can unlock/open the top door.

Room templates may vary in width, length and obstacle layout, but must preserve clear forward progression.

## Theme integrity — mandatory

Every dungeon has a single `theme_id`.

A room may only use shapes/assets registered to that exact theme.

Never mix a wall from one cave with a floor, corner, door, altar or obstacle from another cave merely because the geometry fits.

Each theme can contain:

- floors
- top walls
- bottom walls
- left walls
- right walls
- corners
- doors
- pillars
- rocks
- statues
- ruins
- holes
- environmental hazards
- floor decorations
- altars
- boss decorations
- transition pieces

## Floors and variation

A dungeon is composed of several floors/rooms. Floors should feel related but not identical.

Variation may come from:

- obstacle placement
- floor decorations
- columns/pillars
- rocks or broken structures
- hazards
- different room dimensions
- enemy spawn layouts (later phase)
- elite/event room composition (later phase)

All variation must remain inside the same theme.

## KingRoom

The final floor of a dungeon is a `KING_ROOM`.

It can use visually important pieces belonging to the same theme, for example:

- altar
- throne
- boss portal
- large statue
- ritual floor
- special columns
- large theme-specific decoration

KingRoom pieces are not required in ordinary floors.

## Initial room types

- `STANDARD_LONG`
- `STANDARD_NARROW`
- `STANDARD_WIDE`
- `OBSTACLE`
- `PILLARS`
- `ELITE`
- `EVENT`
- `KING_ROOM`

Only `STANDARD_LONG` and `KING_ROOM` are required for the first visual prototype.

## Layers

Visual composition and gameplay logic must remain separate.

### Visual layer

- floor
- wall pieces
- corners
- door
- objects
- decorations

### Collision layer

At minimum:

- `0` walkable
- `1` blocked

Later additions may include hazard, slow, void, door-blocked, etc.

### Gameplay layer

Reserved markers:

- player spawn
- monster spawn
- elite spawn
- boss spawn
- chest
- event trigger
- exit trigger

The first milestone only needs player-entry and exit markers as data; no gameplay is required yet.

## Shape metadata

Every extracted or registered cave shape should retain source information.

Recommended fields:

```json
{
  "shape_id": "theme_wall_top_001",
  "theme_id": "example_cave",
  "type": "WALL_TOP",
  "source_family": "WemadeMir2",
  "source_library": "Objects12",
  "source_image": 341,
  "source_map": null,
  "width_cells": 3,
  "height_cells": 2,
  "anchor_x": 0,
  "anchor_y": 1,
  "collision_profile": "SOLID"
}
```

This metadata prevents accidental mixing between unrelated cave styles and makes generated rooms reproducible.

## Crystal reference

Crystal is used as a technical reference for reading Mir map formats and graphic-library indexing. Crystal-derived code must remain clearly separated/attributed according to its GPLv2 licensing requirements.

ORIGINS-specific room generation, theme manifests and dungeon design should be implemented as independent project code.

## V1 acceptance test

Map Engine V1 is considered visually proven when one complete cave theme can produce:

1. one elongated room;
2. central walkable floor;
3. coherent left/right/bottom/top walls;
4. a top exit door;
5. correct corners;
6. at least one theme-specific obstacle/decorative variation;
7. a distinct KingRoom using a theme-specific altar or equivalent landmark;
8. no asset from another cave/theme.
