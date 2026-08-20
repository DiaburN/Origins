import test from 'node:test';
import assert from 'node:assert/strict';
import {
  MIR_ACTION,
  MIR_DIRECTION,
  PreviewPlayerObject,
  directionFromVector,
  normalizeInputVector,
} from '../runtime-core.js';

test('MirDirection values match pinned Zircon ordering', () => {
  assert.deepEqual(MIR_DIRECTION, {
    Up: 0,
    UpRight: 1,
    Right: 2,
    DownRight: 3,
    Down: 4,
    DownLeft: 5,
    Left: 6,
    UpLeft: 7,
  });
});

test('MirAction values preserve Zircon enum ordering', () => {
  assert.equal(MIR_ACTION.Standing, 0);
  assert.equal(MIR_ACTION.Moving, 1);
  assert.equal(MIR_ACTION.Attack, 3);
  assert.equal(MIR_ACTION.RangeAttack, 4);
  assert.equal(MIR_ACTION.Spell, 5);
  assert.equal(MIR_ACTION.Die, 8);
  assert.equal(MIR_ACTION.Dead, 9);
  assert.equal(MIR_ACTION.Idle, 16);
});

test('eight-way input maps to the Zircon direction enum', () => {
  const cases = [
    [[0, -1], MIR_DIRECTION.Up],
    [[1, -1], MIR_DIRECTION.UpRight],
    [[1, 0], MIR_DIRECTION.Right],
    [[1, 1], MIR_DIRECTION.DownRight],
    [[0, 1], MIR_DIRECTION.Down],
    [[-1, 1], MIR_DIRECTION.DownLeft],
    [[-1, 0], MIR_DIRECTION.Left],
    [[-1, -1], MIR_DIRECTION.UpLeft],
  ];

  for (const [[x, y], expected] of cases) {
    assert.equal(directionFromVector(x, y), expected);
  }
});

test('diagonal preview movement is normalized', () => {
  const vector = normalizeInputVector(1, 1);
  assert.ok(Math.abs(Math.hypot(vector.x, vector.y) - 1) < 1e-10);
});

test('preview PlayerObject switches only between Standing and Moving in Step 1', () => {
  const player = new PreviewPlayerObject({ x: 10, y: 10, speed: 4 });
  player.update(1 / 60, { x: 0, y: 0 });
  assert.equal(player.action, MIR_ACTION.Standing);

  player.update(1 / 60, { x: 1, y: 0 });
  assert.equal(player.action, MIR_ACTION.Moving);
  assert.equal(player.direction, MIR_DIRECTION.Right);
  assert.ok(player.x > 10);
});

test('preview bounds prevent leaving the diagnostic world', () => {
  const player = new PreviewPlayerObject({ x: 1, y: 1, speed: 100 });
  player.update(1, { x: -1, y: -1 }, { minX: 0.5, minY: 0.5, maxX: 2.5, maxY: 2.5 });
  assert.equal(player.x, 0.5);
  assert.equal(player.y, 0.5);
});
