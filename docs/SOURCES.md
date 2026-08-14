# ORIGINS Map Engine Sources

This project must NOT use the multipart ZIP previously uploaded in ChatGPT as a source for Mir2 map assets.

Authoritative/reference sources for Map Engine V1:

1. Crystal engine/source code
   - Repository: `Suprcode/Crystal`
   - Purpose: map format parsing, Crystal `.Lib` format, map-library index mapping, technical behavior reference.

2. Crystal database / Jev maps
   - Repository: `Suprcode/Crystal.Database`
   - Primary path: `Jev/Maps/`
   - Purpose: real `.map` files used to identify coherent dungeon themes and source image indices.

3. MirFiles Crystal client map assets
   - Public directory: `mirfiles.co.uk/resources/mir2/crystal/patch/Data/Map/`
   - Primary family for first prototype: `WemadeMir2/`
   - Purpose: actual `.Lib` graphical libraries referenced by Crystal maps.

## Zuma prototype

Reference maps:
- `Jev/Maps/d501.map` — standard Zuma floor reference
- `Jev/Maps/d515.map` — Zuma final/KingRoom reference

The importer must determine exact library/image dependencies from those maps and fetch/use only the required MirFiles libraries.

## Mandatory rule

Do not use the previously uploaded `WemadeMir2(1).zip`, any split ZIP parts from the chat, or derived files from those uploads. If a required asset cannot be obtained from the sources above, stop and mark it as missing instead of silently substituting another source or another cave style.
