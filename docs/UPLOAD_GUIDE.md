# Subida de assets

## Librerías ZL

Colocar los `.Zl` originales en `ZIRCON_ASSETS/originals/`.

El repositorio está preparado para usar Git LFS con `.Zl`, porque algunas librerías pueden superar los límites normales de GitHub.

## PNG extraídos

Los PNG individuales deben quedar en Git normal, no LFS, para que puedan localizarse y descargarse directamente por ID.

Si una librería produce un volumen excesivo de datos, se dividirá por carpetas/rangos de índice sin alterar los IDs.

Ejemplo:

```text
ZIRCON_ASSETS/extracted/forest-tiles/
  00000.png
  00001.png
  ...
```
