import {
  FixedStepRuntime,
  MIR_ACTION_BY_VALUE,
  MIR_DIRECTION_BY_VALUE,
  PreviewPlayerObject,
  RUNTIME_MODE,
  ZIRCON_SOURCE_COMMIT,
} from './runtime-core.js';
import {
  getPlayerFrameDefinition,
  resolvePlayerAnimation,
  resolvePlayerFrameAtElapsed,
  resolvePlayerLayerFrames,
} from './player-animation-runtime.js';
import {
  PLAYER_ASSET_STATUS,
  ZirconPlayerSpriteStore,
  drawResolvedFrame,
  resolveBaseHumanLibrary,
} from './player-sprite-runtime.js';

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

const previewParams = new URLSearchParams(window.location.search);
const requestedPreviewGender = previewParams.get('gender');
const requestedDirection = parseIntegerInRange(previewParams.get('direction'), 0, 7, null);
const requestedArmourShape = parseIntegerInRange(previewParams.get('armourShape'), 0, 10, 0);
const requestedAnimation = validateAnimationName(previewParams.get('animation'));

const player = new PreviewPlayerObject({
  x: 32,
  y: 24,
  direction: requestedDirection ?? 4,
});
const spriteStore = new ZirconPlayerSpriteStore({ rootUrl: './assets/player/' });
const input = { x: 0, y: 0 };
const keyboard = new Set();
const touchDirections = new Map();
const camera = { x: 0, y: 0 };
const visualState = {
  gender: requestedPreviewGender === 'Female' ? 'Female' : 'Male',
  armourShape: requestedArmourShape,
  forcedAnimation: requestedAnimation,
  forcedDirection: requestedDirection,
  actionName: null,
  animation: requestedAnimation ?? 'Standing',
  animationStartedAt: performance.now(),
  pairStatus: PLAYER_ASSET_STATUS.Missing,
};

setRenderDiagnostics({
  previewGender: visualState.gender,
  pairStatus: visualState.pairStatus,
  playerLibrary: resolveBaseHumanLibrary(visualState.gender),
  armourShape: visualState.armourShape,
  animation: visualState.animation,
  direction: visualState.forcedDirection ?? player.direction,
  realFrameDrawn: false,
});

runtimeValue.textContent = RUNTIME_MODE.PreviewLocal;
sourceValue.textContent = ZIRCON_SOURCE_COMMIT.slice(0, 12);
assetValue.textContent = 'probing M-Hum + WM-Hum';
serverValue.textContent = 'disconnected by design (local visual runtime)';

void initializePlayerAssets();

async function initializePlayerAssets() {
  const status = await spriteStore.load();
  visualState.pairStatus = spriteStore.getBaseHumanPairStatus();
  setRenderDiagnostics({ pairStatus: visualState.pairStatus });

  if (status !== PLAYER_ASSET_STATUS.Ready || visualState.pairStatus !== PLAYER_ASSET_STATUS.Ready) {
    assetValue.textContent = visualState.pairStatus === PLAYER_ASSET_STATUS.Partial
      ? 'M-Hum / WM-Hum incomplete pair'
      : 'M-Hum + WM-Hum pending real Zircon .Zl';
    return;
  }

  assetValue.textContent = 'M-Hum + WM-Hum READY';
  await prewarmBaseHumanPreviewFrames();
}

async function prewarmBaseHumanPreviewFrames() {
  const animations = ['Standing', 'Walking'];
  const requests = [];
  for (const gender of ['Male', 'Female']) {
    for (const animation of animations) {
      const frame = getPlayerFrameDefinition(animation);
      for (let direction = 0; direction < 8; direction += 1) {
        for (let localFrame = 0; localFrame < frame.frameCount; localFrame += 1) {
          const drawFrame = frame.startIndex + frame.offset * direction + localFrame;
          const imageIndex = resolveBodyImageIndex(drawFrame, visualState.armourShape);
          requests.push(spriteStore.requestBaseHumanFrame(gender, imageIndex));
        }
      }
    }
  }
  await Promise.allSettled(requests);
}

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

function updateVisualAnimation(snapshot, timestamp) {
  if (visualState.forcedAnimation) {
    if (visualState.animation !== visualState.forcedAnimation) {
      visualState.animation = visualState.forcedAnimation;
      visualState.animationStartedAt = timestamp;
    }
    visualState.actionName = `FORCED:${visualState.forcedAnimation}`;
    return;
  }

  if (visualState.actionName === snapshot.actionName) return;
  visualState.actionName = snapshot.actionName;
  visualState.animation = resolvePlayerAnimation({
    action: snapshot.actionName,
    moveDistance: 1,
    playerClass: 'Warrior',
  }).animation;
  visualState.animationStartedAt = timestamp;
}

