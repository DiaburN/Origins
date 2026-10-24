# PROJECT STRUCTURE

Documento único y corto de estructura oficial. Revisar antes de crear archivos.

```text
Origins/
├── index.html
├── css/
│   ├── game.css
│   └── ingame.css
├── js/
│   ├── core/        # config, input, cámara, MIR animation/sprites/map parser+renderer
│   ├── entities/    # Player
│   ├── systems/     # session, player-state, map-world, movement
│   ├── ui/          # flow + ingame HUD/windows/minimap
│   └── game.js
├── data/
│   ├── ui/zircon-ui-spec.json   # geometría/índices UI verificados
│   ├── players/
│   └── magics/
├── docs/
│   └── ZIRCON_UI_REFERENCE.md   # fuente de verdad de interfaz/menús/submenús
├── tools/mir3/
│   ├── build_map_runtime.py
│   ├── build_player_runtime.py
│   └── build_ui_runtime.py
└── assets/
    ├── maps/<map-id>/manifest.json
    ├── monsters/<monster-id>/
    ├── players/<race>/<class>/<gender>/<appearance>/manifest.json
    └── ui/zircon/   # runtime web extraído de Interface/GameInter
```

## Reglas

1. No escanear todo el repo en cada tarea; mirar este archivo y solo lo afectado.
2. No crear TXT temporales, copias ni documentación redundante.
3. No importar Zircon/PokéSurvivor completos: reutilizar reglas/assets concretos.
4. Assets y lógica separados; `.Zl` solo fuente de conversión, nunca runtime web.
5. Movimiento continuo; direcciones/acciones/frames MIR3/Zircon.
6. Clases, mapas, monstruos, magias, items y spawns deben ser data-driven.
7. Para UI: consultar primero `docs/ZIRCON_UI_REFERENCE.md` y `data/ui/zircon-ui-spec.json`. No inventar posiciones, cajas, capas o assets.

## Flujo actual

`Login local -> Crear/Seleccionar personaje -> Entrar -> HUD ingame -> mapa inicial`

- Cuenta/personajes temporales en `localStorage`.
- Clases: Warrior, Wizard, Taoist, Assassin; hombre/mujer.
- Login/Select/Create reconstruidos con assets reales de Zircon.
- Panel inferior basado en `GameInter[50]`; hotspots originales 82/87/92/112/97/107/102/117/122.
- La interfaz ingame está en reconstrucción fuente-a-fuente contra Zircon. No considerar una ventana terminada hasta que figure `VERIFIED-IMPLEMENTED` en la referencia UI.
- Character debe usar paperdoll por capas `ProgUse + Equip`; nunca una preview estática equipada.
- MiniMap real de `3.map` requiere `MiniMap.Zl` (índice 145); no inventar su interior.

## Mapa inicial

**Start actual: `3.map`.**

Manifest: `assets/maps/start-3/manifest.json`.

- `game.js` apunta directamente a este manifest.
- Runtime todavía `ready:false`; cuando se genere `3.map + render-pack + atlas`, arrancará automáticamente ahí.
- `01.map` / Border Village se conserva como mapa técnico ya validado y referencia del parser/renderer.

## Player / mapas

- `js/core/mir-animation.js`: FrameSets/timings Zircon.
- `js/core/mir-sprites.js`: atlas + offsets MIR.
- `js/entities/player.js`: personaje continuo con renderer MIR; todavía no implementa todas las capas de equipamiento.
- `js/core/mir-map.js`: parser `.map`.
- `js/core/mir-map-renderer.js`: capas/profundidad/animación.
- `js/systems/map-world.js`: carga, spawn, límites y colisión.
- `tools/mir3/build_map_runtime.py`: `.map` -> runtime web.

## Runtime pesado

Drive conserva fuentes/runtimes pesados; GitHub conserva código, manifests y assets web pequeños.

## Siguiente paso

1. Reconstruir primitives UI: DXWindow, DXButton/DXTab, DXItemCell.
2. Cerrar MainPanel exacto.
3. Crear renderer compartido de personaje por capas `ProgUse + Equip`.
4. Completar CharacterDialog e InventoryDialog.
5. Seguir el orden de `docs/ZIRCON_UI_REFERENCE.md` para todos los menús/submenús.
