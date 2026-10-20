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
        └── <race>/<common-or-class>/<gender>/<appearance>/
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
7. Una criatura, personaje, raza o magia debe poder añadirse sin modificar el motor salvo mecánica nueva.
8. Posición del gameplay: continua, estilo PokéSurvivor.
9. Dirección y animaciones: estándar MIR3/Zircon de 8 direcciones.
10. Los frames MIR usan índices lógicos; el manifest conserva librería, frame base y offsets del origen. El renderer admite atlas para evitar miles de peticiones/PNG sueltos.
11. Estructura Player: `race/common-or-class/gender/appearance`; nuevas razas reutilizan el mismo renderer y sistema de animación.
12. Persistencia: copiar el modelo lógico de Zircon: `AccountInfo -> CharacterInfo -> UserItem/UserMagic`; `UserItem -> ItemInfo` y `UserMagic -> MagicInfo`. Adaptar solo almacenamiento/comunicación al entorno web.

## Referencias

- PokéSurvivor `b297089`: loop, cámara, input y dinámica general.
- Zircon `80d5df21016b2f377d48f14f7dcc2e994b163ff1`: reglas MIR3, direcciones, frames, personajes, items y magias.

## Apariencias elegidas

- Base: `M001`; noob común: `M003`.
- Warrior: `M004 > M007 > M002 > M053 > M067`.
- Taoist: `M006 > M009 > M010 > M051 > M056`.
- Wizard: `M005 > M008 > M011 > M054 > M061`.
- Assassin: las selecciones visuales `M013 > M016 > M014 > M015` corresponden realmente a `A002 > A007 > A004 > A006` en las librerías Assassin de Zircon. `M046` pertenece a una librería normal y necesita sustituto Assassin real.
- Femenino: equivalente femenino del mismo shape/librería.

## Estado

- [x] Cliente web mínimo.
- [x] Loop, input, cámara y movimiento continuo.
- [x] Direcciones Zircon 0-7 y Standing/Walking/Running lógicos.
- [x] Renderer MIR3 desacoplado del Player.
- [x] Renderer compatible con atlas.
- [x] Catálogo Hums analizado.
- [x] Warrior/Taoist/Wizard seleccionados.
- [x] Modelo lógico de persistencia fijado siguiendo Zircon.
- [x] Diferencia Assassin verificada: `ArmourShapeOffSet=3000` y shifts por animación.
- [ ] Elegir sustituto Assassin real para `M046`.
- [ ] Importar atlases definitivos y validar Standing/Walking.
- [ ] Resto de acciones del Player.
- [ ] Cuenta/personajes/inventario/equipo/magias según Zircon.
- [ ] Mapa y colisiones.
- [ ] Monstruos y spawn.
- [ ] Combate y magias.

## Siguiente paso

Cerrar el quinto set Assassin usando el catálogo `A001-A026`; después generar/importar los atlases definitivos sin cambiar el renderer.
