# ORIGINS HPR -> Zircon Monster Builder V2

Herramienta para convertir bibliotecas de monstruos **HispaCrystal `.hpr`** a paquetes listos para integrar en Zircon y generar un MasterSheet completo, sin adivinar comportamiento de servidor.

La entrada recomendada es `origins_hpr_zircon_v2.py`. Esta versión incorpora el layout HispaCrystal v3 contrastado con HPR reales de la colección ORIGINS (`000.hpr` y `001.hpr`).

## Qué hace

Por cada `.hpr`:

- verifica la firma `HispaCrystal`;
- en v3 lee `version`, `slot_count`, `FrameSet offset` y la tabla real de offsets;
- conserva el ID original de cada slot;
- lee el registro real de 17 bytes por imagen (`width/height/X/Y/shadow/compressedLength`);
- descomprime los sprites gzip/BGRA32;
- conserva X/Y y metadatos de sombra;
- reutiliza los `CURSOR_PROFILE.json` o `ALL_MONSTERS_CURSOR_MANIFEST.json` ya verificados cuando existen;
- calcula exactamente qué índices usa cada acción y cada dirección;
- marca gráficos no referenciados como candidatos a efectos/overlays, sin asignarlos a ciegas;
- genera una `.Zl` ZL2 con payload PNG;
- valida la `.Zl` después de escribirla;
- genera instrucciones específicas para Cursor;
- genera `MASTER_SHEET.csv`, `MASTER_SHEET.json` y `MASTER_SHEET.html` al terminar el lote.

No necesita GIFs. Los PNG individuales son opcionales con `--export-png`.

## Regla fundamental

La herramienta separa **visual** de **IA/comportamiento de servidor**.

Un nombre como `Attack1`, `AttackRange1`, `Spell` o `Special` solo identifica un bloque visual. No demuestra daño, rango, proyectil, heal ni AI. El caso confirmado `1911 / AttackRange1 -> SelfHeal / HealingAnt` está incluido en `SEMANTICS_OVERRIDES.csv` para impedir que Cursor convierta todos los `AttackRange1` en ataques a distancia.

## HispaCrystal v3 verificado

Cabecera usada por V2:

```text
0x00  12 bytes   "HispaCrystal"
0x0C  uint32     version (=3)
0x10  uint32     número de slots
0x14  uint32     offset absoluto donde empieza FrameSet
0x18  uint32[]   offset de registro de cada slot
```

Los offsets de imagen están almacenados relativos al final de la firma de 12 bytes:

```text
physical_record_offset = stored_offset + 12
```

Registro de imagen presente:

```text
uint16 width
uint16 height
int16  x
int16  y
int16  shadow_x
int16  shadow_y
uint8  shadow_type
uint32 compressed_length
byte[] gzip(BGRA32)
```

El lector **no atraviesa el `FrameSet offset`**. Si un índice o payload sale del área de imágenes, se marca error/revisión en vez de inventar datos.

## Instalación

Windows:

```bat
cd TOOLS\hpr_zircon_builder
py -m pip install -r requirements.txt
```

O simplemente ejecuta:

```text
START_WINDOWS.bat
```

## Uso recomendado con las 650 Hispa

1. Pon las `.hpr` dentro de `INPUT_HPR` o en otra carpeta.
2. Recomendado: usa el análisis anterior de las 650 bibliotecas, porque ya contiene los FrameSets visuales comprobados (`CURSOR_PROFILE.json`).
3. Ejecuta:

```bat
py origins_hpr_zircon_v2.py batch "D:\HISPA_HPR" ^
  --analysis-root "D:\HISPA_ANALYSIS" ^
  --out "D:\HISPA_ZIRCON_READY"
```

También se puede usar directamente el manifiesto global:

```bat
py origins_hpr_zircon_v2.py batch "D:\HISPA_HPR" ^
  --manifest "D:\ALL_MONSTERS_CURSOR_MANIFEST.json" ^
  --out "D:\HISPA_ZIRCON_READY"
```

