import test from 'node:test';
import assert from 'node:assert/strict';

import {
  PLAYER_ANIMATION_SOURCE,
  resolvePlayerDrawPlan,
  resolvePlayerLibrarySelection,
} from '../player-animation-runtime.js';
import { resolvePlayerVisualComposition } from '../player-visual-runtime.js';
import {
  ZIRCON_COSTUME_HIDE_WEAPON,
  ZIRCON_PLAYER_ASSET_CONTRACT,
  ZIRCON_PLAYER_LIBRARY_SELECTORS,
} from '../generated/zircon-player-asset-contract.generated.js';

const libraryNames = new Set(ZIRCON_PLAYER_ASSET_CONTRACT.playerLibraries.map(row => row.libraryFile));

function visual(overrides = {}) {
  return resolvePlayerVisualComposition({
    drawFrame: 40,
    direction: 4,
    animation: 'Standing',
    playerClass: 'Warrior',
    gender: 'Male',
    armourShape: 0,
    costumeShape: -1,
    helmetShape: 0,
    hairType: 1,
    libraryWeaponShape: 0,
    weaponEquipped: false,
    shieldShape: -1,
    horseShape: 0,
    horseType: 0,
    drawWeapon: true,
    hideHead: false,
    ...overrides,
  });
}

test('complete pinned PlayerObject visual source counts remain locked', () => {
  assert.equal(PLAYER_ANIMATION_SOURCE.frameCount, 42);
  assert.equal(PLAYER_ANIMATION_SOURCE.libraryCount, 137);
  assert.equal(PLAYER_ANIMATION_SOURCE.selectorCount, 122);
});

test('every PlayerObject dictionary selector resolves to a contracted player library', () => {
  for (const [selectorName, mapping] of Object.entries(ZIRCON_PLAYER_LIBRARY_SELECTORS)) {
    for (const [key, libraryFile] of Object.entries(mapping)) {
      assert.ok(libraryNames.has(libraryFile), `${selectorName}[${key}] -> ${libraryFile} missing from contract`);
    }
  }
});

test('normal and Assassin costumes select exact male/female Zircon libraries', () => {
  assert.equal(resolvePlayerLibrarySelection({ gender: 'Male', costumeShape: 0 }).body, 'M_Costume');
  assert.equal(resolvePlayerLibrarySelection({ gender: 'Male', costumeShape: 10 }).body, 'M_CostumeEx1');
  assert.equal(resolvePlayerLibrarySelection({ gender: 'Female', costumeShape: 0 }).body, 'WM_Costume');
  assert.equal(resolvePlayerLibrarySelection({ gender: 'Female', costumeShape: 10 }).body, 'WM_CostumeEx1');
  assert.equal(resolvePlayerLibrarySelection({ playerClass: 'Assassin', gender: 'Male', costumeShape: 0 }).body, 'M_CostumeA');
  assert.equal(resolvePlayerLibrarySelection({ playerClass: 'Assassin', gender: 'Female', costumeShape: 0 }).body, 'WM_CostumeA');
});

test('every pinned costume hide shape suppresses weapon and shield without suppressing body/head', () => {
  assert.deepEqual([...ZIRCON_COSTUME_HIDE_WEAPON], [6, 7, 8, 9, 10, 11, 12, 13, 16, 17, 18]);
  for (const costumeShape of ZIRCON_COSTUME_HIDE_WEAPON) {
    const composition = visual({
      costumeShape,
      weaponEquipped: true,
      shieldShape: 0,
    });
    const layers = composition.layers.map(layer => layer.layer);
    assert.ok(layers.includes('body'), `costume ${costumeShape} omitted body`);
    assert.ok(layers.includes('hair'), `costume ${costumeShape} omitted hair`);
    assert.ok(!layers.includes('weapon1') && !layers.includes('weapon2'), `costume ${costumeShape} leaked weapon`);
    assert.ok(!layers.includes('shield'), `costume ${costumeShape} leaked shield`);
  }
});

