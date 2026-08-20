# ORIGINS-DxR — cierre del núcleo Zircon

Estado consolidado del núcleo antes de empezar Items/Equipment/Balance y el resto de contenido ORIGINS.

## Autoridad fijada

- Rama activa: `Origins-DxR`
- Zircon source of truth: `cbf1aa919083bc13fc3f23f93772a8ab8370632d`
- Clases activas: Warrior, Wizard, Taoist, Assassin
- Archer: fuera
- Monk: fuera
- Crystal / Crystal-Monk: fuera del runtime activo
- UI cerrada: `apps/zircon-ui-reference/`
- Snapshot DB canónica: `database/generated/zircon-system/`

## FASE 1 — ARRANQUE REAL

**Estado: PASS con GitHub Actions.**

Evidencia canónica: `docs/generated/ORIGINS_DXR_CORE_BOOTSTRAP_STATUS.md`.

Validado:

- bootstrap del Zircon fijado;
- `LibraryCore` compila;
- `ServerLibrary` compila;
- servidor compila;
- cliente compila;
- Warrior/Wizard/Taoist/Assassin están cableados en selección;
- no hay dependencias Crystal activas en build/bootstrap;
- herramientas ORIGINS DB compilan;
- `System.db` se regenera desde la snapshot canónica;
- `System.db` se verifica;
- round-trip de `MagicInfo` compatible con el modelo fijado;
- preflight de entrypoints/configuración servidor + cliente.

Último `System.db` validado por el gate: **5,751,925 bytes**.

### Fallos reales encontrados y corregidos

1. **Colisión Windows `database/` vs `Database/`.**  El primer gate borraba accidentalmente la snapshot canónica porque Windows no distingue mayúsculas/minúsculas. Se corrigió el CI para no usar la carpeta runtime del servidor sobre la raíz del repositorio.
2. **`MagicInfo.LevelDelayReduction` no existe en el Zircon fijado.** La snapshot exportada incluía el campo, pero las 174 filas tenían valor `0`. Se añadió un normalizador fail-closed: solo podía retirar el campo si todos los valores eran cero; cualquier valor no cero habría abortado. La condición se cumplió y la snapshot quedó alineada con el `MagicInfo` real de `cbf1aa...` sin portar ni inventar comportamiento.

## FASE 2 — AUDITORÍA FINAL DE MAGIAS

**Estado: PASS.**

Evidencia canónica: `docs/generated/ORIGINS_DXR_MAGIC_AUDIT.md` y `database/magic/generated/zircon-four-class-runtime-audit.json`.

| Clase | Enum | MagicInfo | Handlers | Jugables | Enum-only | DB sin handler | Handler sin DB | NOT CODED | UNUSED |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Warrior | 38 | 32 | 37 | 32 | 0 | 0 | 5 | 1 | 0 |
| Wizard | 47 | 42 | 46 | 40 | 0 | 0 | 4 | 3 | 0 |
| Taoist | 52 | 47 | 51 | 47 | 0 | 0 | 4 | 1 | 0 |
| Assassin | 58 | 53 | 56 | 52 | 0 | 0 | 4 | 1 | 1 |
| **TOTAL** | **195** | **174** | **190** | **171** | **0** | **0** | **17** | **6** | **1** |

Una magia se cuenta como jugable únicamente cuando tiene enum nativo definido + una fila `MagicInfo` real + un handler registrado real. No se rellenó ningún hueco.

`LevelDelayReduction`: **N/A en este Zircon fijado**, porque la propiedad no forma parte de `MagicInfo` en `cbf1aa...`.

## FASE 3 — MAGICDIALOG + MAGICBAR

**Estado: PASS.**

Evidencia canónica: `docs/generated/ORIGINS_DXR_MAGIC_UI_STATUS.md`.

Validado contra cliente Zircon fijado:

- filtro por clase y `MagicSchool`;
- pestañas dinámicas;
- scroll;
- `MagicInfo.Icon` / nombre;
- aprendido/no aprendido;
- niveles y experiencia;
- `ItemRequired`;
- `SpellSet` 1..4;
- `Spell01`..`Spell24`;
- actualización de iconos;
- desasignación de teclas duplicadas en los cuatro sets;
- `C.MagicKey` queda en cliente Zircon;
- cooldown queda en `NextCast` / `ToggleTime` de Zircon.

El runtime HTML de referencia ORIGINS queda explícitamente como **presentación**. El gate falla si intenta escribir `Set1Key..Set4Key`, modificar cooldowns o enviar paquetes de gameplay.

## FASE 4 — PERSONAJE 100% ZIRCON

**Estado: PASS.**

Evidencia canónica: `docs/generated/ORIGINS_DXR_PLAYER_RUNTIME_STATUS.md`.

