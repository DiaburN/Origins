# PROJECT STRUCTURE

Documento corto con la estructura oficial. No duplicar documentación.

```text
Origins/
├── README.md
├── PROJECT_STRUCTURE.md
├── index.html                 # se crea al arrancar el cliente web
├── css/                       # interfaz y canvas
├── js/
│   ├── core/                  # loop, input, cámara, tiempo
│   ├── entities/              # player, monsters, projectiles
│   ├── systems/               # movement, combat, magic, map, spawn
│   └── game.js                # flujo principal
└── assets/
    ├── players/
    │   ├── warrior/
    │   ├── wizard/
    │   └── taoist/
    ├── monsters/
    ├── magic/
    ├── maps/
    ├── tiles/
    ├── objects/
    └── ui/
```

## Reglas

1. Revisar este archivo antes de crear carpetas nuevas.
2. No escanear todo el repositorio para una tarea local.
3. No crear TXT temporales, notas, copias ni documentación redundante.
4. No importar Zircon ni PokéSurvivor completos.
5. Antes de crear un archivo nuevo, comprobar si su función ya existe.
6. Assets y lógica deben estar separados.
7. Una criatura, personaje o magia debe poder añadirse sin modificar el motor salvo que necesite una mecánica nueva.

## Orden actual

1. Cliente web mínimo.
2. Player MIR3.
3. Movimiento + cámara.
4. Animaciones completas del player.
5. Mapa + tiles + colisiones.
6. Monstruos + spawn.
7. Combate.
8. Magias.
9. Progresión y resto de gameplay.
