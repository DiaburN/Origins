# ORIGINS — Zircon Asset & Map Library

Este repositorio es la biblioteca maestra de recursos de **Zircon** que utilizaremos para reconstruir mapas reales y reutilizar sus piezas visuales en **ORIGINS IDLE**.

## Objetivo

El flujo de trabajo será:

```text
.Zl originales
    -> extracción PNG + metadata
.MAP original
    -> lectura de celdas y librerías
    -> resolución de IDs en manifests
    -> render completo / minimapa
    -> selección de zona
    -> ampliación con tiles reales
    -> composición horizontal para ORIGINS IDLE
```

Los índices originales de Zircon nunca se renumeran.

## Estructura

- `ZIRCON_ASSETS/originals/` — librerías `.Zl` originales.
- `ZIRCON_ASSETS/extracted/` — imágenes extraídas por librería, conservando ID original.
- `ZIRCON_ASSETS/manifests/` — índice global y metadata de cada librería.
- `MAPS/originals/` — mapas `.map` originales.
- `MAPS/renders/` — renders completos reconstruidos.
- `MAPS/minimaps/` — vistas reducidas generadas desde el mapa real.
- `MAPS/selections/` — recortes/zonas seleccionadas.
- `TOOLS/` — extractores, renderer e inspector.
- `schemas/` — esquemas de manifests.
- `docs/` — especificaciones del pipeline.

## Regla principal

Un render de mapa debe proceder siempre de:

`MAP real + librerías reales + image IDs reales + offsets reales`.

No se generan aproximaciones cuando existen los recursos originales.
