window.G = window.G || {};

G.Input = (() => {
  const down = new Set();

  const moveKeys = Object.freeze({
    up: ['keyw', 'arrowup'],
    down: ['keys', 'arrowdown'],
    left: ['keya', 'arrowleft'],
    right: ['keyd', 'arrowright']
  });

  function keyCode(event) {
    return String(event.code || event.key || '').toLowerCase();
  }

  addEventListener('keydown', event => {
    const code = keyCode(event);
    down.add(code);
    if (code.startsWith('arrow')) event.preventDefault();
  }, { passive: false });

  addEventListener('keyup', event => down.delete(keyCode(event)));
  addEventListener('blur', () => down.clear());

  function held(keys) {
    return keys.some(key => down.has(key));
  }

  return Object.freeze({
    axis() {
      let x = 0;
      let y = 0;
      if (held(moveKeys.left)) x -= 1;
      if (held(moveKeys.right)) x += 1;
      if (held(moveKeys.up)) y -= 1;
      if (held(moveKeys.down)) y += 1;
      return G.Math.normalize(x, y);
    }
  });
})();
