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
│   ├── systems/     # player-state, map-world, movement
│   └── game.js
└── assets/
    ├── maps/<map-id>/manifest.json
    ├── monsters/<monster-id>/ # sprites + manifest + datos por criatura
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
8. El renderer debe aceptar cualquier apariencia/clase sin cambiar el motor.
9. Persistencia seguirá el modelo lógico Zircon: `AccountInfo -> CharacterInfo -> UserItem/UserMagic`; `UserItem -> ItemInfo`; `UserMagic -> MagicInfo`.
10. NO importar sprites definitivos hasta validar el sistema de acciones/movimiento del Player.
11. Magias: lógica autoritativa separada de VFX. No convertir los catálogos fuente en un botón por magia.
12. Clases nuevas deben ser data-driven: añadir una clase no debe requerir rehacer Player, combate, mapa ni renderer base.
13. Monstruos: una carpeta independiente por criatura; no mezclar assets de criaturas distintas.
14. Drive conserva fuentes pesadas; GitHub contiene código y solo assets runtime seleccionados/convertidos.

## Referencias

- PokéSurvivor `b297089`: loop, cámara, input, chunks y dinámica general.
- Zircon `80d5df21016b2f377d48f14f7dcc2e994b163ff1`: direcciones, acciones, frames, personajes, items, magias, monstruos y formato estructural de mapas.
- Crystal `0e315fe327192afe52c3d7357ddd1f5b7e26c5b8`: referencia pública para Archer si se activa más adelante.

## Clases ORIGINS

Núcleo inicial: `Warrior`, `Wizard`, `Taoist`, `Assassin`.

`Archer` y `Monk` quedan fuera del alcance inicial. Se podrán añadir después como paquetes de clase independientes si interesan, sin bloquear el desarrollo actual. `crystal-archer-reference.json` se conserva únicamente como referencia futura.

## Apariencias definitivas a importar después

- Base `M001/F001`; noob `M003/F003`.
- Warrior: `M004 > M007 > M002 > M053 > M067` + `Fxxx`.
- Taoist: `M006 > M009 > M010 > M051 > M056` + `Fxxx`.
- Wizard: `M005 > M008 > M011 > M054 > M061` + `Fxxx`.
- Assassin: `M013 > M016 > M014 > M015 > M046` + `Fxxx`.

`M046` sigue siendo Assassin aunque su recurso fuente proceda de otra familia HUM. Importar solo sets elegidos, 8 direcciones, índices MIR y offsets originales, atlas+manifest por apariencia.

## Acciones y estados Player

- `js/core/mir-animation.js`: 43 definiciones `FrameSet.Players` de Zircon.
- `js/systems/player-state.js`: intención `MirAction` separada de `MirAnimation`.
- Prioridad: locomoción < acción < struck < pushed < die < dead.
- One-shot -> Standing; `Die -> Dead`; revive explícito.
- Secuencias: Channelling, DragonRepulse, Fishing y Taming.
- Debug temporal para Combat1-15/transiciones sin sprites.
- Direcciones: `0 Up, 1 UpRight, 2 Right, 3 DownRight, 4 Down, 5 DownLeft, 6 Left, 7 UpLeft`.
- Acciones Archer (`WalkingBow`, `RunningBow`, `AttackRange1/2/3`, `Jump`) quedan registradas como referencia, pero NO se integran al runtime ahora.

## Magias

