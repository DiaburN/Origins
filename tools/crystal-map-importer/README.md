# Crystal Map Importer — ORIGINS

Purpose: use Crystal as a technical reference to inspect Mir map files and Crystal `.Lib` graphics without requiring the full Crystal client at runtime.

## V1 scope

Implemented foundations:

- detect Mir map families used by Crystal;
- parse classic Mir2 maps;
- parse Wemade Mir3 maps;
- preserve Back/Middle/Front library slots and image IDs;
- inspect Crystal `.Lib` v2/v3 headers and image metadata;
- decode the primary GZip-compressed image layer to RGBA;
- resolve Crystal map-library slots to their expected relative `.Lib` path;
- report exactly which `.Lib` files a map references.

Formats detected but not yet parsed are intentionally rejected with a clear error instead of guessing.

## Why dependency analysis matters

The Crystal client Data directory can be enormous. ORIGINS does not need the whole thing.

Workflow for a cave:

1. choose one source `.map` that visually belongs to the cave style we want;
2. `parseMap()` it;
3. run `analyzeMapDependencies()`;
4. obtain the short list of `.Lib` files actually referenced by that map;
5. inspect only those libraries;
6. register coherent shapes into one ORIGINS `theme_id`;
7. build our own vertical rooms from those shapes.

## ORIGINS rule

A source map is a **reference/catalogue**, not the final playable layout.

We extract coherent visual pieces from one cave style and reconstruct original ORIGINS rooms:

`BOTTOM ENTRY -> LONG CENTRAL PLAY AREA -> TOP DOOR -> NEXT FLOOR -> ... -> KING_ROOM`

A theme may contain floors, walls, corners, doors, obstacles, decoration and KingRoom landmarks. Assets from different visual cave themes must never be mixed.

## Crystal reference

Crystal is GPLv2. ORIGINS-specific room generation, theme manifests and gameplay data should remain independent project code. Keep attribution/licensing for any Crystal-derived implementation that is distributed.
