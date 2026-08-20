# ORIGINS Web Runtime

Este directorio es el cliente web jugable incremental de ORIGINS. No sustituye ni modifica la reconstrucción cerrada de UI en `apps/zircon-ui-reference/`.

## Step 1 — runtime mínimo

Estado implementado:

- bucle fijo de simulación a 60 Hz;
- `MirDirection` 0..7 copiado del Zircon fijado;
- `MirAction` 0..16 copiado del Zircon fijado;
- input de teclado WASD/flechas;
- input táctil de ocho direcciones;
- cámara siguiendo al jugador;
- `PreviewPlayerObject` con transición `Standing <-> Moving`;
- previsualización Canvas responsive;
- pruebas unitarias sin dependencias externas.

La representación PLAYER de Step 1 es deliberadamente diagnóstica. No es un sprite del juego y no debe convertirse en asset final.

## Autoridad

Fuente funcional fijada:

`Suprcode/Zircon @ cbf1aa919083bc13fc3f23f93772a8ab8370632d`

En este Step 1 el movimiento es **solo previsualización local** para validar el loop, input y renderer. No se presenta como movimiento autoritativo.

El navegador no abre `System.db` ni `Users.db` directamente y no existe todavía transporte WebSocket en este directorio. La futura conexión mantiene al servidor Zircon como autoridad de movimiento, combate, magias, inventario, monstruos y persistencia.

## Siguientes pasos ya delimitados

1. Step 2 — asset pipeline Zircon: frames/atlas/metadatos, sin recolocar offsets a ojo.
2. Step 3 — mapa real y tiles reales.
3. Step 4 — PlayerObject visual Zircon: body/hair/helmet/weapon/shield y animaciones reales.
4. Step 5 — movimiento autoritativo conectado al servidor.

## Ejecutar localmente

Servir la raíz del repositorio con cualquier servidor HTTP estático y abrir:

`/apps/origins-web-runtime/`

Para pruebas de contrato:

```bash
cd apps/origins-web-runtime
npm test
```

No se necesitan dependencias npm para Step 1.
