# Cursor — ORIGINS Map Engine V1 next action

Work only on branch `map-engine-v1`.

## Authoritative sources only

Do NOT use any ZIP previously uploaded in ChatGPT.

Use only:

- `Suprcode/Crystal` for Crystal map/library format behavior.
- `Suprcode/Crystal.Database` for Jev `.map` files.
- MirFiles Crystal patch data for real Mir2 `.Lib` graphics.

Public MirFiles map root:

`https://mirfiles.co.uk/resources/mir2/crystal/patch/Data/Map/`

First asset family:

`WemadeMir2/`

## Objective

Extract the exact public Mir2 graphics referenced by the Zuma reference maps without copying a complete Crystal client into ORIGINS.

Reference maps from `Suprcode/Crystal.Database/Jev/Maps`:

- `d501.map` = normal Zuma floor reference
- `d515.map` = Zuma KingRoom reference

Analysis shows these maps require only:

- `WemadeMir2/Tiles.Lib`
- `WemadeMir2/Objects2.Lib`
- `WemadeMir2/Objects6.Lib`

Fetch/use those libraries from the MirFiles Crystal patch source, not from the user's previous chat uploads.

## Extraction

Use `tools/crystal-map-importer/extract_theme_assets.py` against the three fetched public `.Lib` files and the two Jev maps.

Expected output:

```text
origins/map-engine/themes/zuma/extracted/
  common/
    Tiles/
    Objects2/
    Objects6/
  standard_only/
    Tiles/
    Objects2/
    Objects6/
  kingroom_only/
    Tiles/
    Objects6/
  manifest.json
  gallery.html
```

## Important classification rule

Do not automatically call every `kingroom_only` image an altar. `kingroom_only` only means the image is present in `d515` but not `d501`.

Visually classify extracted images into:

- `FLOOR`
- `FLOOR_VARIANT`
- `WALL_TOP`
- `WALL_BOTTOM`
- `WALL_LEFT`
- `WALL_RIGHT`
- `CORNER_TL`
- `CORNER_TR`
- `CORNER_BL`
- `CORNER_BR`
- `DOOR_TOP`
- `DOOR_FRAME`
- `PILLAR`
- `OBSTACLE`
- `DECORATION_FLOOR`
- `DECORATION_WALL`
- `ALTAR`
- `KINGROOM_DECOR`
- `HAZARD`
- `IGNORE`

Never mix an image from another cave/theme into Zuma.

## First visual target

Build only these two ORIGINS rooms from classified Zuma shapes:

1. `origins/map-engine/themes/zuma/rooms/standard-long-01.json`
2. `origins/map-engine/themes/zuma/rooms/king-room-01.json`

The standard room is vertical with entry at the bottom and a door at the top. The KingRoom is the final floor and must contain a Zuma-specific landmark selected from the same theme.

## Commit policy

Do not commit a complete Crystal client or full MirFiles library collection into ORIGINS.

Commit only:

- ORIGINS code
- manifests
- classification metadata
- minimal extracted PNG assets actually selected for ORIGINS rooms
- generated room data required by the prototype

Every selected shape must retain source family, source library and source image ID.
