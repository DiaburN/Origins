window.G = window.G || {};

G.Player = class Player {
  constructor({ x = 0, y = 0, speed = G.Config.playerSpeed } = {}) {
    this.x = x;
    this.y = y;
    this.speed = speed;
    this.direction = G.MirDirection.Down;
    this.action = G.MirAnimation.Standing;
    this.moving = false;
    this.animator = new G.MirAnimator();
    this.animator.setDirection(this.direction);
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
    // Temporary diagnostic renderer. It will be replaced by the MIR asset renderer,
    // while position, direction, action and logical frame remain unchanged.
    ctx.save();
    ctx.translate(this.x, this.y);

    ctx.fillStyle = '#d9d9d9';
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
    ctx.fillText(String(this.animator.logicalFrame()), 0, 12);
    ctx.restore();
  }
};
