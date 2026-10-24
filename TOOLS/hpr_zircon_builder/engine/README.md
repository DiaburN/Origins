# HPR ENGINE

Coloca aquí el lector probado:

`monster_hpr_analyzer.py`

Debe ser el mismo backend de `MonsterHPR_Crystal_Analyzer_ForCursor_v3` / `ORIGINS_Monster_Preparer_ONE_CLICK_v4` que ya se validó con las librerías HispaCrystal.

El builder principal NO vuelve a adivinar el binario HPR: reutiliza este parser validado y se encarga de normalizar su salida, construir el MASTER SHEET, generar FrameSets y empaquetar `.Zl`.

Si lo guardas en otra ruta, usa:

```bat
py origins_hpr_zircon_builder.py analyze --hpr-root "D:\HPR" --output "D:\ANALYSIS" --engine "D:\TOOLS\monster_hpr_analyzer.py"
```

Si la CLI concreta de esa versión del backend difiere, se puede indicar literalmente:

```bat
py origins_hpr_zircon_builder.py analyze --hpr-root "D:\HPR" --output "D:\ANALYSIS" --engine "D:\TOOLS\monster_hpr_analyzer.py" --engine-command "{python} {engine} --input {input} --output {output}"
```

No se debe sustituir este parser por heurísticas visuales: FrameSet, índices, X/Y y bloques no referenciados deben salir del HPR real.
