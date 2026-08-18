# ORIGINS MOBILE — Magic Dialog V1

## Estado

Esta fase deja cerrado el contrato de integración de magias para ORIGINS MOBILE con esta jerarquía:

- **Shell/UI:** `Suprcode/Zircon` → `Client/Scenes/Views/MagicDialog.cs`
- **Warrior / Wizard / Taoist / Assassin / Archer:** `Suprcode/Crystal`
- **Monk:** `JevLOMCN/Crystal-Monk`
- **Catálogo machine-readable:** `data/magic/crystal_magic_manifest.json`
- **QA:** `tools/verify_magic_manifest.py`

No se crea un árbol RPG nuevo ni categorías ficticias.

> Importante: en el repositorio ORIGINS actual no existe todavía la reconstrucción source-faithful del `MagicDialog` de Zircon ni un runtime/UI framework al que conectarla. Por eso esta entrega no introduce un panel alternativo ni un mock visual: deja el catálogo completo, el binding real y el contrato exacto para conectar la UI cuando esa base esté presente.

## 1. Shell Zircon que se debe preservar

Referencia: `Suprcode/Zircon/Client/Scenes/Views/MagicDialog.cs`.

Geometría y comportamiento relevantes del source:

- `MagicDialog`: 419 × 511.
- `DXTabControl`: 420 × 448, posición `(0, 40)`.
- Fondo de contenido: `LibraryFile.Interface`, índice `164`, posición `(0, 66)`.
- `MagicCell`: 369 × 54.
- Fondo de celda: `LibraryFile.Interface`, índice `165`.
- Icono dentro de la celda: posición `(9, 9)`.
- Scroll vertical real con assets Interface `60/61/62`.
- Zircon ordena su catálogo por requisito de nivel antes de crear celdas.
- La celda tiene soporte nativo para nombre, nivel actual, experiencia/progreso y keybind.

No deben redibujarse estos componentes si ya existe la reconstrucción aprobada.

## 2. Selector de clase ORIGINS

Se usarán **6 tabs de primer nivel**, todos dentro del lenguaje de Zircon:

1. Warrior
2. Wizard
3. Taoist
4. Assassin
5. Archer
6. Monk

Los nombres serán texto dinámico/localizable. No se queman nombres de clase dentro de PNG.

### Por qué no hay subárboles inventados

Crystal no define una taxonomía equivalente al `MagicSchool` de Zircon para estas magias. Por tanto, ORIGINS V1 usa una lista plana por clase.

No se asignan arbitrariamente categorías como Fire/Ice/Support/Passive si no existe una fuente inequívoca. Si más adelante se incorpora una clasificación fuente-real, podrá añadirse como segundo nivel sin cambiar el catálogo base.

## 3. Celdas

Cada celda reutiliza el lenguaje de `MagicCell` de Zircon y recibe estos datos estáticos del manifest:

- `spell`
- `spellId`
- `iconId`
- `requiredLevels`

El formato compacto de cada registro es:

`[spell, spellId, iconId, requiredLevels]`

### Datos runtime

Nunca se rellenan con valores de ejemplo:

- nivel actual de la magia
- experiencia actual
- tecla / keybind
- cooldown
- estado de desbloqueo del jugador

Esos campos se muestran únicamente cuando exista binding con datos reales del jugador. Sin runtime deben quedar vacíos/neutros y conservar la geometría.

## 4. Iconos

Crystal/Crystal-Monk separan el ID lógico del icono de los frames de la librería cliente.

Binding confirmado en source:

- librería: `MagIcon2`
- asset lógico: `Settings.DataPath + "MagIcon2"`
- frame normal: `iconId * 2`
- frame pulsado: `iconId * 2 + 1`

El manifest documenta para cada skill el `iconId`. La fuente y la librería se resuelven por clase/globalmente, y los frames se calculan de forma determinista.

### Estado del asset gráfico

En las fuentes accesibles auditadas se ha podido cerrar la librería y los índices verificables, pero **no se ha podido recuperar el asset cliente `MagIcon2` con los píxeles finales de los iconos**. No se ha generado ningún icono sustituto.

En cuanto el asset real `MagIcon2` esté disponible dentro del repositorio o del pack cliente, la extracción puede hacerse de forma determinista con los índices ya cerrados.

## 5. Hallazgos de source que no deben ocultarse

### Wizard.FastMove

`Spell.FastMove = 54` existe en el enum de Crystal, pero su alta en `FillMagicInfoList()` está comentada y contiene `Icon = ?` y demás valores desconocidos.

Decisión ORIGINS:
- La magia sí se lista porque existe en el source y forma parte del alcance.
- `iconId` y requisitos desconocidos quedan `null`.
- No se asigna icono prestado ni nivel inventado.

### Archer.Stonetrap

Crystal define:

- `Icon = 97`
- `Level1/2/3 = 40/43/46`
- `Need1/2/3 = 4900/9800/141`

`Need3 = 141` es anómalo respecto a los valores vecinos, pero se conserva como hallazgo de source. No se corrige por intuición.

### Monk

El fork `Crystal-Monk` reutiliza explícitamente:
- `Icon = 42` en JiBenGunFa, LuoHanGunFa, JinGangGunFa, DaMoGunFa, XiangLongGunFa, Taunt y TianLeiZhen.
- `Icon = 23` en LuoHanZhen y ShiBuYiSha.

Esta repetición viene del fork y no es un placeholder añadido por ORIGINS.

## 6. Conteo cerrado

| Clase | Magias |
|---|---:|
| Warrior | 17 |
| Wizard | 25 |
| Taoist | 25 |
| Assassin | 17 |
| Archer | 21 |
| Monk | 9 |
| **Total** | **114** |

## 7. Orden de render

V1 conserva el orden del alcance definido para ORIGINS dentro de cada clase, manteniendo siempre los `spellId`, `iconId` y requisitos tomados del source. No se usa el orden para reinterpretar IDs ni para inventar categorías.

Si posteriormente se decide ordenar visualmente por nivel requerido, el cambio debe hacerse en presentación, sin alterar IDs ni mappings.

## 8. Integración cuando el MagicDialog aprobado esté presente

1. Mantener el shell/PNG/medidas existentes.
2. Sustituir la fuente de datos de las celdas por `crystal_magic_manifest.json`.
3. Añadir el selector de 6 clases.
4. Filtrar las magias por clase.
5. Crear una `MagicCell` por entrada.
6. Resolver icono mediante `MagIcon2` y `iconId * 2`.
7. Bindear nivel actual, EXP, keybind y cooldown solo desde runtime.
8. Mantener scroll vertical real.
9. No crear placeholders para FastMove.
10. Ejecutar `tools/verify_magic_manifest.py`.

## 9. Criterios QA V1

El verificador exige:

- exactamente 6 clases;
- conteos 17/25/25/17/21/9;
- exactamente 114 magias;
- IDs de spell únicos;
- nombres únicos dentro de cada clase;
- mapping de frames `iconId*2` / `iconId*2+1` como contrato de cliente;
- solo FastMove puede carecer de icono en el catálogo actual;
- ningún campo runtime falso dentro del manifest.

## 10. Pendiente real

Quedan dos dependencias externas a este commit:

1. **Conectar el catálogo al MagicDialog source-faithful** cuando esa reconstrucción esté añadida al repositorio ORIGINS.
2. **Añadir/extractar el asset cliente real `MagIcon2`** para disponer de los píxeles finales de los 113 mappings verificables.

No hay ningún otro placeholder visual introducido por esta fase.
