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
│       ├── zircon-player-magics.json
│       ├── zircon-magic-mechanics.json
│       └── crystal-archer-reference.json
├── js/
│   ├── core/        # config, input, cámara, MIR animation/sprites/map parser
│   ├── entities/    # Player
│   ├── systems/     # player-state + movement
│   └── game.js
└── assets/
    ├── maps/        # .map reales cuando se importen
    └── players/<race>/<common-or-class>/<gender>/<appearance>/
        ├── manifest.json
        └── atlas.png
```

## Reglas

1. Revisar este archivo antes de crear carpetas o archivos nuevos.
2. No escanear todo el repositorio para una tarea local.
3. No crear TXT temporales, notas, copias ni documentación redundante.
4. No importar Zircon, Crystal ni PokéSurvivor completos.
5. Antes de crear un archivo nuevo, comprobar si su función ya existe.
6. Assets y lógica permanecen separados.
7. Posición: continua estilo PokéSurvivor. Dirección/acciones: estándar MIR3/Zircon.
8. El renderer debe aceptar cualquier apariencia sin cambiar el motor.
9. Persistencia seguirá el modelo lógico Zircon: `AccountInfo -> CharacterInfo -> UserItem/UserMagic`; `UserItem -> ItemInfo`; `UserMagic -> MagicInfo`.
10. NO importar sprites definitivos hasta validar el sistema de acciones/movimiento del Player.
11. Magias: lógica autoritativa separada de VFX. No convertir los catálogos fuente en un botón por magia.

## Referencias

- PokéSurvivor `b297089`: loop, cámara, input y dinámica general.
- Zircon `80d5df21016b2f377d48f14f7dcc2e994b163ff1`: direcciones, acciones, frames, personajes, items, magias y formato estructural de mapas.
- Crystal `0e315fe327192afe52c3d7357ddd1f5b7e26c5b8`: donor técnico público para la clase Archer y sus acciones/skills.

## Clases ORIGINS

Clases previstas: `Warrior`, `Wizard`, `Taoist`, `Assassin`, `Archer`.

Archer se toma como quinta clase. El donor abierto es Crystal; las variantes Zircon/Mir3 Xtreme y Mir3SEA con Archer son custom y no se asume que su lógica sea idéntica mientras no haya source verificable.

## Apariencias definitivas a importar después

- Base `M001/F001`; noob `M003/F003`.
- Warrior: `M004 > M007 > M002 > M053 > M067` + `Fxxx`.
- Taoist: `M006 > M009 > M010 > M051 > M056` + `Fxxx`.
- Wizard: `M005 > M008 > M011 > M054 > M061` + `Fxxx`.
- Assassin: `M013 > M016 > M014 > M015 > M046` + `Fxxx`.
- Archer: apariencia aún pendiente de localizar/seleccionar cuando estén disponibles sus librerías.

`M046` sigue siendo Assassin aunque su recurso fuente proceda de otra familia HUM. Importar solo sets elegidos, 8 direcciones, índices MIR y offsets originales, atlas+manifest por apariencia.

## Acciones y estados Player

- `js/core/mir-animation.js`: 43 definiciones `FrameSet.Players` de Zircon.
- `js/systems/player-state.js`: intención `MirAction` separada de `MirAnimation`.
- Prioridad: locomoción < acción < struck < pushed < die < dead.
- One-shot -> Standing; `Die -> Dead`; revive explícito.
- Secuencias: Channelling, DragonRepulse, Fishing y Taming.
- Debug temporal para Combat1-15/transiciones sin sprites.
- Direcciones: `0 Up, 1 UpRight, 2 Right, 3 DownRight, 4 Down, 5 DownLeft, 6 Left, 7 UpLeft`.
- Archer añade como donor Crystal: `WalkingBow`, `RunningBow`, `AttackRange1`, `AttackRange2`, `AttackRange3`, `Jump`; aún no integrarlos al runtime hasta auditar assets/mappings completos.

## Magias

- `data/magics/zircon-player-magics.json`: IDs, nombres, 124 mappings centrales de animación, reglas de ataque y referencias VFX conocidas para las 4 clases Zircon.
- `data/magics/zircon-magic-mechanics.json`: clasificación mecánica de las 195 entradas Zircon, dependencias/augments, familias, casos especiales y stubs.
- `data/magics/crystal-archer-reference.json`: donor Archer con 21 skills IDs 121-141 y acciones de arco verificadas.
- Conteo Zircon actual: Warrior 38, Wizard 47, Taoist 52, Assassin 58. Archer se audita aparte porque procede de Crystal.
- Arquitectura: servidor decide coste/objetivo/daño/buff/summon/cooldown; cliente reproduce acción/VFX.
- Modelo ORIGINS acordado: pocas skills principales; las magias fuente pueden actuar como `coreSkill`, evolución, modifier, proc, pasiva o utilidad. Las cadenas finales aún NO están fijadas.
- Interacciones Zircon útiles ya registradas: `Burning` sobre familia Fuego; `Shocked` sobre Rayo; `Asteroid -> FireWall`; augments Taoist; combo Lotus Assassin; `Chain -> ChainOfFire`; etc.
- No copiar stubs/bugs a ciegas. Ej.: `DarkConversion.MagicConsume` requiere reimplementación segura.
- Valores exactos Zircon siguen pendientes de `MagicInfo`.
- VFX Zircon a pedir: `Magic.Zl`, `MagicEx.Zl`...`MagicEx11.Zl`, `MonMagicEx7.Zl`, `MonMagicEx8.Zl`, `MonMagicEx20.Zl`, `MIcon.Zl`.
- Archer: antes de importar, localizar librerías de body/bow/proyectiles/VFX y auditar las 21 skills.

## Mapas MIR3

- `js/core/mir-map.js`: parser estructural `.map`.
- Ancho bytes `22-23`, alto `24-25`; offset `28 + floor(width*height/4)*3`; 14 bytes/celda.
- Grid MIR solo para colisión/navegación; movimiento gameplay continuo.
- Render real pendiente de `0.map` + librerías de tiles.

## Estado

- [x] Cliente mínimo, loop, input, cámara y movimiento continuo.
- [x] Definiciones/timings + máquina de estados Player.
- [x] Renderer MIR desacoplado + pipeline M001 validado técnicamente.
- [x] Apariencias definitivas elegidas para las 4 clases Zircon.
- [x] Persistencia lógica fijada según Zircon.
- [x] Parser estructural `.map` preparado.
- [x] 195 magias Zircon Player indexadas y animaciones centrales registradas.
- [x] Clasificación mecánica Zircon y dependencias/augments principales guardadas.
- [x] Archer añadido como quinta clase prevista; 21 skills y acciones base registradas desde Crystal.
- [ ] Validar Player visualmente en navegador.
- [ ] Auditar las 21 skills Archer + localizar sus assets exactos.
- [ ] Recibir/importar VFX Zircon + `MIcon.Zl` + datos `MagicInfo` y validar cada efecto visual contra sus índices reales.
- [ ] Diseñar después las cadenas definitivas ORIGINS sin multiplicar botones.
- [ ] Probar `0.map` real + colisiones + renderer de mapa.
- [ ] Monstruos, spawn y combate.

## Siguiente paso

Mientras no estén disponibles los archivos del PC, usar los JSON de referencia y no volver a escanear repos completos. Para Archer, continuar únicamente con auditoría de sus 21 skills y assets fuente; para Zircon, esperar `MagicInfo` y los `.Zl` antes de fijar las cadenas definitivas.