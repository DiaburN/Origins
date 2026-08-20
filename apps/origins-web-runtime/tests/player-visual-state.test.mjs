import test from 'node:test';
import assert from 'node:assert/strict';

import {
  applyPlayerVisualState,
  createPlayerVisualState,
  fromZirconObjectPlayer,
  isMounted,
  toPlayerCompositionContext,
} from '../player-visual-state.js';
import { resolvePlayerVisualComposition } from '../player-visual-runtime.js';

test('default PlayerObject visual state has no equipment or mount', () => {
  const state = createPlayerVisualState();
  assert.deepEqual(state, {
    playerClass: 'Warrior',
    gender: 'Male',
    armourShape: 0,
    costumeShape: -1,
    hairType: 0,
    helmetShape: 0,
    libraryWeaponShape: 0,
    weaponEquipped: false,
    shieldShape: -1,
    horseShape: 0,
    horseType: 0,
    hideHead: false,
  });
  assert.equal(isMounted(state), false);
});

test('visual state patch supports Assassin costume, dual weapon, shield and mount', () => {
  const state = applyPlayerVisualState(createPlayerVisualState(), {
    playerClass: 'Assassin',
    gender: 'Female',
    armourShape: 11,
    costumeShape: 0,
    hairType: 2,
    helmetShape: 1,
    weaponShape: 1200,
    shieldShape: 0,
    horseShape: 6,
    horseType: 1,
    hideHead: true,
  });
  assert.equal(state.playerClass, 'Assassin');
  assert.equal(state.gender, 'Female');
  assert.equal(state.weaponEquipped, true);
  assert.equal(state.libraryWeaponShape, 1200);
  assert.equal(state.shieldShape, 0);
  assert.equal(state.horseShape, 6);
  assert.equal(isMounted(state), true);
  assert.equal(state.hideHead, true);
});

test('weapon can be unequipped without erasing last shape', () => {
  const armed = applyPlayerVisualState(createPlayerVisualState(), { weaponShape: 1200 });
  const unarmed = applyPlayerVisualState(armed, { weaponShape: null });
  assert.equal(unarmed.weaponEquipped, false);
  assert.equal(unarmed.libraryWeaponShape, 1200);
});

test('Zircon ObjectPlayer PascalCase snapshot maps directly to renderer state', () => {
  const state = fromZirconObjectPlayer({
    Class: 'Assassin',
    Gender: 'Female',
    Armour: 22,
    Costume: 0,
    HairType: 3,
    Helmet: 11,
    Weapon: 1200,
    Shield: 0,
    HorseShape: 5,
    Horse: 1,
    HideHead: true,
  });
  assert.deepEqual(state, {
    playerClass: 'Assassin',
    gender: 'Female',
    armourShape: 22,
    costumeShape: 0,
    hairType: 3,
    helmetShape: 11,
    libraryWeaponShape: 1200,
    weaponEquipped: true,
    shieldShape: 0,
    horseShape: 5,
    horseType: 1,
    hideHead: true,
  });
});

test('camelCase ObjectPlayer snapshot and absent equipment sentinels are supported', () => {
  const state = fromZirconObjectPlayer({
    class: 'Wizard',
    gender: 'Male',
    armour: 0,
    costume: -1,
    hairType: 1,
    helmet: 0,
    weapon: -1,
    shield: -1,
    horseShape: 0,
    horse: 'None',
    hideHead: false,
  });
  assert.equal(state.playerClass, 'Wizard');
  assert.equal(state.weaponEquipped, false);
  assert.equal(state.shieldShape, -1);
  assert.equal(state.horseType, 0);
});

test('composition context contains all PlayerObject visual selectors and no unrelated state', () => {
  const state = createPlayerVisualState({
    playerClass: 'Taoist',
    gender: 'Female',
    costumeShape: 10,
    weaponShape: 0,
    shieldShape: 0,
    horseShape: 7,
    horseType: 1,
  });
  assert.deepEqual(toPlayerCompositionContext(state), {
    playerClass: 'Taoist',
    gender: 'Female',
    armourShape: 0,
    costumeShape: 10,
    helmetShape: 0,
    hairType: 0,
    libraryWeaponShape: 0,
    weaponEquipped: true,
    shieldShape: 0,
    horseShape: 7,
    horseType: 1,
    hideHead: false,
  });
});

test('ObjectPlayer state drives source-faithful costume hiding directly into composition', () => {
  const state = fromZirconObjectPlayer({
    Class: 'Wizard',
    Gender: 'Female',
    Armour: 0,
    Costume: 10,
    HairType: 1,
    Helmet: 0,
    Weapon: 0,
    Shield: 0,
    HorseShape: 0,
    Horse: 0,
    HideHead: false,
  });
  const composition = resolvePlayerVisualComposition({
    drawFrame: 40,
    direction: 4,
    animation: 'Standing',
    drawWeapon: true,
    ...toPlayerCompositionContext(state),
  });
  assert.deepEqual(composition.layers.map(layer => layer.libraryFile), ['WM_CostumeEx1', 'WM_Hair']);
  assert.deepEqual(composition.equipment, { weapon: true, helmet: false, shield: true, mounted: false });
});

test('ObjectPlayer Assassin dual weapon state drives both gender-specific weapon layers', () => {
  const state = fromZirconObjectPlayer({
    Class: 'Assassin', Gender: 'Female', Armour: 0, Costume: -1, HairType: 1,
    Helmet: 0, Weapon: 1200, Shield: -1, HorseShape: 0, Horse: 0, HideHead: false,
  });
  const composition = resolvePlayerVisualComposition({
    drawFrame: 40,
    direction: 4,
    animation: 'Standing',
    drawWeapon: true,
    ...toPlayerCompositionContext(state),
  });
  assert.deepEqual(composition.layers.map(layer => layer.libraryFile), [
    'WM_WeaponADR1', 'WM_HumA', 'WM_HairA', 'WM_WeaponADL1',
  ]);
});

test('invalid class and horse shape fail closed', () => {
  assert.throws(() => createPlayerVisualState({ playerClass: 'Monk' }), /MirClass/);
  assert.throws(() => createPlayerVisualState({ horseShape: 8 }), /horseShape/);
});