Validado:

- `FrameSet.Players` como fuente de frames;
- Standing;
- Walking (`MirAction.Moving`);
- Running (`MirAction.Moving`, distancia >= 2);
- Pushed;
- Attack mediante `Functions.GetAttackAnimation`;
- RangeAttack;
- Spell mediante `Functions.GetMagicAnimation`;
- Harvest;
- Struck;
- Die;
- Dead;
- Fishing;
- Taming;
- Body;
- Hair;
- Helmet;
- Weapon1 / Weapon2;
- Shield;
- Horse;
- las ocho direcciones;
- layering de armas/escudo/cuerpo/casco/pelo/caballo;
- `FrameIndexChanged()`;
- efectos/proyectiles ligados a frames nativos, incluidos SeismicSlam, CrushingWave, OffensiveBlow, Taming y Fishing;
- autoridad servidor `C.Move -> Player.Move`, `C.Mount -> Player.Mount`, `C.Attack -> Player.Attack`, `C.RangeAttack -> Player.RangeAttack`, `C.Magic -> Player.Magic`.

No se inventan animaciones para huecos del propio Zircon:

- `Show`: existe en `MirAction`, sin mapping directo en `PlayerObject.SetAnimation()`;
- `Hide`: igual;
- `Idle`: sin mapping directo; el flujo normal vuelve a Standing cuando no hay acción en cola;
- `Mount`: estado, no animación directa; `Horse` determina HorseStanding/HorseWalking/HorseRunning/HorseStruck.

### Falso fallo de auditoría corregido

El primer auditor esperaba un método servidor `PlayerObject.Walk()`. El Zircon fijado usa el pipeline real `C.Move -> Player.Move`. Se corrigió únicamente el auditor; no se modificó runtime Zircon.

## Integridad después del PASS de compilación

Desde el HEAD probado por el gate de Fase 1 hasta el cierre de Fase 4, los cambios de ORIGINS-DxR son auditorías, workflows, informes y salidas de auditoría. **No se ha parcheado el runtime Zircon fijado.**

## Qué falta para entrar visualmente con un personaje

Esto es distinto de compilar el núcleo. El runner de Actions no demuestra una sesión GUI jugada.

### Servidor — staging separado

Zircon espera, relativo al directorio de ejecución:

- `Database/System.db` — debe ser el `System.db` regenerado y validado;
- `Database/Users.db` — puede crearse nuevo, pero la carpeta debe ser escribible;
- `Map/` — mapas requeridos por la DB;
- `Server.ini`;
- ejecutable + dependencias del build servidor.

Para poder pulsar Start Game, `Server.ini` debe contener como mínimo:

```ini
[Control]
AllowStartGame=True
```

El valor nativo por defecto de `AllowStartGame` es `false` porque la propiedad no tiene inicializador.

El Zircon fijado además tiene `CheckVersion=True` por defecto. Su `VersionPath` por defecto es `.\Zircon.dll`; debe existir un binario cliente compatible para que el hash del cliente y el servidor coincidan. No se desactiva esta comprobación en ORIGINS-DxR.

### Cliente — staging separado

El cliente abre su DB en `Data/`, no en la carpeta DB del servidor:

- `Data/System.db` — misma versión/snapshot de sistema que usa el servidor;
- `Data/Users.db` — estado local del cliente; puede generarse;
- `Data/*.Zl` requeridos por `Libraries.LibraryList` (`GameInter`, cuerpos, pelo, armas, escudos, iconos, magias, etc.);
- `Map/`;
- `Zircon.ini` si se quieren sobrescribir defaults;
- ejecutable + dependencias del build cliente.

Para una prueba local, el cliente ya tiene por defecto `127.0.0.1:7000`.

### Bloqueo actual de la prueba visual

El repositorio ORIGINS-DxR contiene la reconstrucción UI y la base de datos canónica, pero no contiene el payload completo de librerías nativas `Data/*.Zl` y mapas necesario para renderizar/jugar el cliente Zircon completo. Por tanto:

- **núcleo de código/DB: cerrado**;
- **login GUI hasta mundo jugable: todavía no demostrado**;
- bloqueo: staging del payload runtime cliente/mapas + configuración `AllowStartGame=True`, no lógica Crystal ni una carencia detectada de compilación.

El staging de servidor y cliente debe hacerse fuera de la raíz del repositorio para evitar la colisión Windows entre la fuente `database/` y la carpeta runtime Zircon `Database/`.

## Siguiente bloque autorizado por el orden maestro

Con Fases 1–4 cerradas, el siguiente bloque es **Items**, seguido de Equipment, Sets, Stats/balance, Monsters, Drops, Respawns, NPCs, Stores, Maps, dungeons Archero, Quests y progresión ORIGINS.
