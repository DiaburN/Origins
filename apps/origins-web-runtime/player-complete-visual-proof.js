import { getPlayerFrameDefinition } from './player-animation-runtime.js';
import { resolvePlayerVisualComposition } from './player-visual-runtime.js';
import { PLAYER_ASSET_STATUS, ZirconPlayerSpriteStore, drawResolvedFrame } from './player-sprite-runtime.js';

const canvas = document.querySelector('#proof');
const ctx = canvas.getContext('2d', { alpha: false });
const resultNode = document.querySelector('#result');
const store = new ZirconPlayerSpriteStore({ rootUrl: './assets/player/' });

function firstDrawFrame(animation, direction = 4) {
  const frame = getPlayerFrameDefinition(animation);
  return frame.startIndex + frame.offset * direction;
}

const STANDING_DOWN = firstDrawFrame('Standing', 4);
const HORSE_WALK_DOWN = firstDrawFrame('HorseWalking', 4);

const CASES = [
  {
    id: 'male-no-equipment', label: 'Male — no equipment', x: 110, y: 210,
    context: { drawFrame: STANDING_DOWN, direction: 4, animation: 'Standing', playerClass: 'Warrior', gender: 'Male', hairType: 1 },
    expected: ['M_Hum', 'M_Hair'],
  },
  {
    id: 'female-no-equipment', label: 'Female — no equipment', x: 340, y: 210,
    context: { drawFrame: STANDING_DOWN, direction: 4, animation: 'Standing', playerClass: 'Warrior', gender: 'Female', hairType: 1 },
    expected: ['WM_Hum', 'WM_Hair'],
  },
  {
    id: 'male-equipped', label: 'Male — helmet + weapon + shield', x: 600, y: 210,
    context: { drawFrame: STANDING_DOWN, direction: 4, animation: 'Standing', playerClass: 'Warrior', gender: 'Male', helmetShape: 1, hairType: 1, libraryWeaponShape: 0, weaponEquipped: true, shieldShape: 0 },
    expected: ['M_Hum', 'M_Helmet1', 'M_Weapon1', 'M_Shield1'],
  },
  {
    id: 'female-equipped', label: 'Female — helmet + weapon + shield', x: 920, y: 210,
    context: { drawFrame: STANDING_DOWN, direction: 4, animation: 'Standing', playerClass: 'Warrior', gender: 'Female', helmetShape: 1, hairType: 1, libraryWeaponShape: 0, weaponEquipped: true, shieldShape: 0 },
    expected: ['WM_Hum', 'WM_Helmet1', 'WM_Weapon1', 'WM_Shield1'],
  },
  {
    id: 'male-costume-hide', label: 'Male costume 10 — weapon/shield hidden', x: 150, y: 470,
    context: { drawFrame: STANDING_DOWN, direction: 4, animation: 'Standing', playerClass: 'Warrior', gender: 'Male', costumeShape: 10, hairType: 1, libraryWeaponShape: 0, weaponEquipped: true, shieldShape: 0 },
    expected: ['M_CostumeEx1', 'M_Hair'],
  },
  {
    id: 'female-costume-hide', label: 'Female costume 10 — weapon/shield hidden', x: 420, y: 470,
    context: { drawFrame: STANDING_DOWN, direction: 4, animation: 'Standing', playerClass: 'Warrior', gender: 'Female', costumeShape: 10, hairType: 1, libraryWeaponShape: 0, weaponEquipped: true, shieldShape: 0 },
    expected: ['WM_CostumeEx1', 'WM_Hair'],
  },
  {
    id: 'male-assassin-dual', label: 'Male Assassin — dual weapon', x: 730, y: 470,
    context: { drawFrame: STANDING_DOWN, direction: 4, animation: 'Standing', playerClass: 'Assassin', gender: 'Male', hairType: 1, libraryWeaponShape: 1200, weaponEquipped: true },
    expected: ['M_WeaponADR1', 'M_HumA', 'M_HairA', 'M_WeaponADL1'],
  },
  {
    id: 'female-assassin-dual', label: 'Female Assassin — dual weapon', x: 1030, y: 470,
    context: { drawFrame: STANDING_DOWN, direction: 4, animation: 'Standing', playerClass: 'Assassin', gender: 'Female', hairType: 1, libraryWeaponShape: 1200, weaponEquipped: true },
    expected: ['WM_WeaponADR1', 'WM_HumA', 'WM_HairA', 'WM_WeaponADL1'],
  },
  {
    id: 'dark-horse', label: 'Dark horse + native overlay', x: 240, y: 735,
    context: { drawFrame: HORSE_WALK_DOWN, direction: 4, animation: 'HorseWalking', playerClass: 'Warrior', gender: 'Male', horseShape: 5, horseType: 1 },
    expected: ['HorseDark', 'M_Hum', 'HorseDarkEffect'],
  },
  {
    id: 'royal-horse', label: 'Royal horse + native overlay', x: 600, y: 735,
    context: { drawFrame: HORSE_WALK_DOWN, direction: 4, animation: 'HorseWalking', playerClass: 'Warrior', gender: 'Female', horseShape: 6, horseType: 1 },
    expected: ['HorseRoyal', 'WM_Hum', 'HorseRoyalEffect'],
  },
  {
    id: 'blue-dragon', label: 'BlueDragon — overlay disabled upstream', x: 960, y: 735,
    context: { drawFrame: HORSE_WALK_DOWN, direction: 4, animation: 'HorseWalking', playerClass: 'Warrior', gender: 'Male', horseShape: 7, horseType: 1 },
    expected: ['HorseBlueDragon', 'M_Hum'],
  },
];

