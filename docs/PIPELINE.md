# Pipeline de reconstrucción

## 1. Ingesta de librerías

Guardar `.Zl` original en `ZIRCON_ASSETS/originals/`.

## 2. Extracción

Extraer cada imagen a:

`ZIRCON_ASSETS/extracted/<library-key>/<id>.png`

con alpha real y sin renumerar.

## 3. Manifest

Guardar metadata en:

`ZIRCON_ASSETS/manifests/<library-key>.json`

y registrar la librería en `library_index.json`.

## 4. Ingesta del mapa

Guardar `.map` en `MAPS/originals/` y registrar sus dimensiones/formato en `MAPS/catalog.json`.

## 5. Reconstrucción

El renderer lee el mapa, determina librerías/IDs, resuelve PNGs en los manifests y dibuja las capas respetando offsets.

## 6. Selección

A partir del render se podrán definir regiones por coordenadas del mapa. Una región se vuelve a renderizar a tamaño grande con los assets originales.

## 7. ORIGINS IDLE

Las zonas seleccionadas sirven como catálogo visual. Las piezas aprobadas se combinan después en segmentos horizontales nuevos para el juego Idle.
