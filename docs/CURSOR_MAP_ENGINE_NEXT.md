# Cursor — ORIGINS Map Engine V1 next action

Work only on branch `map-engine-v1`.

## Objective

Extract the exact Crystal graphics referenced by the Zuma reference maps without copying the full Crystal client into ORIGINS.

Reference maps:

- `d501.map` = normal Zuma floor reference
- `d515.map` = Zuma KingRoom reference

The analysis already proves these maps only require:

- `Data/Map/WemadeMir2/Tiles.Lib`
- `Data/Map/WemadeMir2/Objects2.Lib`
- `Data/Map/WemadeMir2/Objects6.Lib`

Do **not** copy the whole `Data` directory into this repository.

## Run

Use the user's local Crystal client and local Crystal.Database checkout/folder.

From the ORIGINS repository root run:

```powershell
python tools/crystal-map-importer/extract_theme_assets.py `
  --data "C:\PATH\TO\CRYSTAL\Client\Data" `
  --maps "C:\PATH\TO\Crystal.Database\Jev\Maps" `
  --standard d501.map `
  --king d515.map `
  --theme zuma `
  --out origins\map-engine\themes\zuma\extracted
```

If the executable client has `Data` somewhere else, point `--data` to that Data folder. The script also accepts a direct path to `Data/Map/WemadeMir2`.

The extractor uses Python standard library only. Do not install image packages unless a real incompatibility is found.

## Expected output

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

Open `gallery.html` locally in a browser.

## Important classification rule

Do not automatically call every `kingroom_only` image an altar. `kingroom_only` only means the image is present in `d515` but not `d501`.

Visually classify extracted images into these roles:

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

Do not build a giant Mir map.

Build only these two ORIGINS rooms from the classified Zuma shapes:

1. `origins/map-engine/themes/zuma/rooms/standard-long-01.json`
2. `origins/map-engine/themes/zuma/rooms/king-room-01.json`

The standard room is vertical with entry at the bottom and a door at the top. The KingRoom is the final floor and must contain a Zuma-specific landmark (altar/ritual/portal/etc.) selected from the same theme.

## Commit policy

Do not commit any complete Crystal client or complete `.Lib` archive to ORIGINS.

Commit only:

- ORIGINS code
- manifests
- classification metadata
- the minimal extracted PNG assets actually selected for ORIGINS rooms
- generated room data required by the prototype

Keep source library name and source image ID in every selected shape's metadata so provenance is never lost.
