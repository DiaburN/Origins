# ORIGINS DxR — arquitectura maestra

`Origins-DxR` es la línea activa única de desarrollo de ORIGINS MOBILE.

## Fuente funcional única

- Runtime: `Suprcode/Zircon`.
- Commit fijado: `cbf1aa919083bc13fc3f23f93772a8ab8370632d`.
- Base de datos: MirDB/System.db/Users.db de Zircon.
- Magias: `MagicType`, `MagicInfo`, `UserMagic`, `MagicObject` y lógica cliente/servidor nativos de Zircon.
- Personaje, movimiento, combate, estados y animaciones: arquitectura Zircon.

Crystal y Crystal-Monk NO forman parte del runtime, la base de datos activa ni el catálogo de magias de esta rama.

El trabajo anterior se conserva fuera de esta línea en:

- `archive/crystal-spells-complete`
- `archive/crystal-player-actions`

No se borrará ni se reutilizará implícitamente código Crystal desde esos archivos.

## Clases activas

Solo las cuatro clases que Zircon define de forma nativa:

1. Warrior
2. Wizard
3. Taoist
4. Assassin

Archer y Monk quedan fuera de alcance hasta una decisión futura explícita.

## Política de magias

El catálogo fuente es exclusivamente `LibraryCore/Enum.cs::MagicType` del commit fijado de Zircon.

Una entrada del enum no implica por sí sola que la magia esté disponible. La validación distingue:

- `ENUM_DEFINED`: existe en `MagicType`.
- `DB_PRESENT`: existe como `MagicInfo` en el System.db de Zircon.
- `RUNTIME_HANDLER_PRESENT`: existe una ruta de ejecución Zircon.
- `PLAYABLE`: DB + runtime + clase coinciden y la magia puede usarse.
- `UPSTREAM_NOT_CODED`: Zircon la marca explícitamente `NOT CODED`.
- `UPSTREAM_UNUSED`: Zircon la marca explícitamente `UNUSED`.

ORIGINS-DxR no inventará handlers para convertir automáticamente entradas incompletas de Zircon en magias activas. Primero reconstruimos Zircon fielmente.

## Base de datos

La base inicial se obtiene con:

- `scripts/fetch-zircon-system-db.sh`
- `scripts/fetch-zircon-system-db.ps1`

El `System.db` de Zircon es el punto de partida autoritativo. Los datos propios de ORIGINS se añadirán después como cambios deliberados y compatibles con el esquema Zircon.

No existe overlay Crystal de magias en esta rama.

## Interfaz

La interfaz visual aprobada de ORIGINS se conserva al 100 % como shell de cliente. Su base consolidada es:

`Origins_GameInter_Navegable_v1.0_MINIMAP_CONTROLES_BAJADOS.zip`

Reglas:

- no reconstruir ni rediseñar módulos aprobados;
- no recolocar HUD, minimapa, ventanas ni controles ya validados;
- conservar assets separados y textos dinámicos/traducibles;
- conectar la ventana de magias a los datos Zircon de las cuatro clases;
- la interfaz no decide comportamiento de combate: el runtime Zircon sigue siendo autoritativo.

La copia binaria del paquete GameInter se integrará como bloque íntegro cuando esté disponible en el checkout/almacenamiento del repositorio; no se sustituirá por una reconstrucción aproximada.

## Regla de continuidad

No se crearán ramas `v1`, `v2`, etc. para esta línea. El desarrollo funcional continúa sobre `Origins-DxR`, usando commits para mantener historial y recuperación.