- `data/magics/zircon-player-magics.json`: IDs, nombres, 124 mappings centrales de animación, reglas de ataque y referencias VFX conocidas para las 4 clases Zircon.
- `data/magics/zircon-magic-mechanics.json`: clasificación mecánica de las 195 entradas Zircon, dependencias/augments, familias, casos especiales y stubs.
- `data/magics/crystal-archer-reference.json`: referencia opcional futura con 21 skills Archer y acciones de arco verificadas.
- Conteo Zircon actual: Warrior 38, Wizard 47, Taoist 52, Assassin 58.
- Arquitectura: servidor decide coste/objetivo/daño/buff/summon/cooldown; cliente reproduce acción/VFX.
- Modelo ORIGINS acordado: pocas skills principales; las magias fuente pueden actuar como `coreSkill`, evolución, modifier, proc, pasiva o utilidad. Las cadenas finales aún NO están fijadas.
- Interacciones Zircon útiles ya registradas: `Burning` sobre familia Fuego; `Shocked` sobre Rayo; `Asteroid -> FireWall`; augments Taoist; combo Lotus Assassin; `Chain -> ChainOfFire`; etc.
- No copiar stubs/bugs a ciegas. Ej.: `DarkConversion.MagicConsume` requiere reimplementación segura.
- Valores exactos Zircon siguen pendientes de `MagicInfo`.
- VFX Zircon a pedir: `Magic.Zl`, `MagicEx.Zl`...`MagicEx11.Zl`, `MonMagicEx7.Zl`, `MonMagicEx8.Zl`, `MonMagicEx20.Zl`, `MIcon.Zl`.

## Mapas MIR3

- Primer objetivo: `01.map` = Border Village.
- Fuente oficial ORIGINS X recibida y validada: `600x600`, `5.310.028 bytes`, SHA1 `61c550cd938573a26efa7ee7067d51d9aa47d391`.
- `assets/maps/border-village/manifest.json`: identidad, hash y 11 librerías Map Data realmente usadas por este mapa.
- `js/core/mir-map.js`: parser completo `.map`: Back/Middle/Front, animación, luz, librerías y colisión.
- Formato verificado contra Zircon: ancho bytes `22-23`, alto `24-25`, header `28`; fondos por bloques 2x2 de 3 bytes; 14 bytes por celda.
- Compatibilidad añadida con mapas válidos que omiten únicamente el último byte de padding.
- `js/systems/map-world.js`: puente runtime para carga, spawn de prueba, límites, movimiento continuo y colisión MIR.
- Grid MIR solo para colisión/navegación; movimiento gameplay continuo.
- Drive conserva `Map` + `Map Data`; importar únicamente las librerías e imágenes usadas por cada mapa.
- Mapas abiertos: perímetro visual/jugable natural e irregular; evitar límites rectos visibles.
- Templos/cuevas/interiores: salas y pasillos amplios; colisión y borde visual derivados de la misma máscara.

## Orden de implementación

1. Convertir `01.map` Border Village a paquete runtime y validar estructura + colisiones.
2. Extraer únicamente imágenes usadas de sus 11 librerías y renderizar Back/Middle/Front.
3. Ver Player real moviéndose correctamente sobre Border Village.
4. Importar/validar primeras magias con VFX y comportamiento real.
5. Importar monstruos: animaciones, lógica, colisión y combate; una carpeta por criatura.
6. Montar spawns, zonas de farmeo y bosses/eventos por coordenadas.
7. Ampliar catálogo de criaturas y biomas/mapas.
8. Interfaz, equipamiento, menús y acabado visual después del gameplay base.

## Estado

- [x] Cliente mínimo, loop, input, cámara y movimiento continuo.
- [x] Definiciones/timings + máquina de estados Player.
- [x] Renderer MIR desacoplado + pipeline M001 validado técnicamente.
- [x] Apariencias definitivas elegidas para las 4 clases iniciales.
- [x] Persistencia lógica fijada según Zircon.
- [x] Parser completo `.map` preparado y contrastado con el lector de Zircon.
- [x] Runtime `MapWorld` conectado a MovementSystem y cámara.
- [x] Border Village `01.map` recibido, validado y registrado.
- [x] Sus 11 librerías exactas de Map Data identificadas.
- [x] 195 magias Zircon Player indexadas y animaciones centrales registradas.
- [x] Clasificación mecánica Zircon y dependencias/augments principales guardadas.
- [ ] Crear paquete runtime de `01.map` sin subir la fuente pesada completa.
- [ ] Extraer/renderizar las imágenes `.Zl` realmente usadas por Border Village.
- [ ] Validar Player visualmente sobre el mapa real.
- [ ] Monstruos, spawn y combate.

## Siguiente paso

Procesar `01.map` recibido y sus 11 librerías exactas de `Map Data`. Empezar por las librerías de suelo, generar assets web mínimos y validar el primer render real antes de importar objetos y capas superiores.