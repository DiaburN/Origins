window.G = window.G || {};

G.Math = Object.freeze({
  clamp(value, min, max) {
    return Math.max(min, Math.min(max, value));
  },

  damp(current, target, lambda, dt) {
    return current + (target - current) * (1 - Math.exp(-lambda * dt));
  },

  normalize(x, y) {
    const length = Math.hypot(x, y);
    return length > 0 ? [x / length, y / length] : [0, 0];
  }
});
