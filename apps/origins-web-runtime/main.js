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
} from './player-animation-runtime.js';
import {
  PLAYER_ASSET_STATUS,
  ZirconPlayerSpriteStore,
  drawResolvedFrame,
  resolveBaseHumanLibrary,
} from './player-sprite-runtime.js';
import { resolvePlayerVisualComposition } from './player-visual-runtime.js';
import {
  applyPlayerVisualState,
  createPlayerVisualState,
  fromZirconObjectPlayer,
  isMounted,
  toPlayerCompositionContext,
} from './player-visual-state.js';

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

const WORLD = Object.freeze({ width: 64, height: 48, tile: 48 });
const previewParams = new URLSearchParams(window.location.search);
const requestedDirection = parseIntegerInRange(previewParams.get('direction'), 0, 7, null);
const requestedAnimation = validateAnimationName(previewParams.get('animation'));

const initialPlayerVisual = createPlayerVisualState({
  playerClass: parseChoice(previewParams.get('class'), ['Warrior', 'Wizard', 'Taoist', 'Assassin'], 'Warrior'),
  gender: parseChoice(previewParams.get('gender'), ['Male', 'Female'], 'Male'),
  armourShape: parseIntegerInRange(previewParams.get('armourShape'), 0, 999999, 0),
  costumeShape: parseIntegerWithSentinel(previewParams.get('costumeShape'), -1, 999999, -1),
  hairType: parseIntegerInRange(previewParams.get('hairType'), 0, 999999, 0),
  helmetShape: parseIntegerInRange(previewParams.get('helmetShape'), 0, 999999, 0),
  weaponShape: previewParams.has('weaponShape')
    ? parseIntegerInRange(previewParams.get('weaponShape'), 0, 999999, null)
    : null,
  shieldShape: previewParams.has('shieldShape')
    ? parseIntegerWithSentinel(previewParams.get('shieldShape'), -1, 999999, -1)
    : -1,
  horseShape: parseIntegerInRange(previewParams.get('horseShape'), 0, 7, 0),
  horseType: parseIntegerInRange(previewParams.get('horseType'), 0, 255, 0),
  hideHead: parseBoolean(previewParams.get('hideHead'), false),
});

const player = new PreviewPlayerObject({ x: 32, y: 24, direction: requestedDirection ?? 4 });
const spriteStore = new ZirconPlayerSpriteStore({ rootUrl: './assets/player/' });
const input = { x: 0, y: 0 };
const keyboard = new Set();
const touchDirections = new Map();
const camera = { x: 0, y: 0 };
const visualState = {
  player: initialPlayerVisual,
  forcedAnimation: requestedAnimation,
  forcedDirection: requestedDirection,
  actionName: null,
  animation: requestedAnimation ?? 'Standing',
  drawWeapon: true,
  animationStartedAt: performance.now(),
  pairStatus: PLAYER_ASSET_STATUS.Missing,
};

runtimeValue.textContent = RUNTIME_MODE.PreviewLocal;
sourceValue.textContent = ZIRCON_SOURCE_COMMIT.slice(0, 12);
assetValue.textContent = 'probing complete Zircon player assets';
serverValue.textContent = 'disconnected by design (local visual runtime)';
setRenderDiagnostics({ realFrameDrawn: false, visibleLayers: [], missingLayers: [] });
void initializePlayerAssets();

