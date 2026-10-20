# PROJECT STRUCTURE

Único documento de estructura del proyecto. Mantener corto y actualizado.

```text
Origins/
├── README.md
├── PROJECT_STRUCTURE.md
├── index.html
├── css/
│   └── game.css
└── js/
    ├── core/
    │   ├── config.js
    │   ├── math.js
    │   ├── mir-animation.js
    │   ├── input.js
    │   └── camera.js
    ├── entities/
    │   └── player.js
    ├── systems/
    │   └── movement.js
    └── game.js
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
- [ ] Renderer real de sprites MIR3.
- [ ] Primera armadura M-Hum completa.
- [ ] Resto de acciones del Player.
- [ ] Mapa y colisiones.
- [ ] Monstruos y spawn.
- [ ] Combate.
- [ ] Magias.

## Siguiente paso

Crear el renderer de assets MIR3 y conectar una única armadura M-Hum de prueba sin modificar Player ni MovementSystem.
