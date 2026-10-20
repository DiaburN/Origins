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
        └── warrior/male/armour_01/
            └── manifest.json
```

## Reglas

1. Revisar este archivo antes de crear carpetas o archivos nuevos.
2. No escanear todo el repositorio para una tarea local.
3. No crear TXT temporales, notas, copias ni documentación redundante.
4. No importar Zircon ni PokéSurvivor completos.
5. Antes de crear un archivo nuevo, comprobar si su función ya existe.
6. Assets y lógica permanecen separados.
7. Una criatura, personaje o magia debe poder añadirse sin modificar el motor salvo mecánica nueva.
8. Posición del gameplay: continua, estilo PokéSurvivor.
9. Dirección y animaciones: estándar MIR3/Zircon de 8 direcciones.
10. Los PNG MIR usan frames lógicos; el manifest conserva librería, frame base y offsets del origen.

## Referencias

- PokéSurvivor `b297089`: loop, cámara, input y dinámica general.
- Zircon `80d5df21016b2f377d48f14f7dcc2e994b163ff1`: reglas MIR3, direcciones, frames y sistemas técnicos.

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
- [x] Paquete de assets para primera armadura M-Hum.
- [ ] Importar PNG + OffSetX/OffSetY reales de M-Hum armour shape 0.
- [ ] Validar Standing/Walking en 8 direcciones con sprite real.
- [ ] Resto de acciones del Player.
- [ ] Mapa y colisiones.
- [ ] Monstruos y spawn.
- [ ] Combate.
- [ ] Magias.

## Siguiente paso

Importar únicamente los frames necesarios de `M_Hum` armour shape 0, conservando sus offsets originales de Zircon. Activar `ready` en el manifest y validar Standing/Walking en las 8 direcciones.