async function initializePlayerAssets() {
  const status = await spriteStore.load();
  visualState.pairStatus = spriteStore.getBaseHumanPairStatus();
  setRenderDiagnostics();
  if (status !== PLAYER_ASSET_STATUS.Ready || visualState.pairStatus !== PLAYER_ASSET_STATUS.Ready) {
    assetValue.textContent = visualState.pairStatus === PLAYER_ASSET_STATUS.Partial
      ? 'M-Hum / WM-Hum incomplete pair'
      : 'Zircon player atlas payload pending';
    return;
  }
  assetValue.textContent = `Zircon player assets READY • ${spriteStore.master?.libraries?.length ?? 0} libraries mounted`;
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
  const pointerKey = pointerId => `${button.dataset.vector}:${pointerId}`;
  button.addEventListener('pointerdown', event => {
    event.preventDefault();
    button.setPointerCapture(event.pointerId);
    touchDirections.set(pointerKey(event.pointerId), vector);
    recomputeInput();
  });
  const release = event => {
    touchDirections.delete(pointerKey(event.pointerId));
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
  camera.x = player.x * WORLD.tile - viewWidth / 2;
  camera.y = player.y * WORLD.tile - viewHeight / 2;
  camera.x = Math.max(0, Math.min(Math.max(0, WORLD.width * WORLD.tile - viewWidth), camera.x));
  camera.y = Math.max(0, Math.min(Math.max(0, WORLD.height * WORLD.tile - viewHeight), camera.y));
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
      const x = col * WORLD.tile - camera.x;
      const y = row * WORLD.tile - camera.y;
      ctx.fillStyle = (row + col) % 2 === 0 ? '#151719' : '#121416';
      ctx.fillRect(x, y, WORLD.tile, WORLD.tile);
      ctx.strokeStyle = '#202326';
      ctx.strokeRect(x + 0.5, y + 0.5, WORLD.tile - 1, WORLD.tile - 1);
    }
  }
}

function drawWorldBounds(viewWidth, viewHeight) {
  ctx.strokeStyle = '#675126';
  ctx.lineWidth = 2;
  ctx.strokeRect(-camera.x, -camera.y, WORLD.width * WORLD.tile, WORLD.height * WORLD.tile);
  ctx.fillStyle = '#69645b';
  ctx.font = '12px ui-monospace, SFMono-Regular, Menlo, monospace';
  ctx.fillText('Diagnostic world — maps intentionally deferred', 14, viewHeight - 18);
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
    visualState.drawWeapon = true;
    visualState.actionName = `FORCED:${visualState.forcedAnimation}`;
    return;
  }

  const signature = `${snapshot.actionName}:${visualState.player.playerClass}:${visualState.player.libraryWeaponShape}:${visualState.player.horseType}`;
  if (visualState.actionName === signature) return;
  visualState.actionName = signature;
  const resolved = resolvePlayerAnimation({
    action: snapshot.actionName,
    moveDistance: 1,
    playerClass: visualState.player.playerClass,
    weaponShape: visualState.player.libraryWeaponShape,
    horse: isMounted(visualState.player),
  });
  visualState.animation = resolved.animation;
  visualState.drawWeapon = resolved.drawWeapon;
  visualState.animationStartedAt = timestamp;
}

function resolvePreviewBaseDrawFrame(snapshot, timestamp) {
  updateVisualAnimation(snapshot, timestamp);
  const definition = getPlayerFrameDefinition(visualState.animation);
  const duration = definition.delaysMs.reduce((sum, delay) => sum + delay, 0);
  const elapsedMs = duration > 0 ? (timestamp - visualState.animationStartedAt) % duration : 0;
  const direction = visualState.forcedDirection ?? snapshot.direction;
  const runtimeAction = visualState.animation === 'Pushed' ? 'Pushed' : snapshot.actionName;
  return resolvePlayerFrameAtElapsed(visualState.animation, direction, elapsedMs, { action: runtimeAction }).drawFrame;
}

function resolvePreviewComposition(snapshot, timestamp) {
  const drawFrame = resolvePreviewBaseDrawFrame(snapshot, timestamp);
  if (drawFrame === null) return null;
  return resolvePlayerVisualComposition({
    drawFrame,
    direction: visualState.forcedDirection ?? snapshot.direction,
    animation: visualState.animation,
    drawWeapon: visualState.drawWeapon,
    ...toPlayerCompositionContext(visualState.player),
  });
}

