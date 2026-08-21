# ORIGINS-DxR — Authentic Forest F1 Real Zircon Render

- Forest gate: **FAIL**
- HEAD: `085da9c06534e6af4fb4f14b17cc52651f0d0584`

## Steps

- BOOTSTRAP: **success**
- DXT: **success**
- FETCH: **success**
- BUILD: **success**
- RENDER_BICHON: **success**
- BUILD_FOREST: **failure**
- RENDER_FOREST: **skipped**
- VALIDATE_FOREST: **skipped**

## Official Zircon files

- `Map/0.map`: **READY**; `1806903` bytes
- `Data/Map Data/Tilesc.Zl`: **READY**; `33484507` bytes
- `Data/Map Data/Tiles30c.Zl`: **READY**; `2899880` bytes
- `Data/Map Data/Tiles5c.Zl`: **READY**; `10673688` bytes
- `Data/Map Data/SmTilesc.Zl`: **READY**; `770956` bytes
- `Data/Map Data/Housesc.Zl`: **READY**; `29850809` bytes
- `Data/Map Data/Cliffsc.Zl`: **READY**; `8917280` bytes
- `Data/Map Data/Dungeonsc.Zl`: **READY**; `11683647` bytes
- `Data/Map Data/Innersc.Zl`: **READY**; `208560` bytes
- `Data/Map Data/Furnituresc.Zl`: **READY**; `1984163` bytes
- `Data/Map Data/Wallsc.Zl`: **READY**; `39287002` bytes
- `Data/Map Data/SmObjectsc.Zl`: **READY**; `21322908` bytes
- `Data/Map Data/Animationsc.Zl`: **READY**; `17278768` bytes
- `Data/Map Data/Object1c.Zl`: **READY**; `35432235` bytes
- `Data/Map Data/Object2c.Zl`: **READY**; `24844067` bytes
- `Data/Map Data/Wood/Tilesc.Zl`: **READY**; `80192342` bytes
- `Data/Map Data/Wood/Housesc.Zl`: **READY**; `21723636` bytes
- `Data/Map Data/Wood/SmObjectsc.Zl`: **READY**; `19811316` bytes

## forest build log

```text
Traceback (most recent call last):
  File "D:\a\Origins\Origins\scripts\build-origins-forest-room.py", line 247, in <module>
    raise SystemExit(main())
                     ^^^^^^
  File "D:\a\Origins\Origins\scripts\build-origins-forest-room.py", line 236, in main
    out,report=build(src)
               ^^^^^^^^^^
  File "D:\a\Origins\Origins\scripts\build-origins-forest-room.py", line 150, in build
    raise ValueError(f'Expected official Bichon 0.map 800x800, got {src.w}x{src.h}')
ValueError: Expected official Bichon 0.map 800x800, got 350x350
```
