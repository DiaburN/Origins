import test from 'node:test';
import assert from 'node:assert/strict';

import {
  collectPlayerVisualFrameRequests,
  collectPlayerVisualLibraryFiles,
  resolvePlayerVisualComposition,
} from '../player-visual-runtime.js';

test('base Warrior body resolves gender-specific Zircon body library', () => {
  const male = resolvePlayerVisualComposition({
    drawFrame: 40,
    direction: 4,
    playerClass: 'Warrior',
    gender: 'Male',
    armourShape: 0,
    drawWeapon: false,
  });
  const female = resolvePlayerVisualComposition({
    drawFrame: 40,
    direction: 4,
    playerClass: 'Warrior',
    gender: 'Female',
    armourShape: 0,
    drawWeapon: false,
  });

  assert.equal(male.layers.length, 1);
  assert.equal(male.layers[0].layer, 'body');
  assert.equal(male.layers[0].libraryFile, 'M_Hum');
  assert.equal(male.layers[0].imageIndex, 40);

  assert.equal(female.layers.length, 1);
  assert.equal(female.layers[0].libraryFile, 'WM_Hum');
  assert.equal(female.layers[0].imageIndex, 40);
});

test('normal body armour bank uses the pinned +5000 shape stride', () => {
  const composition = resolvePlayerVisualComposition({
    drawFrame: 2040,
    direction: 4,
    animation: 'FishingCast',
    playerClass: 'Warrior',
    gender: 'Male',
    armourShape: 5,
    drawWeapon: false,
  });

  assert.equal(composition.armourShift, 0);
  assert.equal(composition.layers[0].libraryFile, 'M_Hum');
  assert.equal(composition.layers[0].imageIndex, 27040);
});

test('Assassin Fishing applies the pinned +80 ArmourShift', () => {
  const composition = resolvePlayerVisualComposition({
    drawFrame: 2040,
    direction: 4,
    animation: 'FishingCast',
    playerClass: 'Assassin',
    gender: 'Female',
    armourShape: 0,
    drawWeapon: false,
  });

  assert.equal(composition.armourShift, 80);
  const body = composition.layers.find(layer => layer.layer === 'body');
  assert.ok(body);
  assert.equal(body.libraryFile, 'WM_HumA');
  assert.equal(body.imageIndex, 2120);
});

test('horse shape 5 composes dark horse behind player and its effect overlay after player', () => {
  const composition = resolvePlayerVisualComposition({
    drawFrame: 200,
    direction: 4,
    animation: 'HorseWalking',
    playerClass: 'Warrior',
    gender: 'Male',
    armourShape: 0,
    horseShape: 5,
    horseType: 1,
    drawWeapon: false,
  });

  assert.deepEqual(composition.layers.map(layer => layer.layer), [
    'horse',
    'body',
    'horseShapeEffect',
  ]);
  assert.equal(composition.layers[0].libraryFile, 'HorseDark');
  assert.equal(composition.layers[0].imageIndex, 200);
  assert.equal(composition.layers.at(-1).libraryFile, 'HorseDarkEffect');
  assert.equal(composition.layers.at(-1).imageIndex, 200);
});

test('composition exposes deduplicated libraries and exact frame requests', () => {
  const composition = resolvePlayerVisualComposition({
    drawFrame: 80,
    direction: 0,
    animation: 'Walking',
    playerClass: 'Warrior',
    gender: 'Male',
    armourShape: 0,
    hairType: 1,
    drawWeapon: false,
  });

  assert.deepEqual(collectPlayerVisualLibraryFiles(composition), ['M_Hum', 'M_Hair']);
  assert.deepEqual(collectPlayerVisualFrameRequests(composition), [
    { libraryFile: 'M_Hum', imageIndex: 80 },
    { libraryFile: 'M_Hair', imageIndex: 80 },
  ]);
});
