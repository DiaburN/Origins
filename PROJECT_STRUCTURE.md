# PROJECT STRUCTURE

Único documento de estructura del proyecto. Mantener corto y actualizado.

```text
Origins/
├── README.md
├── PROJECT_STRUCTURE.md
├── index.html
├── css/game.css
├── data/
│   ├── players/
│   └── magics/
├── js/
│   ├── core/        # config, input, cámara, MIR animation/sprites/map parser+renderer
│   ├── entities/    # Player
│   ├── systems/     # player-state, map-world, movement
│   └── game.js
├── tools/mir3/
│   ├── build_map_runtime.py
│   └── build_player_runtime.py
└── assets/
    ├── maps/<map-id>/manifest.json
    ├── monsters/<monster-id>/
    └── players/<race>/<common-or-class>/<gender>/<appearance>/manifest.json
```

## Reglas

1. Revisar este archivo antes de crear carpetas o archivos nuevos.
2. No crear TXT temporales, copias ni documentación redundante.
3. No importar Zircon, Crystal ni PokéSurvivor completos.
4. Assets y lógica permanecen separados.
5. Posición: continua estilo PokéSurvivor. Dirección/acciones/frames: MIR3/Zircon.
6. Clases, razas, apariencias, monstruos y magias deben ser data-driven.
7. Drive conserva fuentes pesadas y runtime pesado; GitHub conserva código, manifests y herramientas.
8. Los `.Zl` son fuente de conversión, nunca formato que deba interpretar el navegador.

## Referencias

- PokéSurvivor `b297089`: loop, cámara, input, chunks y dinámica general.
- Zircon `80d5df21016b2f377d48f14f7dcc2e994b163ff1`: direcciones, acciones, frames, personajes, items, magias, monstruos y mapas.
- Crystal `0e315fe327192afe52c3d7357ddd1f5b7e26c5b8`: referencia futura opcional para Archer.

## Clases y apariencias

Núcleo inicial: `Warrior`, `Wizard`, `Taoist`, `Assassin`.

- Base `M001/F001`; noob `M003/F003`.
- Warrior: `M004 > M007 > M002 > M053 > M067` + femenino.
- Taoist: `M006 > M009 > M010 > M051 > M056` + femenino.
- Wizard: `M005 > M008 > M011 > M054 > M061` + femenino.
- Assassin: `M013 > M016 > M014 > M015 > M046` + femenino.

`M046` sigue siendo Assassin aunque proceda de otra familia HUM. `Archer` y `Monk` quedan fuera del núcleo inicial.

## Player MIR

- Direcciones: `0 Up, 1 UpRight, 2 Right, 3 DownRight, 4 Down, 5 DownLeft, 6 Left, 7 UpLeft`.
- `js/core/mir-animation.js`: FrameSets/timings Player de Zircon, incluido Combat1-15 y estados especiales.
- `js/systems/player-state.js`: intención `MirAction` separada de `MirAnimation`.
- `js/core/mir-sprites.js`: atlas compactos de tamaño variable, offsets originales y soporte multipágina.
- `js/entities/player.js`: posición continua en centro de celda; al renderizar se convierte al origen MIR 48x32 y se aplican `OffSetX/OffSetY` originales.
- `tools/mir3/build_player_runtime.py`: convierte un bloque de apariencia de 5000 frames a WebP lossless + manifest web.
- M001 masculino generado: `1576` frames reales, todos contrastados píxel a píxel con `M-Hum.Zl`; runtime almacenado en Drive.

## Mapas MIR3

Primer mapa: `01.map` = Border Village.

- Fuente oficial ORIGINS X: `600x600`, `5.310.028 bytes`, SHA1 `61c550cd938573a26efa7ee7067d51d9aa47d391`.
- Usa exactamente 11 librerías: `0,1,2,3,4,5,9,10,11,15,25`.
- `js/core/mir-map.js`: parser Back/Middle/Front, animación, luz, librerías y colisión.
- `js/core/mir-map-renderer.js`: atlas compartidos, animación 100 ms y profundidad equivalente al cliente Zircon.
- Orden visual verificado contra Zircon: Back -> capas estáticas 48x32/96x64 de suelo -> por cada fila capas altas/animadas -> entidades de esa fila.
- `js/systems/map-world.js`: carga, spawn, límites, movimiento continuo y colisión MIR.
- `tools/mir3/build_map_runtime.py`: extrae solo frames realmente usados y genera `.map` + `render-pack.json` + WebP lossless.
- Border Village runtime generado: `10.914` frames reales, `5` páginas compartidas de atlas; todos los frames extraídos fueron contrastados contra sus `.Zl`.
- El mapa completo fue reconstruido desde `01.map` + `.Zl` y contrastado con el preview oficial antes de fijar el renderer.

## Runtime pesado

Drive: `MAPAS Y ARCHIVOS / ORIGINS X RUNTIME`.

- `border-village/`: `01.map`, `render-pack.json`, `page-0.webp` ... `page-4.webp`.
- `players/base_m001/`: `atlas.webp`, `manifest.json`.

Estos archivos todavía no se sirven directamente al navegador: Drive actúa como almacén maestro, no como CDN web. Los manifests de GitHub permanecen `ready:false` hasta disponer de una ruta HTTP/CORS estable para los binarios runtime.

## Magias

- `data/magics/zircon-player-magics.json`: catálogo/mappings centrales Zircon.
- `data/magics/zircon-magic-mechanics.json`: familias, dependencias y mecánicas.
- Lógica autoritativa separada de VFX.
- No copiar stubs/bugs de Zircon a ciegas.

## Estado

- [x] Cliente mínimo, loop, input y cámara.
- [x] Player: movimiento continuo + 8 direcciones + FrameSets/estados MIR.
- [x] Player renderer: offsets originales, atlas compactos y multipágina.
- [x] Conversor genérico de apariencias MIR3.
- [x] M001 masculino convertido y validado.
- [x] Parser completo `.map` y `MapWorld`.
- [x] Border Village recibido y validado.
- [x] 11 librerías exactas detectadas.
- [x] Conversor genérico de mapas MIR3.
- [x] Border Village runtime generado y validado.
- [x] Profundidad mapa/personaje ajustada al orden de Zircon.
- [x] Runtime pesado guardado en Drive.
- [ ] Publicar/sincronizar runtime pesado en una ubicación web accesible por el cliente.
- [ ] Activar manifests `ready:true` y probar Border Village + M001 en navegador.
- [ ] Mejorar huella de colisión continua si la prueba visual detecta recorte de esquinas.
- [ ] Importar siguientes apariencias elegidas.
- [ ] Monstruos, spawn, combate y primeras magias.

## Siguiente paso

Resolver una ubicación web estable para los binarios runtime (mapa/atlases). Después activar Border Village y M001 y hacer la primera prueba real en navegador: caminar, correr, 8 direcciones, cámara, colisión y oclusión por árboles/casas.