function drawBackground() {
  ctx.fillStyle = '#111416';
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  ctx.strokeStyle = '#202629';
  for (let x = 0; x < canvas.width; x += 40) {
    ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, canvas.height); ctx.stroke();
  }
  for (let y = 0; y < canvas.height; y += 40) {
    ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(canvas.width, y); ctx.stroke();
  }
}

async function drawCase(row) {
  const composition = resolvePlayerVisualComposition({
    armourShape: 0,
    costumeShape: -1,
    helmetShape: 0,
    hairType: 0,
    libraryWeaponShape: 0,
    weaponEquipped: false,
    shieldShape: -1,
    horseShape: 0,
    horseType: 0,
    drawWeapon: true,
    hideHead: false,
    ...row.context,
  });

  const libraries = composition.layers.map(layer => layer.libraryFile);
  if (JSON.stringify(libraries) !== JSON.stringify(row.expected)) {
    throw new Error(`${row.id}: composition ${JSON.stringify(libraries)} != ${JSON.stringify(row.expected)}`);
  }

  const resolved = [];
  for (const layer of composition.layers) {
    const frame = await store.getFrame(layer.libraryFile, layer.imageIndex);
    if (!frame) throw new Error(`${row.id}: missing ${layer.libraryFile} frame ${layer.imageIndex}`);
    resolved.push({ layer, frame });
  }
  for (const entry of resolved) drawResolvedFrame(ctx, entry.frame, row.x, row.y);

  ctx.fillStyle = '#e7c875';
  ctx.font = '12px ui-monospace,monospace';
  ctx.textAlign = 'center';
  ctx.fillText(row.label, row.x, row.y - 115);
  return {
    id: row.id,
    label: row.label,
    libraries,
    layers: composition.layers.map(layer => ({
      layer: layer.layer,
      phase: layer.phase,
      libraryFile: layer.libraryFile,
      imageIndex: layer.imageIndex,
    })),
  };
}

async function run() {
  try {
    drawBackground();
    const status = await store.load();
    if (status !== PLAYER_ASSET_STATUS.Ready) throw new Error(`asset store status ${status}`);

    const results = [];
    for (const row of CASES) results.push(await drawCase(row));

    const report = {
      status: 'PASS',
      caseCount: results.length,
      standingDown: STANDING_DOWN,
      horseWalkDown: HORSE_WALK_DOWN,
      cases: results,
    };
    resultNode.textContent = JSON.stringify(report, null, 2);
    Object.assign(document.documentElement.dataset, {
      playerCompleteStatus: 'PASS',
      playerCompleteCaseCount: String(results.length),
      playerCompleteNoEquipment: 'PASS',
      playerCompleteEquipment: 'PASS',
      playerCompleteCostume: 'PASS',
      playerCompleteAssassin: 'PASS',
      playerCompleteHorse: 'PASS',
    });
  } catch (error) {
    const message = error instanceof Error ? error.stack ?? error.message : String(error);
    resultNode.textContent = `FAIL: ${message}`;
    Object.assign(document.documentElement.dataset, {
      playerCompleteStatus: 'FAIL',
      playerCompleteError: message,
    });
  }
}

void run();
