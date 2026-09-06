# Manifests de librerías

Cada `.Zl` extraído tendrá un manifest JSON. El nombre del manifest debe coincidir con la clave estable de la librería.

Cada imagen debe conservar como mínimo:

- `id`
- `file`
- `width`
- `height`
- `offsetX`
- `offsetY`
- `sourceLibrary`
- `present`

Cuando conozcamos el uso real también podremos añadir `category`, `layer`, `mapUsage` y notas, sin cambiar nunca el ID original.
