# ORIGINS HPR -> Zircon Monster Builder

Herramienta para convertir bibliotecas de monstruos **HispaCrystal `.hpr`** a un paquete listo para integrar en Zircon, sin adivinar comportamiento de servidor.

## Qué hace

Por cada `.hpr`:

- verifica la firma `HispaCrystal`;
- detecta el layout de los registros de imagen;
- descomprime los sprites BGRA/gzip;
- conserva los **índices originales**;
- conserva X/Y y metadatos de sombra;
- reutiliza los `CURSOR_PROFILE.json` o `ALL_MONSTERS_CURSOR_MANIFEST.json` ya verificados cuando existen;
- calcula exactamente qué índices usa cada acción y cada dirección;
- marca gráficos no referenciados como candidatos a efectos/overlays, sin asignarlos a ciegas;
- genera una `.Zl` ZL2 con payload PNG;
- valida el contenedor `.Zl` después de escribirlo;
- genera instrucciones para Cursor;
- genera `MASTER_SHEET.csv`, `MASTER_SHEET.json` y `MASTER_SHEET.html` al terminar un lote.

No genera GIFs. Los PNG individuales son opcionales con `--export-png`.

## Regla fundamental

La herramienta separa **visual** de **IA/comportamiento de servidor**.

Un nombre como `Attack1`, `AttackRange1`, `Spell` o `Special` solo identifica un bloque visual. No demuestra daño, rango, proyectil, heal ni AI. El caso `1911 / AttackRange1 -> SelfHeal / HealingAnt` está incluido como override confirmado precisamente para impedir que Cursor convierta todos los `AttackRange1` en ataques a distancia.

## Instalación

Windows:

```bat
cd TOOLS\hpr_zircon_builder
py -m pip install -r requirements.txt
```

## Uso recomendado con las 650 Hispa

1. Pon las `.hpr` en una carpeta, por ejemplo:

```text
D:\HISPA_HPR\
  000.hpr
  001.hpr
  ...
  1911.hpr
```

2. Descomprime el paquete de análisis anterior que contiene los `CURSOR_PROFILE.json` de las 650 bibliotecas. Por ejemplo:

```text
D:\HISPA_ANALYSIS\
  ...\000\CURSOR_PROFILE.json
  ...\001\CURSOR_PROFILE.json
  ...
```

3. Ejecuta:

```bat
py origins_hpr_zircon.py batch "D:\HISPA_HPR" ^
  --analysis-root "D:\HISPA_ANALYSIS" ^
  --out "D:\HISPA_ZIRCON_READY"
```

También se puede usar el manifiesto global:

```bat
py origins_hpr_zircon.py batch "D:\HISPA_HPR" ^
  --manifest "D:\ALL_MONSTERS_CURSOR_MANIFEST.json" ^
  --out "D:\HISPA_ZIRCON_READY"
```

La herramienta acepta también un `.zip` que contenga `.hpr`.

## Salida

```text
HISPA_ZIRCON_READY/
├─ MASTER_SHEET.csv
├─ MASTER_SHEET.json
├─ MASTER_SHEET.html
├─ BATCH_SUMMARY.txt
├─ FAILURES.json
└─ MONSTERS/
   ├─ 000/
   │  ├─ Hispa_000.Zl
   │  ├─ CURSOR_PROFILE.json
   │  ├─ IMAGE_METADATA.csv
   │  ├─ FRAMESET.cs.txt
   │  ├─ CURSOR_IMPORT_THIS_MONSTER.md
   │  └─ VALIDATION.txt
   ├─ 001/
   └─ ...
```

Con `--export-png` también crea `FRAMES_PNG/`, pero **no es necesario** para construir la `.Zl`.

## Qué contiene `CURSOR_PROFILE.json`

- índice inicial de cada animación;
- número de frames;
- stride/direction offset;
- delay;
- reverse;
- `source_indices_by_direction` con los índices exactos usados en cada dirección;
- `source_indices` con el conjunto exacto de sprites usados por la acción;
- lista de gráficos no referenciados;
- issues/warnings;
- `mir2_to_zircon_direction_shift = 3`;
- semántica visual/servidor separada.

## Dirección Mir2 -> Zircon

La política por defecto es **preservar físicamente los índices originales**. No gira ni renumera imágenes.

El perfil generado indica:

```text
Mir2DirMap.Shift = 3
```

Cursor debe aplicar esa transformación en el registro/renderer específico del monstruo. Así no se destruyen índices, efectos ni FrameSets raros.

## Casos AUTO / REVIEW

La herramienta no falsea una conversión.

Si puede demostrar la tabla de imágenes pero no tiene un FrameSet verificado, crea el análisis de imágenes y marca:

```text
REVIEW_FRAMESET_UNKNOWN
```

Para las 650 Hispa ya analizadas, usa `--analysis-root` o `--manifest` y el programa reutiliza esos perfiles en vez de inferirlos de nuevo.

Si una HPR no encaja con ninguno de los layouts de imagen comprobables, se añade a `FAILURES.json` y el lote continúa.

## MasterSheet

`MASTER_SHEET.csv/json/html` incluye, por monstruo:

- HPR ID;
- versión;
- layout de registros detectado;
- slots totales;
- imágenes reales;
- estado;
- origen del FrameSet;
- acciones;
- acciones con comportamiento desconocido;
- número de gráficos sin referenciar;
- `.Zl` generada;
- issues;
- warnings.

El HTML tiene filtro rápido para buscar por ID, acción, estado o error.

## Integración con Cursor

Después de generar el lote, el flujo debe ser así:

> "Coge `MONSTERS/1829` y mételo en Mon8 slot 6."

Cursor debe leer `CURSOR_IMPORT_THIS_MONSTER.md` y los archivos de la carpeta. El destino Mon/slot lo decide el usuario; la herramienta no lo inventa.

## Comandos

Inspeccionar una sola HPR sin crear archivos:

```bat
py origins_hpr_zircon.py inspect 1829.hpr --manifest ALL_MONSTERS_CURSOR_MANIFEST.json
```

Procesar carpeta completa:

```bat
py origins_hpr_zircon.py batch D:\HISPA_HPR --out D:\HISPA_ZIRCON_READY
```

Guardar también PNGs:

```bat
py origins_hpr_zircon.py batch D:\HISPA_HPR --out D:\HISPA_ZIRCON_READY --export-png
```

Solo analizar, sin `.Zl`:

```bat
py origins_hpr_zircon.py batch D:\HISPA_HPR --out D:\HISPA_ANALYSIS_ONLY --no-zl
```

## Importante sobre el escritor ZL2

El escritor usa el mismo contenedor que entiende `TOOLS/zl_extractor/zl_extract.py` de Origins:

- firma `ZL2`;
- versión 2;
- índices de slot preservados;
- codec interno PNG;
- sin compresión adicional del entry (`compression=none`);
- metadata X/Y preservada;
- validación de offsets, índice y firma PNG tras escribir.

Esto evita volver a DXT/BC7 durante la conversión y reduce los puntos donde se podría perder información. Más adelante, si se desea, Zircon/LibraryEditor puede recomprimir la librería.

## Autotest

Ejecutar:

```bat
py selftest.py
```

El test fabrica una pequeña HPR sintética, la vuelve a leer, genera ZL2 y comprueba el contenedor.
