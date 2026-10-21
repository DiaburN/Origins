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

// High-level action names from Zircon. These describe intent/state; the
// combat/skill system later chooses the concrete MirAnimation slot.
G.MirAction = Object.freeze({
  Standing: 'standing',
  Moving: 'moving',
  Pushed: 'pushed',
  Attack: 'attack',
  RangeAttack: 'rangeAttack',
  Spell: 'spell',
  Harvest: 'harvest',
  Struck: 'struck',
  Die: 'die',
  Dead: 'dead',
  Show: 'show',
  Hide: 'hide',
  Mount: 'mount',
  Mining: 'mining',
  Fishing: 'fishing',
  Taming: 'taming',
  Idle: 'idle'
});

// Exact player animation names used by Zircon FrameSet.Players.
G.MirAnimation = Object.freeze({
  Standing: 'standing',
  Walking: 'walking',
  CreepStanding: 'creepStanding',
  CreepWalkSlow: 'creepWalkSlow',
  CreepWalkFast: 'creepWalkFast',
  Running: 'running',
  Pushed: 'pushed',
  Combat1: 'combat1',
  Combat2: 'combat2',
  Combat3: 'combat3',
  Combat4: 'combat4',
  Combat5: 'combat5',
  Combat6: 'combat6',
  Combat7: 'combat7',
  Combat8: 'combat8',
  Combat9: 'combat9',
  Combat10: 'combat10',
  Combat11: 'combat11',
  Combat12: 'combat12',
  Combat13: 'combat13',
  Combat14: 'combat14',
  Combat15: 'combat15',
  Harvest: 'harvest',
  Stance: 'stance',
  Struck: 'struck',
  Die: 'die',
  Dead: 'dead',
  HorseStanding: 'horseStanding',
  HorseWalking: 'horseWalking',
  HorseRunning: 'horseRunning',
  HorseStruck: 'horseStruck',
  HorseLeaping: 'horseLeaping',
  DragonRepulseStart: 'dragonRepulseStart',
  DragonRepulseMiddle: 'dragonRepulseMiddle',
  DragonRepulseEnd: 'dragonRepulseEnd',
  ChannellingStart: 'channellingStart',
  ChannellingMiddle: 'channellingMiddle',
  ChannellingEnd: 'channellingEnd',
  FishingCast: 'fishingCast',
  FishingWait: 'fishingWait',
  FishingReel: 'fishingReel',
  TamingCast: 'tamingCast',
  TamingWait: 'tamingWait'
});

// Runtime policy is separate from MIR frame identity.
// loop: locomotion/idles repeat; once: action finishes and holds its final frame;
// hold: a persistent state such as Dead.
function frame(start, count, offset, frameMs, options = {}) {
  return Object.freeze({
    start,
    count,
    offset,
    frameMs,
    mode: options.mode || 'once',
    reversed: options.reversed === true,
    staticSpeed: options.staticSpeed === true,
    delays: Object.freeze(options.delays || {})
  });
}