function drawPlayer(snapshot, timestamp) {
  const anchorX = player.x * WORLD.tile - camera.x;
  const anchorY = player.y * WORLD.tile - camera.y;
  if (visualState.pairStatus === PLAYER_ASSET_STATUS.Ready) {
    const composition = resolvePreviewComposition(snapshot, timestamp);
    if (composition) {
      const visibleLayers = [];
      const missingLayers = [];
      let bodyLayer = null;
      for (const layer of composition.layers) {
        const resolved = spriteStore.peekFrame(layer.libraryFile, layer.imageIndex);
        if (!resolved) {
          missingLayers.push(`${layer.layer}:${layer.libraryFile}:${layer.imageIndex}`);
          void spriteStore.requestFrame(layer.libraryFile, layer.imageIndex);
          continue;
        }
        drawResolvedFrame(ctx, resolved, anchorX, anchorY);
        visibleLayers.push(`${layer.layer}:${layer.libraryFile}`);
        if (layer.layer === 'body') bodyLayer = layer;
      }
      if (bodyLayer && visibleLayers.some(value => value.startsWith('body:'))) {
        setRenderDiagnostics({
          realFrameDrawn: true,
          imageIndex: bodyLayer.imageIndex,
          playerLibrary: bodyLayer.libraryFile,
          visibleLayers,
          missingLayers,
        });
        return;
      }
    }
  }
  setRenderDiagnostics({ realFrameDrawn: false, visibleLayers: [], missingLayers: [] });
  drawDiagnosticPlayer(snapshot, anchorX, anchorY);
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
  ctx.fillStyle = '#f6efda';
  ctx.beginPath();
  ctx.arc(dx * 22, dy * 22 - 4, 3.5, 0, Math.PI * 2);
  ctx.fill();
  ctx.fillStyle = '#e9d7a0';
  ctx.font = '11px ui-monospace, SFMono-Regular, Menlo, monospace';
  ctx.textAlign = 'center';
  ctx.fillText(`${visualState.player.playerClass.toUpperCase()} ${visualState.player.gender.toUpperCase()}`, 0, -28);
  ctx.fillStyle = '#81755c';
  ctx.fillText('REQUESTED ZL FRAME EMPTY / NOT LOADED', 0, 35);
  ctx.restore();
}

