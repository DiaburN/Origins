import {
  FixedStepRuntime,
  MIR_ACTION_BY_VALUE,
  MIR_DIRECTION_BY_VALUE,
  PreviewPlayerObject,
  RUNTIME_MODE,
  ZIRCON_SOURCE_COMMIT,
} from './runtime-core.js';

const canvas = document.querySelector('#game-canvas');
const ctx = canvas.getContext('2d', { alpha: false });
const actionValue = document.querySelector('#action-value');
const directionValue = document.querySelector('#direction-value');
const positionValue = document.querySelector('#position-value');
const frameValue = document.querySelector('#frame-value');
const runtimeValue = document.querySelector('#runtime-mode-value');
const sourceValue = document.querySelector('#source-value');
const assetValue = document.querySelector('#asset-value');
const serverValue = document.querySelector('#server-value');

const WORLD = Object.freeze({
  width: 64,
  height: 48,
  tile: 48,
});

const player = new PreviewPlayerObject({ x: 32, y: 24 });
const input = { x: 0, y: 0 };
const keyboard = new Set();
const touchDirections = new Map();
const camera = { x: 0, y: 0 };

runtimeValue.textContent = RUNTIME_MODE.PreviewLocal;
sourceValue.textContent = ZIRCON_SOURCE_COMMIT.slice(0, 12);
assetValue.textContent = 'diagnostic marker — asset pipeline pending';
serverValue.textContent = 'disconnected by design (Step 1)';

const keyVectors = new Map([
  ['ArrowUp', [0, -1]], ['KeyW', [0, -1]],
  ['ArrowDown', [0, 1]], ['KeyS', [0, 1]],
  ['ArrowLeft', [-1, 0]], ['KeyA', [-1, 0]],
  ['ArrowRight', [1, 0]], ['KeyD', [1, 0]],
]);

function recomputeInput() {
  let x = 0;
  let y = 0;

  for (const code of keyboard) {
    const vector = keyVectors.get(code);
    if (!vector) continue;
    x += vector[0];
    y += vector[1];
  }

  for (const vector of touchDirections.values()) {
    x += vector[0];
    y += vector[1];
  }

  input.x = Math.max(-1, Math.min(1, x));
  input.y = Math.max(-1, Math.min(1, y));
}

window.addEventListener('keydown', event => {
  if (!keyVectors.has(event.code)) return;
  event.preventDefault();
  keyboard.add(event.code);
  recomputeInput();
});

window.addEventListener('keyup', event => {
  if (!keyVectors.has(event.code)) return;
  keyboard.delete(event.code);
  recomputeInput();
});

window.addEventListener('blur', () => {
  keyboard.clear();
  touchDirections.clear();
  recomputeInput();
});

for (const button of document.querySelectorAll('[data-vector]')) {
  const vector = button.dataset.vector.split(',').map(Number);
  const idForPointer = pointerId => `${button.dataset.vector}:${pointerId}`;

  button.addEventListener('pointerdown', event => {
    event.preventDefault();
    button.setPointerCapture(event.pointerId);
    touchDirections.set(idForPointer(event.pointerId), vector);
    recomputeInput();
  });

  const release = event => {
    touchDirections.delete(idForPointer(event.pointerId));
    recomputeInput();
  };
  button.addEventListener('pointerup', release);
  button.addEventListener('pointercancel', release);
  button.addEventListener('lostpointercapture', release);
}

function resizeCanvas() {
  const rect = canvas.getBoundingClientRect();
  const dpr = Math.min(2, window.devicePixelRatio || 1);
  const width = Math.max(1, Math.floor(rect.width * dpr));
  const height = Math.max(1, Math.floor(rect.height * dpr));
  if (canvas.width !== width || canvas.height !== height) {
    canvas.width = width;
    canvas.height = height;
  }
  return { cssWidth: rect.width, cssHeight: rect.height, dpr };
}

function updateCamera(viewWidth, viewHeight) {
  const worldX = player.x * WORLD.tile;
  const worldY = player.y * WORLD.tile;
  camera.x = worldX - viewWidth / 2;
  camera.y = worldY - viewHeight / 2;

  const maxX = Math.max(0, WORLD.width * WORLD.tile - viewWidth);
  const maxY = Math.max(0, WORLD.height * WORLD.tile - viewHeight);
  camera.x = Math.max(0, Math.min(maxX, camera.x));
  camera.y = Math.max(0, Math.min(maxY, camera.y));
}

function drawGrid(viewWidth, viewHeight) {
  ctx.fillStyle = '#0a0c0d';
  ctx.fillRect(0, 0, viewWidth, viewHeight);

  const startCol = Math.max(0, Math.floor(camera.x / WORLD.tile));
  const endCol = Math.min(WORLD.width, Math.ceil((camera.x + viewWidth) / WORLD.tile) + 1);
  const startRow = Math.max(0, Math.floor(camera.y / WORLD.tile));
  const endRow = Math.min(WORLD.height, Math.ceil((camera.y + viewHeight) / WORLD.tile) + 1);

  for (let row = startRow; row < endRow; row += 1) {
    for (let col = startCol; col < endCol; col += 1) {
      const screenX = col * WORLD.tile - camera.x;
      const screenY = row * WORLD.tile - camera.y;
      ctx.fillStyle = (row + col) % 2 === 0 ? '#151719' : '#121416';
      ctx.fillRect(screenX, screenY, WORLD.tile, WORLD.tile);
      ctx.strokeStyle = '#202326';
      ctx.strokeRect(screenX + 0.5, screenY + 0.5, WORLD.tile - 1, WORLD.tile - 1);
    }
  }
}

