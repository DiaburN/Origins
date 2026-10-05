# ORIGINS HPR -> ZIRCON MASTER BUILDER

Herramienta para convertir librerías **HispaCrystal `.hpr`** en paquetes de monstruo utilizables por Zircon y generar un **MASTER SHEET** global.

## Flujo

`HPR -> lector HispaCrystal v3 integrado -> frames RGBA -> metadata X/Y -> perfil visual -> .Zl -> ficha Cursor -> MASTER_SHEET`

La herramienta NO decide AI, daño, heal ni proyectiles a partir del nombre visual de una acción.

## Reglas que nunca se deben romper

1. `Attack*`, `AttackRange*`, `Spell*` y `Special*` son nombres **visuales** del HPR. No prueban comportamiento de servidor.
2. `Frame.OffSet` de Zircon = `direction_stride` del perfil HPR.
3. No modificar `FrameSet.DefaultMonster` para encajar criaturas custom.
4. Preservar índices originales de imagen siempre que sea posible.
5. Este builder, por defecto, **NO compacta** índices.
6. Preservar `X/Y` de cada imagen.
7. Los frames no referenciados quedan marcados para revisión; nunca se asignan automáticamente.
8. Las criaturas REVIEW/SPECIAL siguen pudiendo exportarse visualmente, pero deben revisarse antes de mapear comportamiento de servidor.

## Lector HPR integrado

Ya no hay que copiar un `monster_hpr_analyzer.py` externo.

El proyecto incluye:

- `origins_hpr_zircon.py`: núcleo HispaCrystal + exportador.
- `origins_hpr_zircon_v2.py`: lector **real v3** con tabla de offsets.
- `engine/monster_hpr_analyzer.py`: adaptador usado automáticamente por `analyze`.
- `selftest_real_v3.py`: prueba estructural del formato v3.

El lector v3 fue construido a partir de la estructura verificada en las librerías reales Hispa `000.hpr` y `001.hpr` del proyecto. Los slots se toman de la tabla de offsets y no se renumeran.

## Uso recomendado en Windows

Ejecuta:

```bat
START.bat
```

Opciones principales:

- **[3] Analizar HPR**: selecciona un `.hpr`, una carpeta de `.hpr` o un ZIP. Genera frames PNG, `IMAGE_METADATA.csv`, `CURSOR_PROFILE.json` y validaciones.
- **[4] HPR -> ANALISIS + MASTER**: hace el catálogo completo en un paso. Si tienes `ALL_MONSTERS_CURSOR_MANIFEST.json`, indícalo para reutilizar los FrameSet ya analizados de la colección de 650 HPR.
- **[2] Construir .Zl**: cuando elijas un monstruo concreto, construye su `.Zl` preservando índices y offsets.

## CLI

### Analizar HPR directamente

```bat
py origins_hpr_zircon_builder.py analyze --hpr-root "D:\HISPA_HPR" --output "D:\HISPA_ANALYSIS"
```

El backend está integrado; no necesitas `--engine`.

### Crear MASTER SHEET desde el análisis

Sin manifiesto:

```bat
py origins_hpr_zircon_builder.py master --analysis-root "D:\HISPA_ANALYSIS" --output "D:\HISPA_MASTER"
```

Con el manifiesto de los 650 HPR, recomendado:

```bat
py origins_hpr_zircon_builder.py master --analysis-root "D:\HISPA_ANALYSIS" --manifest "D:\ALL_MONSTERS_CURSOR_MANIFEST.json" --output "D:\HISPA_MASTER"
```

Genera:

- `MASTER_SHEET.csv`
- `MASTER_SHEET.json`
- `MASTER_SHEET.html`
- `READY_IDS.txt`
- `REVIEW_IDS.txt`
- `MONSTERS/<id>/FRAMESET.json`
- `MONSTERS/<id>/FRAMESET.cs.txt`
- `MONSTERS/<id>/CURSOR_IMPORT_THIS_MONSTER.md`

### Construir una `.Zl` de un monstruo

```bat
py origins_hpr_zircon_builder.py build --monster-root "D:\HISPA_ANALYSIS\MONSTERS\1829" --output "D:\BUILT"
```

Salida:

- `1829.Zl`
- `1829.frameset.json`
- `1829.frameset.cs.txt`
- `CURSOR_IMPORT_THIS_MONSTER.md`
- `VALIDATION_BUILD.txt`

La `.Zl` conserva los slots originales y los offsets `X/Y` recuperados del HPR.

## Estructura preparada por monstruo

```text
MONSTERS/1829/
  CURSOR_PROFILE.json
  IMAGE_METADATA.csv
  FRAMES_PNG/
    000000.png
    000001.png
    ...
  FRAMESET.cs.txt
  CURSOR_IMPORT_THIS_MONSTER.md
  VALIDATION.txt
```

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

## Tests

GitHub Actions comprueba automáticamente:

1. writer `.Zl` y lectura inversa;
2. lector HispaCrystal v3;
3. HPR v3 -> análisis -> PNG/metadata -> MASTER;
4. análisis preparado -> `.Zl` -> lectura inversa conservando slots y `X/Y`.

## Importante para Cursor

La ficha generada por monstruo describe **solo el visual/client-side**. Race, AI, stats, rango, proyectil, heal y comportamiento de combate se asignan por separado en servidor.

Ejemplo de uso posterior:

`mete el HPR 034 en Mon8 slot6`

Cursor debe leer la ficha del `034`, usar sus índices/FrameSet y registrar el monstruo sin alterar `FrameSet.DefaultMonster` ni deducir AI por el nombre de las animaciones.
