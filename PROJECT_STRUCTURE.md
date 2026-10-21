# PROJECT STRUCTURE

Único documento de estructura del proyecto. Mantener corto y actualizado.

```text
Origins/
├── README.md
├── PROJECT_STRUCTURE.md
├── index.html
├── css/game.css
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
10. NO importar más sprites definitivos hasta cerrar y validar todo el sistema de acciones/movimiento del Player.

## Referencias

- PokéSurvivor `b297089`: loop, cámara, input y dinámica general.
- Zircon `80d5df21016b2f377d48f14f7dcc2e994b163ff1`: direcciones, acciones, frames, personajes, items, magias y formato estructural de mapas.

## Apariencias definitivas a importar después

Orden visual AUTORITATIVO; no cambiarlo por la librería de origen:

- Base aparición: `M001` / `F001`.
- Noob común: `M003` / `F003`.
- Warrior: `M004 > M007 > M002 > M053 > M067` y equivalentes `Fxxx`.
- Taoist: `M006 > M009 > M010 > M051 > M056` y equivalentes `Fxxx`.
- Wizard: `M005 > M008 > M011 > M054 > M061` y equivalentes `Fxxx`.
- Assassin: `M013 > M016 > M014 > M015 > M046` y equivalentes `Fxxx`.

`M046` se mantiene como quinto set Assassin aunque su recurso fuente proceda de otra familia HUM: en ORIGINS X la clase es dato del juego y no depende del nombre de la librería Zircon.

### Cómo se importarán

1. Usar la entrada exacta `Mxxx/Fxxx` del catálogo HUM ya analizado para localizar librería + slot fuente.
2. Extraer únicamente las apariencias anteriores; no importar el catálogo completo.
3. Mantener las 8 direcciones Zircon sin espejar ni rotar.
4. Mantener índices lógicos de acción/frame y `OffSetX/OffSetY` originales.
5. Empaquetar cada apariencia en atlas + manifest.
6. Masculino y femenino comparten el mismo sistema de acciones.
7. M001 fue solo una validación del pipeline; no continuar importando assets todavía.

## Acciones y estados Player

- `js/core/mir-animation.js`: fuente autoritativa de las 43 definiciones `FrameSet.Players` de Zircon.
- `js/systems/player-state.js`: máquina de estados; separa intención (`MirAction`) de animación (`MirAnimation`).
- Prioridad: locomoción < acción < struck < pushed < die < dead.
- Acciones one-shot bloquean locomoción y al terminar vuelven a Standing.
- `Die -> Dead` automático; Dead persiste hasta revive.
- Secuencias preparadas: Channelling, DragonRepulse, Fishing y Taming.
- Locomoción preparada para Standing/Walking/Running, creep y caballo.
- Debug temporal en `game.js` permite probar Combat1-15 y transiciones sin sprites.

Direcciones fijas Zircon: `0 Up, 1 UpRight, 2 Right, 3 DownRight, 4 Down, 5 DownLeft, 6 Left, 7 UpLeft`.

## Mapas MIR3

- `js/core/mir-map.js` contiene el parser estructural del `.map` siguiendo Zircon.
- Lee ancho en bytes `22-23`, alto en `24-25`.
- Offset de celdas: `28 + floor(width*height/4)*3`.
- Cada celda estructural ocupa 14 bytes.
- Una celda es transitable cuando el flag contiene `0x02` y `0x01`.
- Mantener gameplay continuo; la rejilla MIR se usará para colisiones/navegación, no para convertir el movimiento del Player en grid-step.
- Render de tiles/objetos queda pendiente de disponer de `0.map` real y sus librerías de tiles.

## Estado

- [x] Cliente web mínimo, loop, input y cámara.
- [x] Movimiento continuo y direcciones Zircon 0-7.
- [x] Todas las definiciones/timings Player de Zircon registradas.
- [x] Animator soporta loop, one-shot, hold, reverse y delays por frame.
- [x] Máquina de estados/transiciones Player implementada.
- [x] Movement respeta acciones bloqueantes y muerte.
- [x] Controles diagnósticos para probar estados sin sprites.
- [x] Renderer MIR desacoplado y compatible con atlas.
- [x] Catálogo HUM analizado y apariencias definitivas elegidas.
- [x] Pipeline M001 probado como validación técnica.
- [x] Modelo lógico de persistencia fijado siguiendo Zircon.
- [x] Parser estructural MIR3 `.map` implementado y validado con buffer sintético.
- [ ] Validar visualmente todas las transiciones/timings en navegador.
- [ ] Probar parser contra `0.map` real y conectar colisiones.
- [ ] Implementar render de suelo/tiles/objetos MIR3.
- [ ] Ajustar locomoción final (velocidad de run/creep) con gameplay PokéSurvivor.
- [ ] Importar solo entonces las apariencias definitivas anteriores.
- [ ] Cuenta/personajes/inventario/equipo/magias según Zircon.
- [ ] Monstruos, spawn, combate y magias.

## Siguiente paso

Cuando haya un `.map` real disponible, cargar `0.map`, verificar dimensiones/celdas transitables y conectar colisiones. Hasta entonces se puede seguir preparando el renderer de tiles sin inventar datos del archivo.