La herramienta acepta archivos `.hpr`, carpetas completas y ZIPs que contengan `.hpr`.

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

Con `--export-png` también crea `FRAMES_PNG/`, pero no es necesario para construir la `.Zl`.

## Qué contiene `CURSOR_PROFILE.json`

- índice inicial de cada animación;
- número de frames;
- stride/direction offset;
- delay;
- reverse;
- `source_indices_by_direction` con los índices exactos usados en cada dirección;
- `source_indices` con el conjunto exacto de sprites usados por la acción;
- gráficos no referenciados;
- issues/warnings;
- `mir2_to_zircon_direction_shift = 3`;
- semántica visual y semántica de servidor separadas.

## Dirección Mir2 -> Zircon

La política es preservar físicamente los índices originales. No gira ni renumera los sprites.

El perfil generado indica:

```text
Mir2DirMap.Shift = 3
```

Cursor debe aplicar esa transformación en el registro/renderer específico. Así no se destruyen índices ni FrameSets raros.

## Casos AUTO / REVIEW

La herramienta no falsea conversiones.

Si puede demostrar las imágenes pero no tiene un FrameSet verificado, marca:

```text
REVIEW_FRAMESET_UNKNOWN
```

Para las 650 Hispa ya analizadas, usa `--analysis-root` o `--manifest`. De esa manera reutiliza los perfiles ya obtenidos y no vuelve a inferirlos.

Si una HPR no encaja con el formato verificable, se añade a `FAILURES.json` y el lote continúa con las demás.

## MasterSheet

`MASTER_SHEET.csv/json/html` incluye por monstruo:

- HPR ID;
- versión;
- layout de imagen detectado;
- slots totales;
- imágenes presentes;
- estado AUTO/REVIEW;
- origen del FrameSet;
- acciones;
- acciones cuyo comportamiento de servidor sigue siendo desconocido;
- gráficos no referenciados;
- `.Zl` generada;
- issues;
- warnings.

El HTML incluye filtro por ID, acción, estado o error.

## Integración con Cursor

Después de generar el lote, el flujo queda así:

> Coge `MONSTERS/1829` y mételo en Mon8 slot 6.

Cursor debe leer primero `CURSOR_IMPORT_THIS_MONSTER.md`, `CURSOR_PROFILE.json` y `FRAMESET.cs.txt`. El destino Mon/slot lo decide el usuario; la herramienta no lo inventa.

## Comandos

Inspeccionar una sola HPR:

```bat
py origins_hpr_zircon_v2.py inspect 1829.hpr --manifest ALL_MONSTERS_CURSOR_MANIFEST.json
```

Procesar carpeta completa:

```bat
py origins_hpr_zircon_v2.py batch D:\HISPA_HPR --out D:\HISPA_ZIRCON_READY
```

Guardar también PNGs:

```bat
py origins_hpr_zircon_v2.py batch D:\HISPA_HPR --out D:\HISPA_ZIRCON_READY --export-png
```

Solo analizar, sin escribir `.Zl`:

```bat
py origins_hpr_zircon_v2.py batch D:\HISPA_HPR --out D:\HISPA_ANALYSIS_ONLY --no-zl
```

## Escritor ZL2

El escritor genera el mismo contenedor que entiende `TOOLS/zl_extractor/zl_extract.py` de Origins:

- firma `ZL2`;
- versión 2;
- IDs de slot preservados;
- codec interno PNG;
- entry sin compresión adicional;
- metadata X/Y preservada;
- validación de offsets, índice y firma PNG después de escribir.

Esto evita volver a DXT/BC7 durante la conversión. Más adelante Zircon/LibraryEditor puede recomprimir si interesa.

## Autotests

```bat
py selftest.py
py selftest_real_v3.py
```

`selftest_real_v3.py` crea una biblioteca con la misma arquitectura de cabecera/tabla de offsets/FrameSet-tail verificada en Hispa v3, la lee, genera ZL2 y vuelve a validar el contenedor.

GitHub Actions ejecuta ambos tests en cada cambio de esta herramienta.