test('a non-hiding costume keeps explicitly equipped weapon and shield', () => {
  const composition = visual({ costumeShape: 0, weaponEquipped: true, shieldShape: 0 });
  assert.deepEqual(composition.layers.map(layer => layer.layer), ['body', 'hair', 'weapon1', 'shield']);
  assert.equal(composition.layers[0].libraryFile, 'M_Costume');
});

test('HideHead suppresses both hair and helmet while preserving equipment', () => {
  const hair = visual({ hideHead: true, weaponEquipped: true });
  assert.deepEqual(hair.layers.map(layer => layer.layer), ['body', 'weapon1']);

  const helmet = visual({ hideHead: true, helmetShape: 1, weaponEquipped: true, shieldShape: 0 });
  assert.deepEqual(helmet.layers.map(layer => layer.layer), ['body', 'weapon1', 'shield']);
});

test('all seven Zircon horse shapes resolve exact source libraries', () => {
  const expected = {
    0: ['Horse', null],
    1: ['HorseIron', null],
    2: ['HorseSilver', null],
    3: ['HorseGold', null],
    4: ['HorseBlue', null],
    5: ['HorseDark', 'HorseDarkEffect'],
    6: ['HorseRoyal', 'HorseRoyalEffect'],
    7: ['HorseBlueDragon', 'HorseBlueDragonEffect'],
  };

  for (const [shapeText, [shapeLibrary, effectLibrary]] of Object.entries(expected)) {
    const horseShape = Number(shapeText);
    const selection = resolvePlayerLibrarySelection({ horseShape });
    assert.equal(horseShape === 0 ? selection.horseBase : selection.horseShape, shapeLibrary);
    assert.equal(selection.horseShapeEffect, effectLibrary);
  }
});

test('mounted draw plan matches native overlay behavior: Dark/Royal overlay, BlueDragon overlay disabled', () => {
  for (const horseShape of [5, 6]) {
    const plan = resolvePlayerDrawPlan({ direction: 4, animation: 'HorseWalking', horseShape });
    assert.equal(plan[0].layer, 'horse');
    assert.equal(plan.at(-1).layer, 'horseShapeEffect');
  }
  const blueDragon = resolvePlayerDrawPlan({ direction: 4, animation: 'HorseWalking', horseShape: 7 });
  assert.equal(blueDragon[0].layer, 'horse');
  assert.ok(!blueDragon.some(step => step.layer === 'horseShapeEffect'));
});

test('Assassin dual weapons resolve exact left/right libraries for both genders', () => {
  const male = resolvePlayerLibrarySelection({ playerClass: 'Assassin', gender: 'Male', libraryWeaponShape: 1200 });
  assert.equal(male.weapon1, 'M_WeaponADL1');
  assert.equal(male.weapon2, 'M_WeaponADR1');

  const female = resolvePlayerLibrarySelection({ playerClass: 'Assassin', gender: 'Female', libraryWeaponShape: 1200 });
  assert.equal(female.weapon1, 'WM_WeaponADL1');
  assert.equal(female.weapon2, 'WM_WeaponADR1');

  const chaotic = resolvePlayerLibrarySelection({ playerClass: 'Assassin', gender: 'Male', libraryWeaponShape: 1263 });
  assert.equal(chaotic.weapon1, 'M_WeaponADR1');
  assert.equal(chaotic.weapon2, null);
});

test('unknown body selector falls back to the gender/class default without inventing a library', () => {
  const normal = resolvePlayerLibrarySelection({ gender: 'Female', armourShape: 999999 });
  assert.equal(normal.body, 'WM_Hum');
  assert.equal(normal.effectiveArmourShape, 0);

  const assassin = resolvePlayerLibrarySelection({ playerClass: 'Assassin', gender: 'Male', armourShape: 999999 });
  assert.equal(assassin.body, 'M_HumA');
  assert.equal(assassin.effectiveArmourShape, 0);
});
