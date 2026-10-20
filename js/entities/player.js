window.G = window.G || {};

G.Player = class Player {
  constructor({
    x = 0,
    y = 0,
    speed = G.Config.playerSpeed,
    bodyManifest = 'assets/players/warrior/male/armour_01/manifest.json'
  } = {}) {
    this.x = x;
    this.y = y;
    this.speed = speed;
    this.direction = G.MirDirection.Down;
    this.action = G.MirAnimation.Standing;
    this.moving = false;
    this.animator = new G.MirAnimator();
    this.animator.setDirection(this.direction);

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
      }
    } catch (error) {
      if (loadId !== this._bodyLoadId) return;
      this.assetState = 'error';
      console.error(error);
    }
  }

  setAction(action) {
    if (this.action === action) return;
    this.action = action;
    this.animator.setAction(action);
  }

  update(dt) {
    this.animator.setDirection(this.direction);
    this.animator.update(dt);
  }

  draw(ctx) {
    const logicalFrame = this.animator.logicalFrame();
    if (this.bodySprites && this.assetState === 'ready' && this.bodySprites.draw(ctx, logicalFrame, this.x, this.y)) {
      return;
    }

    this.drawDiagnostic(ctx, logicalFrame);
  }

  drawDiagnostic(ctx, logicalFrame) {
    ctx.save();
    ctx.translate(this.x, this.y);

    ctx.fillStyle = this.assetState === 'error' ? '#b94a48' : '#d9d9d9';
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

    ctx.fillStyle = '#111';
    ctx.font = '11px monospace';
    ctx.textAlign = 'center';
    ctx.fillText(String(logicalFrame), 0, 12);
    ctx.restore();
  }
};