function drawHud(viewWidth) {
  const state = visualState.player;
  ctx.fillStyle = 'rgba(0,0,0,0.72)';
  ctx.fillRect(12, 12, Math.min(650, viewWidth - 24), 116);
  ctx.strokeStyle = '#604a23';
  ctx.strokeRect(12.5, 12.5, Math.min(649, viewWidth - 25), 115);
  ctx.fillStyle = '#e7c875';
  ctx.font = 'bold 13px ui-monospace, SFMono-Regular, Menlo, monospace';
  ctx.fillText('ORIGINS WEB RUNTIME — COMPLETE PLAYEROBJECT VISUAL', 24, 35);
  ctx.fillStyle = '#aaa397';
  ctx.font = '11px ui-monospace, SFMono-Regular, Menlo, monospace';
  ctx.fillText(`${state.playerClass} • ${state.gender} • Armour ${state.armourShape} • Costume ${state.costumeShape}`, 24, 55);
  ctx.fillText(`Animation ${visualState.animation}${visualState.forcedAnimation ? ' [QA override]' : ''} • 8 directions`, 24, 71);
  ctx.fillText(`Weapon ${state.weaponEquipped ? state.libraryWeaponShape : 'OFF'} • Helmet ${state.helmetShape || 'OFF'} • Shield ${state.shieldShape >= 0 ? state.shieldShape : 'OFF'}`, 24, 87);
  ctx.fillText(`Horse type ${state.horseType} • armour ${state.horseShape} • HideHead ${state.hideHead ? 'ON' : 'OFF'}`, 24, 103);
  ctx.fillText('Maps deferred • transport disconnected • Zircon remains authoritative', 24, 119);
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

  const composition = resolvePreviewComposition(snapshot, timestamp);
  const body = composition?.layers.find(layer => layer.layer === 'body') ?? null;
  const effectiveDirection = visualState.forcedDirection ?? snapshot.direction;
  actionValue.textContent = visualState.forcedAnimation ? `QA ${visualState.forcedAnimation}` : `${snapshot.actionName} (${snapshot.action})`;
  directionValue.textContent = `${MIR_DIRECTION_BY_VALUE[effectiveDirection]} (${effectiveDirection})`;
  positionValue.textContent = `${snapshot.x.toFixed(2)}, ${snapshot.y.toFixed(2)}`;
  frameValue.textContent = body ? `${composition.frames.body} → ${body.libraryFile}:${body.imageIndex}` : '—';
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

function patchPlayerVisualState(patch) {
  visualState.player = applyPlayerVisualState(visualState.player, patch);
  resetAnimationClock();
  setRenderDiagnostics({ realFrameDrawn: false, visibleLayers: [], missingLayers: [] });
  return visualState.player;
}

function applyObjectPlayerSnapshot(info) {
  visualState.player = fromZirconObjectPlayer(info);
  resetAnimationClock();
  setRenderDiagnostics({ realFrameDrawn: false, visibleLayers: [], missingLayers: [] });
  return visualState.player;
}

function setPreviewGender(gender) { return patchPlayerVisualState({ gender }); }
function setPreviewClass(playerClass) { return patchPlayerVisualState({ playerClass }); }
function setPreviewArmourShape(armourShape) { return patchPlayerVisualState({ armourShape }); }
function setPreviewCostumeShape(costumeShape) { return patchPlayerVisualState({ costumeShape }); }
function setPreviewHideHead(hideHead) { return patchPlayerVisualState({ hideHead }); }
function setPreviewMount({ horseShape = visualState.player.horseShape, horseType = visualState.player.horseType } = {}) {
  return patchPlayerVisualState({ horseShape, horseType });
}
function clearPreviewMount() { return patchPlayerVisualState({ horseShape: 0, horseType: 0 }); }

function setPreviewEquipment(next = {}) {
  const patch = {};
  for (const key of ['hairType', 'helmetShape', 'weaponShape', 'shieldShape']) {
    if (Object.prototype.hasOwnProperty.call(next, key)) patch[key] = next[key];
  }
  return patchPlayerVisualState(patch);
}
function clearPreviewEquipment() {
  return patchPlayerVisualState({ helmetShape: 0, weaponShape: null, shieldShape: -1 });
}

function setPreviewAnimation(animation) {
  if (animation === null || animation === undefined || animation === '') {
    visualState.forcedAnimation = null;
    visualState.actionName = null;
    resetAnimationClock();
    return;
  }
  const valid = validateAnimationName(String(animation));
  if (!valid) throw new RangeError(`Unknown pinned Zircon player animation: ${animation}`);
  visualState.forcedAnimation = valid;
  visualState.animation = valid;
  visualState.actionName = `FORCED:${valid}`;
  visualState.drawWeapon = true;
  resetAnimationClock();
}

function setPreviewDirection(direction) {
  const parsed = parseIntegerInRange(direction, 0, 7, null);
  if (parsed === null) throw new RangeError(`MirDirection must be 0..7: ${direction}`);
  visualState.forcedDirection = parsed;
  resetAnimationClock();
}
function clearPreviewDirectionOverride() {
  visualState.forcedDirection = null;
  resetAnimationClock();
}
function resetAnimationClock() {
  visualState.actionName = null;
  visualState.animationStartedAt = performance.now();
}

function parseIntegerInRange(value, min, max, fallback) {
  if (value === null || value === undefined || value === '') return fallback;
  const parsed = Number(value);
  return Number.isInteger(parsed) && parsed >= min && parsed <= max ? parsed : fallback;
}
function parseIntegerWithSentinel(value, sentinel, max, fallback) {
  if (value === null || value === undefined || value === '') return fallback;
  if (Number(value) === sentinel) return sentinel;
  return parseIntegerInRange(value, 0, max, fallback);
}
function parseChoice(value, allowed, fallback) {
  return allowed.includes(value) ? value : fallback;
}
function parseBoolean(value, fallback) {
  if (value === null || value === undefined || value === '') return fallback;
  if (value === '1' || value === 'true') return true;
  if (value === '0' || value === 'false') return false;
  return fallback;
}
function validateAnimationName(value) {
  if (!value) return null;
  try { getPlayerFrameDefinition(value); return value; } catch { return null; }
}

function setRenderDiagnostics({ realFrameDrawn, imageIndex, playerLibrary, visibleLayers, missingLayers } = {}) {
  const state = visualState.player;
  const dataset = document.documentElement.dataset;
  dataset.previewGender = state.gender;
  dataset.playerClass = state.playerClass;
  dataset.playerArmourShape = String(state.armourShape);
  dataset.playerCostumeShape = String(state.costumeShape);
  dataset.playerHairType = String(state.hairType);
  dataset.playerHelmetShape = String(state.helmetShape);
  dataset.playerWeaponEquipped = String(state.weaponEquipped);
  dataset.playerWeaponShape = state.weaponEquipped ? String(state.libraryWeaponShape) : 'NONE';
  dataset.playerShieldShape = state.shieldShape >= 0 ? String(state.shieldShape) : 'NONE';
  dataset.playerHorseShape = String(state.horseShape);
  dataset.playerHorseType = String(state.horseType);
  dataset.playerMounted = String(isMounted(state));
  dataset.playerHideHead = String(state.hideHead);
  dataset.playerAnimation = visualState.animation;
  dataset.playerDirection = String(visualState.forcedDirection ?? player.direction);
  dataset.playerAssetPair = String(visualState.pairStatus);
  if (playerLibrary !== undefined) dataset.playerLibrary = String(playerLibrary);
  else dataset.playerLibrary = resolveBaseHumanLibrary(state.gender);
  if (realFrameDrawn !== undefined) dataset.realFrameDrawn = String(Boolean(realFrameDrawn));
  if (imageIndex !== undefined) dataset.playerImageIndex = String(imageIndex);
  if (visibleLayers !== undefined) dataset.playerVisibleLayers = visibleLayers.join(',');
  if (missingLayers !== undefined) dataset.playerMissingLayers = missingLayers.join(',');
}

window.ORIGINS_WEB_RUNTIME = Object.freeze({
  mode: RUNTIME_MODE.PreviewLocal,
  sourceCommit: ZIRCON_SOURCE_COMMIT,
  getPlayerSnapshot: () => player.snapshot(),
  getPlayerVisualState: () => visualState.player,
  patchPlayerVisualState,
  applyObjectPlayerSnapshot,
  getPreviewGender: () => visualState.player.gender,
  setPreviewGender,
  getPreviewClass: () => visualState.player.playerClass,
  setPreviewClass,
  getPreviewArmourShape: () => visualState.player.armourShape,
  setPreviewArmourShape,
  getPreviewCostumeShape: () => visualState.player.costumeShape,
  setPreviewCostumeShape,
  getPreviewEquipment: () => Object.freeze({
    hairType: visualState.player.hairType,
    helmetShape: visualState.player.helmetShape,
    weaponShape: visualState.player.weaponEquipped ? visualState.player.libraryWeaponShape : null,
    shieldShape: visualState.player.shieldShape >= 0 ? visualState.player.shieldShape : null,
  }),
  setPreviewEquipment,
  clearPreviewEquipment,
  setPreviewMount,
  clearPreviewMount,
  setPreviewHideHead,
  getPreviewAnimation: () => visualState.forcedAnimation ?? visualState.animation,
  setPreviewAnimation,
  setPreviewDirection,
  clearPreviewDirectionOverride,
  getBaseHumanPairStatus: () => visualState.pairStatus,
  MirAction: MIR_ACTION_BY_VALUE,
  MirDirection: MIR_DIRECTION_BY_VALUE,
});
