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
│   └── magics/zircon-player-magics.json
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
4. No importar Zircon ni PokéSurvivor completos.
5. Antes de crear un archivo nuevo, comprobar si su función ya existe.
6. Assets y lógica permanecen separados.
7. Posición: continua estilo PokéSurvivor. Dirección/acciones: estándar MIR3/Zircon.
8. El renderer debe aceptar cualquier apariencia sin cambiar el motor.
9. Persistencia seguirá el modelo lógico Zircon: `AccountInfo -> CharacterInfo -> UserItem/UserMagic`; `UserItem -> ItemInfo`; `UserMagic -> MagicInfo`.
10. NO importar sprites definitivos hasta validar el sistema de acciones/movimiento del Player.
11. Magias: copiar comportamiento/arquitectura Zircon; lógica autoritativa separada de gráficos.

## Referencias

- PokéSurvivor `b297089`: loop, cámara, input y dinámica general.
- Zircon `80d5df21016b2f377d48f14f7dcc2e994b163ff1`: direcciones, acciones, frames, personajes, items, magias y formato estructural de mapas.

## Apariencias definitivas a importar después

Orden visual AUTORITATIVO; no cambiarlo por la librería de origen:

- Base: `M001/F001`; noob común: `M003/F003`.
- Warrior: `M004 > M007 > M002 > M053 > M067` + `Fxxx`.
- Taoist: `M006 > M009 > M010 > M051 > M056` + `Fxxx`.
- Wizard: `M005 > M008 > M011 > M054 > M061` + `Fxxx`.
- Assassin: `M013 > M016 > M014 > M015 > M046` + `Fxxx`.

`M046` sigue siendo Assassin aunque su recurso fuente proceda de otra familia HUM.

Importación: localizar librería+slot por código, solo sets elegidos, 8 direcciones sin espejar/rotar, conservar índices MIR y `OffSetX/OffSetY`, atlas+manifest por apariencia.

## Acciones y estados Player

- `js/core/mir-animation.js`: 43 definiciones `FrameSet.Players` de Zircon.
- `js/systems/player-state.js`: intención (`MirAction`) separada de animación (`MirAnimation`).
- Prioridad: locomoción < acción < struck < pushed < die < dead.
- One-shot bloquea locomoción y vuelve a Standing; `Die -> Dead`; revive explícito.
- Secuencias: Channelling, DragonRepulse, Fishing y Taming.
- Debug temporal permite probar Combat1-15 y transiciones sin sprites.
- Direcciones: `0 Up, 1 UpRight, 2 Right, 3 DownRight, 4 Down, 5 DownLeft, 6 Left, 7 UpLeft`.

## Magias Zircon

- Fuente de trabajo: `data/magics/zircon-player-magics.json`.
- Catalogadas las 195 entradas player: Warrior 38, Wizard 47, Taoist 52, Assassin 58.
- El catálogo guarda ID, nombre interno, animación corporal central cuando existe y reglas especiales de ataque.
- `Functions.GetMagicAnimation` de Zircon aporta 124 mappings directos de cast; las restantes pueden ser ataque, pasiva, toggle, augment o lógica especial y se resuelven en su clase de servidor.
- Arquitectura a conservar: el servidor decide coste/objetivo/daño/buff/summon/cooldown; cliente solo reproduce acción y efectos.
- `MagicInfo` contiene valores configurables (potencia, coste, niveles, EXP, delay, descripción); `UserMagic` guarda estado aprendido/nivel/EXP/teclas/cooldown.
- Patrones visuales ya identificados: proyectiles, efectos directos, objetos persistentes de suelo y efectos persistentes de buff/debuff.
- Para assets player se pedirá después un ZIP con `Magic.Zl`, `MagicEx.Zl` ... `MagicEx11.Zl` y `MIcon.Zl`.
- Para copiar valores exactos se pedirá además export de `MagicInfo`; si no se puede exportar, el `System.db` relevante para extraerlo.
- No pedir todavía `MonMagic*` ni sonidos: son fases separadas.

## Mapas MIR3

- `js/core/mir-map.js` sigue el parser estructural `.map` de Zircon.
- Ancho bytes `22-23`, alto `24-25`; offset celdas `28 + floor(width*height/4)*3`; 14 bytes por celda.
- Celda transitable cuando el flag contiene `0x02` y `0x01`.
- Movimiento del gameplay sigue siendo continuo; grid MIR solo para colisión/navegación.
- Render real pendiente de `0.map` + librerías de tiles.

## Estado

- [x] Cliente web mínimo, loop, input y cámara.
- [x] Movimiento continuo + direcciones Zircon 0-7.
- [x] Definiciones/timings y máquina de estados Player.
- [x] Renderer MIR desacoplado + pipeline M001 validado técnicamente.
- [x] Apariencias definitivas elegidas.
- [x] Persistencia lógica fijada según Zircon.
- [x] Parser estructural `.map` preparado.
- [x] 195 magias Player indexadas y mappings de animación central registrados.
- [x] Paquete de assets de magia necesario identificado.
- [ ] Validar Player visualmente en navegador.
- [ ] Completar auditoría mecánica/visual detallada de cada magia antes de implementar combate.
- [ ] Recibir/importar `Magic*.Zl`, `MIcon.Zl` y datos `MagicInfo`.
- [ ] Probar `0.map` real + colisiones + renderer de mapa.
- [ ] Monstruos, spawn y combate.

## Siguiente paso

Mientras no estén disponibles los assets/mapas del PC, completar el catálogo mecánico de magias desde Zircon: distinguir ataque, proyectil, área, buff/debuff, summon, movimiento, toggle/pasiva y persistencia, sin inventar valores que pertenecen a `MagicInfo`.