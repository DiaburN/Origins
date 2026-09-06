# ZL Extractor

Extractor reproducible de librerías gráficas **Zircon** para la biblioteca maestra de ORIGINS.

## Reglas

- Nunca renumera IDs.
- Los PNG usan el ID original (`00000.png`, `00001.png`, ...).
- Los huecos de la librería permanecen huecos; no se compactan.
- Conserva `width`, `height`, `offsetX`, `offsetY` y metadata de shadow/overlay.
- No aplica clasificación visual ni transparencia inventada.
- La salida PNG es RGBA y conserva el alpha codificado en la librería.

## Formatos

- **ZL legacy v0**: metadata legacy + payload DXT1.
- **ZL legacy v1**: metadata legacy + payload DXT5.
- **ZL2**: detectado por firma `ZL2`, con metadata/index/payloads comprimidos y codecs por imagen.

La implementación sigue la estructura de `MirLibrary`, `ZlImageMetadata` y `ZlFormat` del código fuente público de Zircon.

## Uso

```bash
python -m pip install -r TOOLS/zl_extractor/requirements.txt
python TOOLS/zl_extractor/zl_extract.py MapData/Forest/Tiles5c.Zl \
  --source-root MapData \
  --extracted-root ZIRCON_ASSETS/extracted \
  --manifests-root ZIRCON_ASSETS/manifests
```

Para analizar headers y generar metadata sin decodificar PNG:

```bash
python TOOLS/zl_extractor/zl_extract.py MapData --source-root MapData --scan-only
```

## Salida

Para `MapData/Forest/Tiles5c.Zl`:

```text
ZIRCON_ASSETS/
  extracted/
    Forest/
      Tiles5c/
        00000.png
        ...
  manifests/
    Forest/
      Tiles5c.json
```

El manifest mantiene el ID numérico original y la ruta PNG correspondiente. Los slots vacíos se registran como `present: false` cuando se genera un manifest completo.
