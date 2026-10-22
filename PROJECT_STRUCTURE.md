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
│   ├── players/
│   └── magics/
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

## Flujo actual

`Login local -> Crear/Seleccionar personaje -> Entrar -> HUD ingame -> mapa inicial`

- Cuenta/personajes temporales en `localStorage`.
- Clases: Warrior, Wizard, Taoist, Assassin; hombre/mujer.
- Login/Select/Create reconstruidos con assets reales de Zircon.
- `js/ui/ingame.js`: panel principal, ventanas y minimapa.
- Panel inferior basado en `GameInter` index `50`.
- Hotspots reales: Character 82, Bag 87, Magic 92, Quest 112, Mail 97, Belt 107, Group 102, Menu 117, Store 122.
- Minimapa basado en `MiniMapDialog`; controles reales GameInter 130/132/137.
- Ventanas ya preparadas: Personaje, Bolsa, Magias, Misiones, Correo, Cinturón, Grupo, Menú, Tienda y mapa grande.

## Mapa inicial

**Start actual: `3.map`.**

Manifest: `assets/maps/start-3/manifest.json`.

- `game.js` apunta directamente a este manifest.
- Runtime todavía `ready:false`; cuando se genere `3.map + render-pack + atlas`, arrancará automáticamente ahí.
- Tutorial inicial futuro: isla/minitutorial antes o alrededor del inicio; no bloquear la implementación actual.
- `01.map` / Border Village se conserva como mapa técnico ya validado y referencia del parser/renderer.

## Player / mapas

- `js/core/mir-animation.js`: FrameSets/timings Zircon.
- `js/core/mir-sprites.js`: atlas + offsets MIR.
- `js/entities/player.js`: personaje continuo con renderer MIR.
- `js/core/mir-map.js`: parser `.map`.
- `js/core/mir-map-renderer.js`: capas/profundidad/animación.
- `js/systems/map-world.js`: carga, spawn, límites y colisión.
- `tools/mir3/build_map_runtime.py`: `.map` -> runtime web.

## Runtime pesado

Drive conserva fuentes/runtimes pesados; GitHub conserva código, manifests y assets web pequeños.

Pendiente: publicar el runtime real de `3.map` y el player en una ruta HTTP/CORS estable o incorporarlo al flujo local de desarrollo.

## Siguiente paso

1. Probar HUD/minimapa/ventanas desde localhost.
2. Abrir el editor/conversor de mapas.
3. Importar y preparar `3.map` como primer mapa jugable.
4. Definir spawn inicial, regiones y después minitutorial de isla.
5. Continuar con monstruos, combate, drops y magias.
