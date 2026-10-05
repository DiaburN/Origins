# ORIGINS HPR -> ZIRCON MASTER BUILDER

Herramienta para convertir el trabajo de análisis HispaCrystal HPR en paquetes de monstruo utilizables por Zircon y generar un **MASTER SHEET** global.

## Objetivo

Flujo:

`HPR -> analisis probado -> frames RGBA -> metadata -> FrameSet -> .Zl -> ficha Cursor -> MASTER_SHEET`

La herramienta NO decide AI, daño, heal ni proyectiles a partir del nombre visual de una acción.

## Reglas que nunca se deben romper

1. `Attack*`, `AttackRange*`, `Spell*` y `Special*` son nombres **visuales** del HPR. No prueban comportamiento de servidor.
2. `Frame.OffSet` de Zircon = `direction_stride` del perfil HPR.
3. No modificar `FrameSet.DefaultMonster` para encajar criaturas custom.
4. Preservar índices originales de imagen siempre que sea posible.
5. Si se compactan índices, hay que crear `sourceIndex -> targetIndex` y reescribir todos los StartIndex. Este builder, por defecto, **NO compacta**.
6. Preservar `X/Y` de cada imagen.
7. Los frames no referenciados por FrameSet quedan marcados como `UNREFERENCED` / posibles efectos; nunca se asignan automáticamente.
8. Las criaturas con status REVIEW/SPECIAL siguen pudiendo exportarse visualmente, pero el paquete queda marcado para revisión.

## Backend HPR

Este proyecto usa como backend el analizador ya probado de ORIGINS (`monster_hpr_analyzer.py`) porque ese lector ya fue validado sobre 650 HPR HispaCrystal.

Colócalo en:

`TOOLS/hpr_zircon_builder/engine/monster_hpr_analyzer.py`

También funciona apuntando a un análisis ya generado con `--analysis-root`.

## Uso rápido

### 1. Instalar

```bat
py -m pip install -r requirements.txt
```

### 2. Generar MASTER SHEET desde un análisis existente

```bat
py origins_hpr_zircon_builder.py master --analysis-root "D:\HISPA_ANALYSIS" --output "D:\HISPA_MASTER"
```

Genera:

- `MASTER_SHEET.csv`
- `MASTER_SHEET.json`
- `MASTER_SHEET.html`
- `READY_IDS.txt`
- `REVIEW_IDS.txt`
- una ficha `MONSTERS/<id>/CURSOR_IMPORT_THIS_MONSTER.md` por monstruo.

### 3. Construir una .Zl de un monstruo

Si la carpeta del monstruo ya tiene `IMAGE_METADATA.csv`, `CURSOR_PROFILE.json` y frames PNG:

```bat
py origins_hpr_zircon_builder.py build --monster-root "D:\HISPA_MASTER\MONSTERS\1829" --output "D:\BUILT"
```

Salida:

- `1829.Zl`
- `1829.frameset.json`
- `1829.frameset.cs.txt`
- `CURSOR_IMPORT_THIS_MONSTER.md`
- `VALIDATION_BUILD.txt`

La `.Zl` se escribe en el formato legacy DXT1 que el lector de Zircon del propio repositorio ya reconoce. Los slots vacíos se conservan y los IDs de frame no se renumeran.

## Estructura esperada por monstruo

```text
MONSTERS/1829/
  CURSOR_PROFILE.json
  PROFILE_SOURCE.json              (opcional)
  IMAGE_METADATA.csv
  FRAMES_PNG/
    000000.png
    000001.png
    ...
  VALIDATION.txt                   (opcional)
```

El builder acepta también nombres PNG con 5 o 6 dígitos y busca el índice numérico en el nombre.

## MASTER SHEET

Cada fila incluye al menos:

- HPR ID
- status
- slot_count
- nonempty_image_count
- action_count
- acciones visuales
- start/count/stride/delay/reverse por acción
- índices/rangos no referenciados
- issues/warnings
- `needs_review`
- `build_ready`
- ruta de la ficha Cursor

## Sobre `.Zl`

El writer incluido genera **ZL legacy DXT1** preservando índices y offsets. El extractor existente de este repositorio (`TOOLS/zl_extractor/zl_extract.py`) reconoce tanto ZL legacy como ZL2, por lo que puede usarse inmediatamente para validar una librería construida:

```bat
py ..\zl_extractor\zl_extract.py BUILT\1829.Zl --extracted-root CHECK
```

El objetivo inicial es fidelidad y compatibilidad, no recomprimir al formato más nuevo. Si luego interesa ZL2/BC7, se puede añadir otro writer sin tocar el análisis ni el mastersheet.

## Importante para Cursor

La ficha generada por monstruo es deliberadamente explícita: Cursor debe tratar el paquete como **visual/client-side** hasta que se asigne por separado Race/AI/stats en el servidor.
