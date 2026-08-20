export const ZIRCON_SOURCE_COMMIT = 'cbf1aa919083bc13fc3f23f93772a8ab8370632d';

export const MIR_DIRECTION = Object.freeze({
  Up: 0,
  UpRight: 1,
  Right: 2,
  DownRight: 3,
  Down: 4,
  DownLeft: 5,
  Left: 6,
  UpLeft: 7,
});

export const MIR_DIRECTION_BY_VALUE = Object.freeze([
  'Up', 'UpRight', 'Right', 'DownRight', 'Down', 'DownLeft', 'Left', 'UpLeft',
]);

export const MIR_ACTION = Object.freeze({
  Standing: 0,
  Moving: 1,
  Pushed: 2,
  Attack: 3,
  RangeAttack: 4,
  Spell: 5,
  Harvest: 6,
  Struck: 7,
  Die: 8,
  Dead: 9,
  Show: 10,
  Hide: 11,
  Mount: 12,
  Mining: 13,
  Fishing: 14,
  Taming: 15,
  Idle: 16,
});

export const MIR_ACTION_BY_VALUE = Object.freeze([
  'Standing', 'Moving', 'Pushed', 'Attack', 'RangeAttack', 'Spell', 'Harvest',
  'Struck', 'Die', 'Dead', 'Show', 'Hide', 'Mount', 'Mining', 'Fishing', 'Taming', 'Idle',
]);

export const RUNTIME_MODE = Object.freeze({
  PreviewLocal: 'PREVIEW_LOCAL',
  ServerAuthoritative: 'SERVER_AUTHORITATIVE',
});

export const FIXED_STEP_SECONDS = 1 / 60;

const EPSILON = 0.0001;

export function directionFromVector(x, y, fallback = MIR_DIRECTION.Down) {
  if (Math.abs(x) < EPSILON && Math.abs(y) < EPSILON) return fallback;

  const horizontal = x > EPSILON ? 1 : x < -EPSILON ? -1 : 0;
  const vertical = y > EPSILON ? 1 : y < -EPSILON ? -1 : 0;

  if (vertical < 0 && horizontal === 0) return MIR_DIRECTION.Up;
  if (vertical < 0 && horizontal > 0) return MIR_DIRECTION.UpRight;
  if (vertical === 0 && horizontal > 0) return MIR_DIRECTION.Right;
  if (vertical > 0 && horizontal > 0) return MIR_DIRECTION.DownRight;
  if (vertical > 0 && horizontal === 0) return MIR_DIRECTION.Down;
  if (vertical > 0 && horizontal < 0) return MIR_DIRECTION.DownLeft;
  if (vertical === 0 && horizontal < 0) return MIR_DIRECTION.Left;
  return MIR_DIRECTION.UpLeft;
}

export function normalizeInputVector(x, y) {
  const length = Math.hypot(x, y);
  if (length < EPSILON) return { x: 0, y: 0 };
  return { x: x / length, y: y / length };
}

export class PreviewPlayerObject {
  constructor({ x = 20, y = 20, direction = MIR_DIRECTION.Down, speed = 4 } = {}) {
    this.x = x;
    this.y = y;
    this.direction = direction;
    this.action = MIR_ACTION.Standing;
    this.speed = speed;
    this.frameClock = 0;
    this.frameIndex = 0;
  }

  update(deltaSeconds, input, bounds) {
    const rawX = Number(input?.x) || 0;
    const rawY = Number(input?.y) || 0;
    const moving = Math.abs(rawX) >= EPSILON || Math.abs(rawY) >= EPSILON;

    if (!moving) {
      this.action = MIR_ACTION.Standing;
      this.frameClock += deltaSeconds;
      if (this.frameClock >= 0.18) {
        this.frameClock = 0;
        this.frameIndex = (this.frameIndex + 1) % 4;
      }
      return;
    }

    const vector = normalizeInputVector(rawX, rawY);
    this.direction = directionFromVector(vector.x, vector.y, this.direction);
    this.action = MIR_ACTION.Moving;
    this.x += vector.x * this.speed * deltaSeconds;
    this.y += vector.y * this.speed * deltaSeconds;

    if (bounds) {
      this.x = Math.min(Math.max(this.x, bounds.minX), bounds.maxX);
      this.y = Math.min(Math.max(this.y, bounds.minY), bounds.maxY);
    }

    this.frameClock += deltaSeconds;
    if (this.frameClock >= 0.11) {
      this.frameClock = 0;
      this.frameIndex = (this.frameIndex + 1) % 6;
    }
  }

  snapshot() {
    return Object.freeze({
      x: this.x,
      y: this.y,
      direction: this.direction,
      directionName: MIR_DIRECTION_BY_VALUE[this.direction],
      action: this.action,
      actionName: MIR_ACTION_BY_VALUE[this.action],
      frameIndex: this.frameIndex,
    });
  }
}

export class FixedStepRuntime {
  constructor(update, step = FIXED_STEP_SECONDS) {
    this.update = update;
    this.step = step;
    this.accumulator = 0;
    this.lastTimestamp = null;
  }

  tick(timestampMs) {
    if (this.lastTimestamp === null) {
      this.lastTimestamp = timestampMs;
      return 0;
    }

    const elapsed = Math.min(0.25, Math.max(0, (timestampMs - this.lastTimestamp) / 1000));
    this.lastTimestamp = timestampMs;
    this.accumulator += elapsed;

    let updates = 0;
    while (this.accumulator >= this.step) {
      this.update(this.step);
      this.accumulator -= this.step;
      updates += 1;
    }
    return updates;
  }
}
