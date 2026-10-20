window.G = window.G || {};

G.Camera = {
  x: 0,
  y: 0,
  width: 0,
  height: 0,
  cssWidth: 0,
  cssHeight: 0,
  scale: 1,
  dpr: 1,

  resize(cssWidth, cssHeight, dpr = 1) {
    this.cssWidth = cssWidth;
    this.cssHeight = cssHeight;
    this.dpr = dpr;
    this.scale = Math.min(
      cssWidth / G.Config.viewWidth,
      cssHeight / G.Config.minViewHeight
    );
    this.width = cssWidth / this.scale;
    this.height = cssHeight / this.scale;
  },

  snapTo(target) {
    this.x = target.x;
    this.y = target.y;
  },

  follow(target, dt) {
    this.x = G.Math.damp(this.x, target.x, G.Config.cameraFollow, dt);
    this.y = G.Math.damp(this.y, target.y, G.Config.cameraFollow, dt);
  },

  left() {
    return this.x - this.width / 2;
  },

  top() {
    return this.y - this.height / 2;
  },

  apply(ctx) {
    const k = this.scale * this.dpr;
    const tx = (this.cssWidth / 2 - this.x * this.scale) * this.dpr;
    const ty = (this.cssHeight / 2 - this.y * this.scale) * this.dpr;
    ctx.setTransform(k, 0, 0, k, Math.round(tx), Math.round(ty));
  }
};
