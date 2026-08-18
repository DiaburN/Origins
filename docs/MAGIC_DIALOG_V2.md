# ORIGINS MOBILE — MagicDialog V2

## Objetivo cerrado

Esta fase integra el contenido de magias de Crystal dentro del lenguaje visual del `MagicDialog` de Zircon, sin crear un panel alternativo y sin inventar datos runtime.

### Fuentes fijadas

- Zircon UI: `Suprcode/Zircon` commit `cbf1aa919083bc13fc3f23f93772a8ab8370632d`
- Crystal: `Suprcode/Crystal` commit `0e315fe327192afe52c3d7357ddd1f5b7e26c5b8`
- Monk: `JevLOMCN/Crystal-Monk` commit `381e589e3d7ee736cdf0583c8315c0d144ab058f`
- Artwork Zircon: mirror público LOMCN/MirFiles, `Interface.Zl`
- Iconos Crystal: mirror público LOMCN/MirFiles, `MagIcon2.Lib`

El build no depende de assets inventados ni de un ZIP manual del usuario.

## Arquitectura

`apps/origins-magic-dialog-reference/` renderiza:

1. Shell `DXWindow` de Zircon.
2. `MagicDialog` 419×511.
3. Cuerpo `Interface #164` en `(0,66)`.
4. Selector de seis clases usando piezas reales de tabs genéricas Zircon:
   - deselected: `#53/#55/#54`
   - selected: `#56/#58/#57`
5. Lista vertical de `MagicCell` de 369×54 con fondo `Interface #165`.
6. Scroll visual/funcional con `#60/#61/#62`.
7. Iconos reales extraídos de `Crystal MagIcon2.Lib`.

No se crea un árbol de escuelas artificial.

## Clases y conteo

| Clase | Magias |
|---|---:|
| Warrior | 17 |
| Wizard | 25 |
| Taoist | 25 |
| Assassin | 17 |
| Archer | 21 |
| Monk | 9 |
| **Total** | **114** |

El catálogo se genera en cada build directamente desde los sources fijados. No se mantiene a mano un segundo catálogo que pueda desincronizarse.

## Mapping de iconos

Crystal usa `MagIcon2.Lib` para el botón de skill:

- normal = `Icon * 2`
- pressed = `Icon * 2 + 1`

`extract_magicon2.py` abre el formato `.Lib` real de Crystal, descomprime los frames GZip BGRA y genera PNG RGBA sin redibujar nada.

El QA exige que cada magia implementada tenga los dos frames físicos extraídos.

## Headers de clase

Zircon tiene headers específicos de MagicDialog únicamente para:

- Warrior → `Interface #160`
- Wizard → `#161`
- Taoist → `#162`
- Assassin → `#163`

No existe un header Zircon equivalente verificado para Archer o Monk. Por ello V2 no reutiliza un header de otra clase ni dibuja uno falso. Archer/Monk usan el mismo shell y selector de clase, con nombre dinámico en texto.

## Runtime

El catálogo estático prohíbe estos campos:

- nivel actual de magia
- experiencia actual
- keybind
- cooldown
- estado de desbloqueo del jugador

La geometría reserva sitio para ellos, pero solo podrán aparecer cuando ORIGINS proporcione estado real del jugador.

## FastMove — resolución definitiva del hallazgo

`Spell.FastMove = 54` existe en Crystal.

Sin embargo:

- el `FillMagicInfoList()` de `Suprcode/Crystal` deja su línea comentada con `Icon = ?`, niveles `?`, costes `?`;
- un fork histórico de Crystal (`cjlaaa/mir2`) conserva exactamente la misma línea incompleta;
- no se ha encontrado un `MagicInfo` oficial verificable que permita asignar icono/niveles sin inventar.

Por ello **FastMove se integra en la lista**, pero se marca `sourceImplemented=false` y no recibe icono prestado. Esto es una carencia upstream demostrable, no un placeholder ORIGINS.

Si aparece una fuente Crystal auténtica que complete ese `MagicInfo`, el generador podrá incorporarla de forma explícita y el QA obligará a extraer su icono real.

## Monk

Las repeticiones de icono del fork se conservan exactamente:

- iconId 42: JiBenGunFa, LuoHanGunFa, JinGangGunFa, DaMoGunFa, XiangLongGunFa, Taunt, TianLeiZhen.
- iconId 23: LuoHanZhen, ShiBuYiSha.

No se sustituyen por iconos distintos por estética.

## Pipeline

Workflow: `.github/workflows/build-origins-magic-dialog.yml`

1. Descarga `Interface.Zl` real de Zircon.
2. Descarga `MagIcon2.Lib` real de Crystal.
3. Descarga source fijado de Crystal, Crystal-Monk y MagicDialog Zircon.
4. Genera catálogo de 114 magias desde source.
5. Valida conteos e IDs.
6. Extrae los assets Zircon requeridos.
7. Extrae todos los frames Crystal requeridos.
8. Valida que no falta ningún icono source-backed.
9. Monta la referencia navegable.
10. Publica artifact `origins-magic-dialog-reference`.

## Archivos V2

- `tools/crystal-magic-importer/build_magic_catalog.py`
- `tools/crystal-magic-importer/extract_magicon2.py`
- `tools/crystal-magic-importer/verify_magic_catalog.py`
- `apps/origins-magic-dialog-reference/index.html`
- `apps/origins-magic-dialog-reference/magic-dialog.css`
- `apps/origins-magic-dialog-reference/magic-dialog.js`
- `.github/workflows/build-origins-magic-dialog.yml`
- `docs/MAGIC_DIALOG_V2.md`

## Criterio de cierre

V2 solo pasa si:

- hay exactamente 6 clases y 114 spells;
- los IDs son únicos;
- todas las magias implementadas tienen iconId real;
- los dos frames de cada icono existen físicamente tras extracción;
- `Wizard.FastMove` es la única entrada source-incomplete;
- no existe runtime falso en el catálogo;
- shell, cuerpo, celda, tabs y scroll usan índices reales de Zircon.