function resolvePreviewBaseDrawFrame(snapshot, timestamp) {
  updateVisualAnimation(snapshot, timestamp);
  const definition = getPlayerFrameDefinition(visualState.animation);
  const duration = definition.delaysMs.reduce((sum, delay) => sum + delay, 0);
  const elapsedMs = duration > 0 ? (timestamp - visualState.animationStartedAt) % duration : 0;
  const direction = visualState.forcedDirection ?? snapshot.direction;
  const runtimeAction = visualState.animation === 'Pushed' ? 'Pushed' : snapshot.actionName;
  return resolvePlayerFrameAtElapsed(
    visualState.animation,
    direction,
    elapsedMs,
    { action: runtimeAction },
  ).drawFrame;
}

function resolveBodyImageIndex(drawFrame, armourShape = visualState.armourShape) {
  if (drawFrame === null) return null;
  return resolvePlayerLayerFrames({
    drawFrame,
    playerClass: 'Warrior',
    armourShape,
    costumeShape: -1,
    armourShift: 0,
  }).body;
}

function resolvePreviewBodyImageIndex(snapshot, timestamp) {
  return resolveBodyImageIndex(resolvePreviewBaseDrawFrame(snapshot, timestamp));
}

function drawPlayer(snapshot, timestamp) {
  const x = player.x * WORLD.tile - camera.x;
  const y = player.y * WORLD.tile - camera.y;

  if (visualState.pairStatus === PLAYER_ASSET_STATUS.Ready) {
    const imageIndex = resolvePreviewBodyImageIndex(snapshot, timestamp);
    if (imageIndex !== null) {
      const library = resolveBaseHumanLibrary(visualState.gender);
      const resolved = spriteStore.peekFrame(library, imageIndex);
      if (resolved) {
        drawResolvedFrame(ctx, resolved, x, y);
        setRenderDiagnostics({
          previewGender: visualState.gender,
          pairStatus: visualState.pairStatus,
          playerLibrary: library,
          armourShape: visualState.armourShape,
          animation: visualState.animation,
          direction: visualState.forcedDirection ?? snapshot.direction,
          realFrameDrawn: true,
          imageIndex,
        });
        return;
      }
      void spriteStore.requestFrame(library, imageIndex);
    }
  }

  setRenderDiagnostics({
    armourShape: visualState.armourShape,
    animation: visualState.animation,
    direction: visualState.forcedDirection ?? snapshot.direction,
    realFrameDrawn: false,
  });
  drawDiagnosticPlayer(snapshot, x, y);
}

function drawDiagnosticPlayer(snapshot, x, y) {
  const direction = visualState.forcedDirection ?? snapshot.direction;
  const [dx, dy] = directionUnit(direction);

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
  ctx.fillText(`PLAYER ${visualState.gender.toUpperCase()} SHAPE ${visualState.armourShape}`, 0, -28);
  ctx.fillStyle = '#81755c';
  ctx.fillText('REQUESTED ZL FRAME IS EMPTY/NOT LOADED', 0, 35);
  ctx.restore();
}

function drawHud(viewWidth) {
  ctx.fillStyle = 'rgba(0,0,0,0.72)';
  ctx.fillRect(12, 12, Math.min(500, viewWidth - 24), 84);
  ctx.strokeStyle = '#604a23';
  ctx.strokeRect(12.5, 12.5, Math.min(499, viewWidth - 25), 83);

  ctx.fillStyle = '#e7c875';
  ctx.font = 'bold 13px ui-monospace, SFMono-Regular, Menlo, monospace';
  ctx.fillText('ORIGINS WEB RUNTIME — PLAYER ASSETS STEP 2', 24, 35);
  ctx.fillStyle = '#aaa397';
  ctx.font = '11px ui-monospace, SFMono-Regular, Menlo, monospace';
  ctx.fillText('Native Zircon timing • M-Hum male • WM-Hum female • 8 directions', 24, 55);
  ctx.fillText(`Body bank: ArmourShape ${visualState.armourShape} (${visualState.armourShape * 5000} shift)`, 24, 70);
  ctx.fillText(`Animation: ${visualState.animation}${visualState.forcedAnimation ? ' [QA override]' : ''}`, 24, 85);
}

