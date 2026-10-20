window.G = window.G || {};

// Numeric order kept compatible with Zircon / Legend of Mir 3.
G.MirDirection = Object.freeze({
  Up: 0,
  UpRight: 1,
  Right: 2,
  DownRight: 3,
  Down: 4,
  DownLeft: 5,
  Left: 6,
  UpLeft: 7
});

G.MirAnimation = Object.freeze({
  Standing: 'standing',
  Walking: 'walking',
  Running: 'running'
});

// Logical frame layout from Zircon FrameSet.Players.
// Assets are intentionally not coupled to these definitions.
G.MirPlayerFrames = Object.freeze({
  standing: Object.freeze({ start: 0, count: 4, offset: 10, frameMs: 500 }),
  walking: Object.freeze({ start: 80, count: 6, offset: 10, frameMs: 100 }),
  running: Object.freeze({ start: 160, count: 6, offset: 10, frameMs: 100 })
});

G.directionFromVector = function directionFromVector(x, y, fallback = G.MirDirection.Down) {
  if (x === 0 && y === 0) return fallback;
  const octant = Math.round(Math.atan2(y, x) / (Math.PI / 4));
  return (octant + 2 + 8) % 8;
};

G.MirAnimator = class MirAnimator {
  constructor(definitions = G.MirPlayerFrames) {
    this.definitions = definitions;
    this.action = G.MirAnimation.Standing;
    this.direction = G.MirDirection.Down;
    this.index = 0;
    this.elapsedMs = 0;
  }

  setAction(action) {
    if (this.action === action) return;
    if (!this.definitions[action]) throw new Error(`Unknown MIR animation: ${action}`);
    this.action = action;
    this.index = 0;
    this.elapsedMs = 0;
  }

  setDirection(direction) {
    if (direction < 0 || direction > 7) return;
    this.direction = direction;
  }

  update(dt) {
    const def = this.definitions[this.action];
    this.elapsedMs += dt * 1000;
    while (this.elapsedMs >= def.frameMs) {
      this.elapsedMs -= def.frameMs;
      this.index = (this.index + 1) % def.count;
    }
  }

  logicalFrame() {
    const def = this.definitions[this.action];
    return def.start + def.offset * this.direction + this.index;
  }
};
