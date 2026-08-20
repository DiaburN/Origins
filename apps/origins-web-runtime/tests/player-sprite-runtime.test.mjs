import test from 'node:test';
import assert from 'node:assert/strict';
import {
  BASE_HUMAN_LIBRARY_BY_GENDER,
  PLAYER_ASSET_STATUS,
  ZirconPlayerSpriteStore,
  resolveBaseHumanLibrary,
} from '../player-sprite-runtime.js';

test('base human gender mapping is exactly M_Hum / WM_Hum', () => {
  assert.deepEqual(BASE_HUMAN_LIBRARY_BY_GENDER, {
    Male: 'M_Hum',
    Female: 'WM_Hum',
  });
  assert.equal(resolveBaseHumanLibrary('Male'), 'M_Hum');
  assert.equal(resolveBaseHumanLibrary('Female'), 'WM_Hum');
  assert.throws(() => resolveBaseHumanLibrary('Unknown'), /Unsupported Zircon gender/);
});

test('base human pair is READY only when both male and female libraries exist', () => {
  const store = new ZirconPlayerSpriteStore({ rootUrl: './assets/player/' });
  store.status = PLAYER_ASSET_STATUS.Ready;

  store.master = { libraries: [{ libraryFile: 'M_Hum' }] };
  assert.equal(store.getBaseHumanPairStatus(), PLAYER_ASSET_STATUS.Partial);

  store.master = { libraries: [{ libraryFile: 'WM_Hum' }] };
  assert.equal(store.getBaseHumanPairStatus(), PLAYER_ASSET_STATUS.Partial);

  store.master = { libraries: [{ libraryFile: 'M_Hum' }, { libraryFile: 'WM_Hum' }] };
  assert.equal(store.getBaseHumanPairStatus(), PLAYER_ASSET_STATUS.Ready);

  store.master = { libraries: [] };
  assert.equal(store.getBaseHumanPairStatus(), PLAYER_ASSET_STATUS.Missing);
});
