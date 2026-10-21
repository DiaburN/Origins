# PROJECT STRUCTURE

Único documento de estructura del proyecto. Mantener corto y actualizado.

```text
Origins/
├── README.md
├── PROJECT_STRUCTURE.md
├── index.html
├── css/game.css
├── js/
│   ├── core/        # config, input, cámara, MIR animation/sprites
│   ├── entities/    # Player
│   ├── systems/     # movimiento y futuros sistemas
│   └── game.js
└── assets/
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
- Zircon `80d5df21016b2f377d48f14f7dcc2e994b163ff1`: direcciones, acciones, frames, personajes, items y magias.

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

## Acciones Player Zircon

La fuente autoritativa es `js/core/mir-animation.js`. Ya contiene las 43 definiciones de `FrameSet.Players`, con inicio, número de frames, offset de dirección, timing, delays especiales, reverse/static-speed y política loop/once/hold.

Incluye:
- Standing / Walking / Running.
- CreepStanding / CreepWalkSlow / CreepWalkFast.
- Pushed / Stance / Harvest.
- Combat1-Combat15.
- DragonRepulse Start/Middle/End.
- Struck / Die / Dead.
- Fishing Cast/Wait/Reel.
- Horse Standing/Walking/Running/Struck/Leaping.
- Channelling Start/Middle/End.
- Taming Cast/Wait.

Direcciones fijas Zircon: `0 Up, 1 UpRight, 2 Right, 3 DownRight, 4 Down, 5 DownLeft, 6 Left, 7 UpLeft`.

## Estado

- [x] Cliente web mínimo, loop, input y cámara.
- [x] Movimiento continuo y direcciones Zircon 0-7.
- [x] Todas las definiciones/timings Player de Zircon registradas.
- [x] Animator soporta loop, acciones one-shot, hold, reverse y delays por frame.
- [x] Renderer MIR desacoplado y compatible con atlas.
- [x] Catálogo HUM analizado y apariencias definitivas elegidas.
- [x] Pipeline M001 probado como validación técnica.
- [x] Modelo lógico de persistencia fijado siguiendo Zircon.
- [ ] Implementar máquina de estados/transiciones del Player sobre esas acciones.
- [ ] Validar transiciones y timings con representación diagnóstica/placeholders.
- [ ] Importar solo entonces las apariencias definitivas anteriores.
- [ ] Cuenta/personajes/inventario/equipo/magias según Zircon.
- [ ] Mapa y colisiones.
- [ ] Monstruos, spawn, combate y magias.

## Siguiente paso

Crear la máquina de estados del Player que decide cuándo entra/sale de Standing, Moving, Pushed, Attack, Spell, Struck, Die, etc., usando exclusivamente las definiciones ya fijadas en `mir-animation.js`.
