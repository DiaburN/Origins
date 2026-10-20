# PROJECT STRUCTURE

Único documento de estructura del proyecto. Mantener corto y actualizado.

```text
Origins/
├── README.md
├── PROJECT_STRUCTURE.md
├── index.html
├── css/
│   └── game.css
├── js/
│   ├── core/
│   │   ├── config.js
│   │   ├── math.js
│   │   ├── mir-animation.js
│   │   ├── mir-sprites.js
│   │   ├── input.js
│   │   └── camera.js
│   ├── entities/
│   │   └── player.js
│   ├── systems/
│   │   └── movement.js
│   └── game.js
└── assets/
    └── players/
        └── <race>/<class>/<gender>/<armour>/
            ├── manifest.json
            └── frames/
```

## Reglas

1. Revisar este archivo antes de crear carpetas o archivos nuevos.
2. No escanear todo el repositorio para una tarea local.
3. No crear TXT temporales, notas, copias ni documentación redundante.
4. No importar Zircon ni PokéSurvivor completos.
5. Antes de crear un archivo nuevo, comprobar si su función ya existe.
6. Assets y lógica permanecen separados.
7. Una criatura, personaje, raza o magia debe poder añadirse sin modificar el motor salvo mecánica nueva.
8. Posición del gameplay: continua, estilo PokéSurvivor.
9. Dirección y animaciones: estándar MIR3/Zircon de 8 direcciones.
10. Los PNG MIR usan frames lógicos; el manifest conserva librería, frame base y offsets del origen.
11. Estructura Player: `race/class/gender/armour`; nuevas razas reutilizan el mismo renderer y sistema de animación.
12. Persistencia: copiar el modelo lógico de Zircon, separando definiciones y estado del jugador: `AccountInfo -> CharacterInfo -> UserItem/UserMagic`; `UserItem -> ItemInfo` y `UserMagic -> MagicInfo`. Adaptar solo la capa de almacenamiento/comunicación al entorno web.

## Referencias

- PokéSurvivor `b297089`: loop, cámara, input y dinámica general.
- Zircon `80d5df21016b2f377d48f14f7dcc2e994b163ff1`: reglas MIR3, direcciones, frames, datos de personajes/items/magias y sistemas técnicos.

## Apariencias elegidas

- Base: `M001`; noob común: `M003`.
- Warrior: `M004 > M007 > M002 > M053 > M067`.
- Taoist: `M006 > M009 > M010 > M051 > M056`.
- Wizard: `M005 > M008 > M011 > M054 > M061`.
- Assassin: `M013 > M016 > M014 > M015 > M046`.
- Femenino: equivalentes `Fxxx` del mismo código/orden cuando existan.

## Estado

- [x] Cliente web mínimo.
- [x] Loop con delta limitado.
- [x] Input WASD/flechas normalizado.
- [x] Cámara independiente con seguimiento suave.
- [x] Player separado de MovementSystem.
- [x] Direcciones Zircon 0-7.
- [x] Standing/Walking/Running definidos con frames lógicos Zircon.
- [x] Movimiento continuo + Standing/Walking.
- [x] Renderer MIR3 desacoplado del Player.
- [x] Assets preparados para múltiples razas/clases/géneros.
- [x] Catálogo fuente Hums analizado: 69 apariencias masculinas + 69 femeninas.
- [x] Apariencias definitivas seleccionadas.
- [x] Modelo lógico de persistencia fijado siguiendo Zircon.
- [ ] Importar todos los frames/offsets de las apariencias elegidas.
- [ ] Validar Standing/Walking en 8 direcciones con sprite real.
- [ ] Resto de acciones del Player.
- [ ] Cuenta/personajes/inventario/equipo/magias siguiendo asociaciones Zircon.
- [ ] Mapa y colisiones.
- [ ] Monstruos y spawn.
- [ ] Combate.
- [ ] Magias.

## Siguiente paso

Extraer únicamente las apariencias seleccionadas con sus frames/offsets reales de Zircon y validar Standing/Walking antes de ampliar acciones o persistencia.
