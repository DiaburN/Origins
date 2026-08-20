import test from 'node:test';
import assert from 'node:assert/strict';

import {
  applyPlayerVisualState,
  createPlayerVisualState,
  fromZirconObjectPlayer,
  isMounted,
  toPlayerCompositionContext,
} from '../player-visual-state.js';

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
    Costume: 10,
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
    costumeShape: 10,
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

test('invalid class and horse shape fail closed', () => {
  assert.throws(() => createPlayerVisualState({ playerClass: 'Monk' }), /MirClass/);
  assert.throws(() => createPlayerVisualState({ horseShape: 8 }), /horseShape/);
});
