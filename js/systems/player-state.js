window.G = window.G || {};

G.PlayerState = Object.freeze({
  Priority: Object.freeze({
    Locomotion: 0,
    Action: 20,
    Struck: 40,
    Pushed: 50,
    Die: 90,
    Dead: 100
  })
});

G.PlayerStateMachine = class PlayerStateMachine {
  constructor(player) {
    this.player = player;
    this.action = G.MirAction.Standing;
    this.animation = G.MirAnimation.Standing;
    this.priority = G.PlayerState.Priority.Locomotion;
    this.locked = false;
    this.dead = false;
    this.mounted = false;
    this.creeping = false;
    this.chain = null;
  }

  canMove() {
    return !this.dead && !this.locked;
  }

  setMounted(value) {
    if (this.dead || this.locked) return false;
    this.mounted = value === true;
    if (this.mounted) this.creeping = false;
    return true;
  }

  setCreeping(value) {
    if (this.dead || this.locked || this.mounted) return false;
    this.creeping = value === true;
    return true;
  }

  setLocomotion({ moving, running = false, creepFast = true } = {}) {
    if (!this.canMove()) return false;

    const action = moving ? G.MirAction.Moving : G.MirAction.Standing;
    let animation;

    if (this.mounted) {
      animation = moving
        ? (running ? G.MirAnimation.HorseRunning : G.MirAnimation.HorseWalking)
        : G.MirAnimation.HorseStanding;
    } else if (this.creeping) {
      animation = moving
        ? (creepFast ? G.MirAnimation.CreepWalkFast : G.MirAnimation.CreepWalkSlow)
        : G.MirAnimation.CreepStanding;
    } else {
      animation = moving
        ? (running ? G.MirAnimation.Running : G.MirAnimation.Walking)
        : G.MirAnimation.Standing;
    }

    this._enter(action, animation, {
      priority: G.PlayerState.Priority.Locomotion,
      locked: false,
      restart: false,
      chain: null
    });
    return true;
  }

  play(action, animation, {
    priority = G.PlayerState.Priority.Action,
    force = false,
    chain = null,
    restart = true
  } = {}) {
    if (this.dead && action !== G.MirAction.Dead) return false;

    // A lower-priority action can never interrupt a stronger state. Equal
    // priority is also blocked unless explicitly forced for controlled chains
    // such as ChannellingMiddle -> ChannellingEnd.
    if (this.locked && priority < this.priority) return false;
    if (this.locked && priority === this.priority && !force) return false;

    this._enter(action, animation, {
      priority,
      locked: true,
      restart,
      chain
    });
    return true;
  }

  attack(animation = G.MirAnimation.Combat3) {
    return this.play(G.MirAction.Attack, animation);
  }

  spell(animation = G.MirAnimation.Combat1) {
    return this.play(G.MirAction.Spell, animation);
  }

  harvest() {
    return this.play(G.MirAction.Harvest, G.MirAnimation.Harvest);
  }

  struck() {
    return this.play(G.MirAction.Struck, G.MirAnimation.Struck, {
      priority: G.PlayerState.Priority.Struck
    });
  }

  pushed() {
    return this.play(G.MirAction.Pushed, G.MirAnimation.Pushed, {
      priority: G.PlayerState.Priority.Pushed
    });
  }

  die() {
    if (this.dead || this.action === G.MirAction.Die) return false;
    return this.play(G.MirAction.Die, G.MirAnimation.Die, {
      priority: G.PlayerState.Priority.Die,
      chain: {
        action: G.MirAction.Dead,
        animation: G.MirAnimation.Dead,
        priority: G.PlayerState.Priority.Dead,
        locked: true,
        dead: true
      }
    });
  }

  revive() {
    this.dead = false;
    this.locked = false;
    this.priority = G.PlayerState.Priority.Locomotion;
    this.chain = null;
    this._enter(G.MirAction.Standing, G.MirAnimation.Standing, {
      priority: G.PlayerState.Priority.Locomotion,
      locked: false,
      restart: true,
      chain: null
    });
  }

  beginChannel() {
    return this.play(G.MirAction.Spell, G.MirAnimation.ChannellingStart, {
      chain: {
        action: G.MirAction.Spell,
        animation: G.MirAnimation.ChannellingMiddle,
        priority: G.PlayerState.Priority.Action,
        locked: true
      }
    });
  }

  endChannel() {
    if (this.animation !== G.MirAnimation.ChannellingMiddle) return false;
    return this.play(G.MirAction.Spell, G.MirAnimation.ChannellingEnd, {
      force: true,
      chain: null
    });
  }

  beginDragonRepulse() {
    return this.play(G.MirAction.Spell, G.MirAnimation.DragonRepulseStart, {
      chain: {
        action: G.MirAction.Spell,
        animation: G.MirAnimation.DragonRepulseMiddle,
        priority: G.PlayerState.Priority.Action,
        locked: true
      }
    });
  }

  endDragonRepulse() {
    if (this.animation !== G.MirAnimation.DragonRepulseMiddle) return false;
    return this.play(G.MirAction.Spell, G.MirAnimation.DragonRepulseEnd, {
      force: true,
      chain: null
    });
  }

  beginFishing() {
    return this.play(G.MirAction.Fishing, G.MirAnimation.FishingCast, {
      chain: {
        action: G.MirAction.Fishing,
        animation: G.MirAnimation.FishingWait,
        priority: G.PlayerState.Priority.Action,
        locked: true
      }
    });
  }

  reelFishing() {
    if (this.animation !== G.MirAnimation.FishingWait) return false;
    return this.play(G.MirAction.Fishing, G.MirAnimation.FishingReel, {
      force: true,
      chain: null
    });
  }

  beginTaming() {
    return this.play(G.MirAction.Taming, G.MirAnimation.TamingCast, {
      chain: {
        action: G.MirAction.Taming,
        animation: G.MirAnimation.TamingWait,
        priority: G.PlayerState.Priority.Action,
        locked: true
      }
    });
  }

  stopTaming() {
    if (this.animation !== G.MirAnimation.TamingWait) return false;
    this._returnToStanding();
    return true;
  }

  update() {
    if (!this.locked || !this.player.animator.isComplete()) return;

    if (this.chain) {
      const next = this.chain;
      this.chain = null;
      this.dead = next.dead === true || this.dead;
      this._enter(next.action, next.animation, {
        priority: next.priority,
        locked: next.locked !== false,
        restart: true,
        chain: next.chain || null
      });
      return;
    }

    if (this.dead || this.action === G.MirAction.Dead) return;
    this._returnToStanding();
  }

  _returnToStanding() {
    this.locked = false;
    this.priority = G.PlayerState.Priority.Locomotion;
    this.chain = null;
    this._enter(G.MirAction.Standing, this._standingAnimation(), {
      priority: G.PlayerState.Priority.Locomotion,
      locked: false,
      restart: true,
      chain: null
    });
  }

  _standingAnimation() {
    if (this.mounted) return G.MirAnimation.HorseStanding;
    if (this.creeping) return G.MirAnimation.CreepStanding;
    return G.MirAnimation.Standing;
  }

  _enter(action, animation, {
    priority,
    locked,
    restart,
    chain
  }) {
    const sameAnimation = this.animation === animation;
    this.action = action;
    this.animation = animation;
    this.priority = priority;
    this.locked = locked;
    this.chain = chain;

    this.player.action = animation;
    this.player.animator.setAction(animation, {
      restart: restart === true || !sameAnimation
    });
  }
};
