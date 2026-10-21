window.G = window.G || {};

G.Player = class Player {
  constructor({
    x = 0,
    y = 0,
    speed = G.Config.playerSpeed,
    bodyManifest = 'assets/players/human/common/male/base_m001/manifest.json'
  } = {}) {
    this.x = x;
    this.y = y;
    this.speed = speed;
    this.direction = G.MirDirection.Down;
    this.action = G.MirAnimation.Standing;
    this.moving = false;

    this.animator = new G.MirAnimator();
    this.animator.setDirection(this.direction);
    this.state = new G.PlayerStateMachine(this);

    this.bodyManifest = bodyManifest;
    this.bodySprites = null;
    this.assetState = 'loading';
    this._bodyLoadId = 0;
    this.equipBody(bodyManifest);
  }

  async equipBody(manifestPath) {
    const loadId = ++this._bodyLoadId;
    this.bodyManifest = manifestPath;
    this.bodySprites = null;
    this.assetState = 'loading';

    try {
      const sprites = await G.MirSprites.load(manifestPath);
      if (loadId !== this._bodyLoadId) return;
      this.bodySprites = sprites;
      this.assetState = sprites.manifest.ready === false ? 'waiting-assets' : 'ready';

      if (this.assetState === 'ready') {
        sprites.preloadAction(G.MirAnimation.Standing);
        sprites.preloadAction(G.MirAnimation.Walking);
        sprites.preloadAction(G.MirAnimation.Running);
      }
    } catch (error) {
      if (loadId !== this._bodyLoadId) return;
      this.assetState = 'error';
      console.error(error);
    }
  }

  canMove() {
    return this.state.canMove();
  }

  attack(animation = G.MirAnimation.Combat3) {
    return this.state.attack(animation);
  }

  spell(animation = G.MirAnimation.Combat1) {
    return this.state.spell(animation);
  }

  struck() {
    return this.state.struck();
  }

  pushed() {
    return this.state.pushed();
  }

  die() {
    return this.state.die();
  }

  revive() {
    this.state.revive();
  }

  update(dt) {
    this.animator.setDirection(this.direction);
    this.animator.update(dt);
    this.state.update();
  }

  draw(ctx) {
    const logicalFrame = this.animator.logicalFrame();

    // MIR libraries draw relative to the top-left of the logical 48x32 cell.
    // ORIGINS stores the entity position at the centre of that cell so movement
    // can remain continuous; translate back to the MIR origin only for rendering.
    const drawOriginX = this.x - G.Config.mirCellWidth / 2;
    const drawOriginY = this.y - G.Config.mirCellHeight / 2;

    if (
      this.bodySprites &&
      this.assetState === 'ready' &&
      this.bodySprites.draw(ctx, logicalFrame, drawOriginX, drawOriginY)
    ) {
      return;
    }

    this.drawDiagnostic(ctx, logicalFrame);
  }

  drawDiagnostic(ctx, logicalFrame) {
    ctx.save();
    ctx.translate(this.x, this.y);

    if (this.state.dead) ctx.fillStyle = '#6d6d6d';
    else if (this.state.locked) ctx.fillStyle = '#d6a858';
    else if (this.assetState === 'error') ctx.fillStyle = '#b94a48';
    else ctx.fillStyle = '#d9d9d9';

    ctx.beginPath();
    ctx.ellipse(0, -20, 11, 19, 0, 0, Math.PI * 2);
    ctx.fill();

    const angle = (this.direction - 2) * (Math.PI / 4);
    ctx.strokeStyle = '#111';
    ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.moveTo(0, -20);
    ctx.lineTo(Math.cos(angle) * 18, -20 + Math.sin(angle) * 18);
    ctx.stroke();

    ctx.fillStyle = '#f1f1f1';
    ctx.font = '10px monospace';
    ctx.textAlign = 'center';
    ctx.fillText(this.state.animation, 0, 10);
    ctx.fillText(String(logicalFrame), 0, 22);
    ctx.restore();
  }
};