function render(timestamp) {
  const { cssWidth, cssHeight, dpr } = resizeCanvas();
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.imageSmoothingEnabled = false;
  updateCamera(cssWidth, cssHeight);
  drawGrid(cssWidth, cssHeight);
  drawWorldBounds(cssWidth, cssHeight);

  const snapshot = player.snapshot();
  drawPlayer(snapshot, timestamp);
  drawHud(cssWidth);

  const effectiveDirection = visualState.forcedDirection ?? snapshot.direction;
  const baseDrawFrame = resolvePreviewBaseDrawFrame(snapshot, timestamp);
  const bodyImageIndex = resolveBodyImageIndex(baseDrawFrame);
  actionValue.textContent = visualState.forcedAnimation
    ? `QA ${visualState.forcedAnimation}`
    : `${snapshot.actionName} (${snapshot.action})`;
  directionValue.textContent = `${MIR_DIRECTION_BY_VALUE[effectiveDirection]} (${effectiveDirection})`;
  positionValue.textContent = `${snapshot.x.toFixed(2)}, ${snapshot.y.toFixed(2)}`;
  frameValue.textContent = `${baseDrawFrame ?? '—'} → ${bodyImageIndex ?? '—'}`;
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
  render(timestamp);
  requestAnimationFrame(loop);
}

requestAnimationFrame(loop);

function setPreviewGender(gender) {
  const library = resolveBaseHumanLibrary(gender);
  visualState.gender = gender;
  visualState.actionName = null;
  visualState.animationStartedAt = performance.now();
  setRenderDiagnostics({
    previewGender: gender,
    playerLibrary: library,
    realFrameDrawn: false,
  });
}

function setPreviewArmourShape(armourShape) {
  const parsed = parseIntegerInRange(armourShape, 0, 10, null);
  if (parsed === null) throw new RangeError(`Base M-Hum/WM-Hum armourShape must be 0..10: ${armourShape}`);
  visualState.armourShape = parsed;
  visualState.animationStartedAt = performance.now();
  setRenderDiagnostics({ armourShape: parsed, realFrameDrawn: false });
}

function setPreviewAnimation(animation) {
  if (animation === null || animation === undefined || animation === '') {
    visualState.forcedAnimation = null;
    visualState.actionName = null;
    visualState.animationStartedAt = performance.now();
    return;
  }
  const valid = validateAnimationName(String(animation));
  if (!valid) throw new RangeError(`Unknown pinned Zircon player animation: ${animation}`);
  visualState.forcedAnimation = valid;
  visualState.animation = valid;
  visualState.actionName = `FORCED:${valid}`;
  visualState.animationStartedAt = performance.now();
  setRenderDiagnostics({ animation: valid, realFrameDrawn: false });
}

function setPreviewDirection(direction) {
  const parsed = parseIntegerInRange(direction, 0, 7, null);
  if (parsed === null) throw new RangeError(`MirDirection must be 0..7: ${direction}`);
  visualState.forcedDirection = parsed;
  visualState.animationStartedAt = performance.now();
  setRenderDiagnostics({ direction: parsed, realFrameDrawn: false });
}

function clearPreviewDirectionOverride() {
  visualState.forcedDirection = null;
  visualState.animationStartedAt = performance.now();
}

function parseIntegerInRange(value, min, max, fallback) {
  if (value === null || value === undefined || value === '') return fallback;
  const parsed = Number(value);
  return Number.isInteger(parsed) && parsed >= min && parsed <= max ? parsed : fallback;
}

function validateAnimationName(value) {
  if (!value) return null;
  try {
    getPlayerFrameDefinition(value);
    return value;
  } catch {
    return null;
  }
}

function setRenderDiagnostics({
  previewGender,
  pairStatus,
  playerLibrary,
  armourShape,
  animation,
  direction,
  realFrameDrawn,
  imageIndex,
} = {}) {
  const dataset = document.documentElement.dataset;
  if (previewGender !== undefined) dataset.previewGender = String(previewGender);
  if (pairStatus !== undefined) dataset.playerAssetPair = String(pairStatus);
  if (playerLibrary !== undefined) dataset.playerLibrary = String(playerLibrary);
  if (armourShape !== undefined) dataset.playerArmourShape = String(armourShape);
  if (animation !== undefined) dataset.playerAnimation = String(animation);
  if (direction !== undefined) dataset.playerDirection = String(direction);
  if (realFrameDrawn !== undefined) dataset.realFrameDrawn = String(Boolean(realFrameDrawn));
  if (imageIndex !== undefined) dataset.playerImageIndex = String(imageIndex);
}

window.ORIGINS_WEB_RUNTIME = Object.freeze({
  mode: RUNTIME_MODE.PreviewLocal,
  sourceCommit: ZIRCON_SOURCE_COMMIT,
  getPlayerSnapshot: () => player.snapshot(),
  getPreviewGender: () => visualState.gender,
  setPreviewGender,
  getPreviewArmourShape: () => visualState.armourShape,
  setPreviewArmourShape,
  getPreviewAnimation: () => visualState.forcedAnimation ?? visualState.animation,
  setPreviewAnimation,
  setPreviewDirection,
  clearPreviewDirectionOverride,
  getBaseHumanPairStatus: () => visualState.pairStatus,
  MirAction: MIR_ACTION_BY_VALUE,
  MirDirection: MIR_DIRECTION_BY_VALUE,
});