// Exact logical frame layout/timings from Zircon FrameSet.Players at
// Suprcode/Zircon commit 80d5df21016b2f377d48f14f7dcc2e994b163ff1.
// Direction is always applied as: start + offset * direction + frameIndex.
G.MirPlayerFrames = Object.freeze({
  standing: frame(0, 4, 10, 500, { mode: 'loop' }),
  walking: frame(80, 6, 10, 100, { mode: 'loop' }),
  running: frame(160, 6, 10, 100, { mode: 'loop' }),

  // Assassin/stealth locomotion.
  creepStanding: frame(1680, 4, 10, 500, { mode: 'loop' }),
  creepWalkFast: frame(1760, 6, 10, 100, { mode: 'loop' }),
  creepWalkSlow: frame(1760, 6, 10, 200, { mode: 'loop' }),

  pushed: frame(240, 6, 10, 50, { reversed: true, staticSpeed: true }),
  stance: frame(400, 3, 10, 500, { mode: 'loop' }),
  harvest: frame(480, 2, 10, 300),

  // Zircon combat animation slots. The magic/skill system decides which slot to use.
  combat1: frame(560, 5, 10, 100, { delays: { 1: 200 } }), // projectile spell
  combat2: frame(640, 5, 10, 100, { delays: { 3: 200 } }), // target spell
  combat3: frame(720, 6, 10, 100),                         // default W/W/T attack
  combat4: frame(800, 6, 10, 100),                         // assassin 1H / backhand
  combat5: frame(880, 10, 10, 60),                         // lotus 1H
  combat6: frame(960, 10, 10, 60),                         // blade-storm family
  combat7: frame(1040, 10, 10, 100),                       // kick
  combat8: frame(1120, 6, 10, 50, { staticSpeed: true }),  // dash
  combat9: frame(1200, 10, 10, 100),                       // evasion cast
  combat10: frame(1280, 10, 10, 60),                       // sweet-brier 1H
  combat11: frame(1360, 10, 10, 60),                       // dual-wield default
  combat12: frame(1440, 10, 10, 60),                       // sweet-brier dual wield
  combat13: frame(1520, 6, 10, 100),                       // lotus dual wield
  combat14: frame(1600, 8, 10, 100),                       // summon/puppet family
  combat15: frame(400, 3, 10, 200),

  dragonRepulseStart: frame(1600, 6, 10, 100),
  dragonRepulseMiddle: frame(1605, 1, 10, 1000, { mode: 'loop' }),
  dragonRepulseEnd: frame(1606, 2, 10, 100),

  struck: frame(1840, 3, 10, 100),
  die: frame(1920, 10, 10, 100),
  dead: frame(1929, 1, 10, 1000, { mode: 'hold' }),

  fishingCast: frame(2000, 8, 10, 100),
  fishingWait: frame(2080, 6, 10, 120, { mode: 'loop' }),
  fishingReel: frame(2160, 8, 10, 100),

  horseStanding: frame(2240, 4, 10, 500, { mode: 'loop' }),
  horseWalking: frame(2320, 6, 10, 100, { mode: 'loop' }),
  horseRunning: frame(2400, 6, 10, 100, { mode: 'loop' }),
  horseStruck: frame(2480, 3, 10, 100),
  horseLeaping: frame(2240, 4, 10, 125),

  channellingStart: frame(560, 4, 10, 100),
  channellingMiddle: frame(563, 1, 10, 1000, { mode: 'loop' }),
  channellingEnd: frame(0, 1, 10, 60),

  tamingCast: frame(720, 6, 10, 100),
  tamingWait: frame(725, 1, 10, 100, { mode: 'loop' })
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
    this.completed = false;
  }

  setAction(action, { restart = false } = {}) {
    if (!this.definitions[action]) throw new Error(`Unknown MIR animation: ${action}`);
    if (!restart && this.action === action) return;

    this.action = action;
    this.index = 0;
    this.elapsedMs = 0;
    this.completed = false;
  }

  restart() {
    this.setAction(this.action, { restart: true });
  }

  setDirection(direction) {
    if (direction < 0 || direction > 7) return;
    this.direction = direction;
  }

  currentDefinition() {
    return this.definitions[this.action];
  }

  currentFrameDurationMs() {
    const def = this.currentDefinition();
    return Number(def.delays[this.index] ?? def.frameMs);
  }

  update(dt) {
    const def = this.currentDefinition();
    if (def.mode === 'hold' || this.completed) return;

    this.elapsedMs += dt * 1000;

    while (!this.completed) {
      const delay = this.currentFrameDurationMs();
      if (this.elapsedMs < delay) break;
      this.elapsedMs -= delay;

      if (this.index + 1 < def.count) {
        this.index += 1;
        continue;
      }

      if (def.mode === 'loop') {
        this.index = 0;
        continue;
      }

      this.index = def.count - 1;
      this.elapsedMs = 0;
      this.completed = true;
    }
  }

  isComplete() {
    return this.completed;
  }

  logicalFrame() {
    const def = this.currentDefinition();
    const index = def.reversed ? def.count - 1 - this.index : this.index;
    return def.start + def.offset * this.direction + index;
  }
};