function drawWorldBounds(viewWidth, viewHeight) {
  ctx.strokeStyle = '#675126';
  ctx.lineWidth = 2;
  ctx.strokeRect(-camera.x, -camera.y, WORLD.width * WORLD.tile, WORLD.height * WORLD.tile);

  ctx.fillStyle = '#69645b';
  ctx.font = '12px ui-monospace, SFMono-Regular, Menlo, monospace';
  ctx.fillText('Diagnostic world — real Map/tiles enter in Step 3', 14, viewHeight - 18);
}

function directionUnit(direction) {
  switch (direction) {
    case 0: return [0, -1];
    case 1: return [0.707, -0.707];
    case 2: return [1, 0];
    case 3: return [0.707, 0.707];
    case 4: return [0, 1];
    case 5: return [-0.707, 0.707];
    case 6: return [-1, 0];
    case 7: return [-0.707, -0.707];
    default: return [0, 1];
  }
}

function drawDiagnosticPlayer() {
  const x = player.x * WORLD.tile - camera.x;
  const y = player.y * WORLD.tile - camera.y;
  const [dx, dy] = directionUnit(player.direction);

  ctx.save();
  ctx.translate(x, y);

  ctx.fillStyle = 'rgba(0,0,0,0.55)';
  ctx.beginPath();
  ctx.ellipse(0, 12, 18, 7, 0, 0, Math.PI * 2);
  ctx.fill();

  ctx.fillStyle = '#a9853a';
  ctx.strokeStyle = '#f0d07d';
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.arc(0, -4, 14, 0, Math.PI * 2);
  ctx.fill();
  ctx.stroke();

  ctx.strokeStyle = '#f6efda';
  ctx.lineWidth = 3;
  ctx.beginPath();
  ctx.moveTo(dx * 12, dy * 12 - 4);
  ctx.lineTo(dx * 25, dy * 25 - 4);
  ctx.stroke();

  ctx.fillStyle = '#e9d7a0';
  ctx.font = '11px ui-monospace, SFMono-Regular, Menlo, monospace';
  ctx.textAlign = 'center';
  ctx.fillText('PLAYER', 0, -28);
  ctx.fillStyle = '#81755c';
  ctx.fillText('NO SPRITE BOUND', 0, 35);
  ctx.restore();
}

function drawHud(viewWidth) {
  ctx.fillStyle = 'rgba(0,0,0,0.72)';
  ctx.fillRect(12, 12, Math.min(430, viewWidth - 24), 68);
  ctx.strokeStyle = '#604a23';
  ctx.strokeRect(12.5, 12.5, Math.min(429, viewWidth - 25), 67);

  ctx.fillStyle = '#e7c875';
  ctx.font = 'bold 13px ui-monospace, SFMono-Regular, Menlo, monospace';
  ctx.fillText('ORIGINS WEB RUNTIME — STEP 1', 24, 35);
  ctx.fillStyle = '#aaa397';
  ctx.font = '11px ui-monospace, SFMono-Regular, Menlo, monospace';
  ctx.fillText('Fixed 60 Hz simulation • 8 Zircon directions • local visual preview only', 24, 55);
  ctx.fillText('Server authority and real assets are intentionally not emulated here.', 24, 70);
}

function render() {
  const { cssWidth, cssHeight, dpr } = resizeCanvas();
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.imageSmoothingEnabled = false;
  updateCamera(cssWidth, cssHeight);
  drawGrid(cssWidth, cssHeight);
  drawWorldBounds(cssWidth, cssHeight);
  drawDiagnosticPlayer();
  drawHud(cssWidth);

  const snapshot = player.snapshot();
  actionValue.textContent = `${snapshot.actionName} (${snapshot.action})`;
  directionValue.textContent = `${snapshot.directionName} (${snapshot.direction})`;
  positionValue.textContent = `${snapshot.x.toFixed(2)}, ${snapshot.y.toFixed(2)}`;
  frameValue.textContent = String(snapshot.frameIndex);
}

const runtime = new FixedStepRuntime(delta => {
  player.update(delta, input, {
    minX: 0.5,
    minY: 0.5,
    maxX: WORLD.width - 0.5,
    maxY: WORLD.height - 0.5,
  });
});

function loop(timestamp) {
  runtime.tick(timestamp);
  render();
  requestAnimationFrame(loop);
}

requestAnimationFrame(loop);

window.ORIGINS_WEB_RUNTIME = Object.freeze({
  mode: RUNTIME_MODE.PreviewLocal,
  sourceCommit: ZIRCON_SOURCE_COMMIT,
  getPlayerSnapshot: () => player.snapshot(),
  MirAction: MIR_ACTION_BY_VALUE,
  MirDirection: MIR_DIRECTION_BY_VALUE,
});
