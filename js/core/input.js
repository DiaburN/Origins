window.G = window.G || {};

G.Input = (() => {
  const down = new Set();
  const pressed = new Set();

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
    if (!down.has(code)) pressed.add(code);
    down.add(code);
    if (code.startsWith('arrow') || code === 'space') event.preventDefault();
  }, { passive: false });

  addEventListener('keyup', event => down.delete(keyCode(event)));
  addEventListener('blur', () => {
    down.clear();
    pressed.clear();
  });

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
    },

    isHeld(...keys) {
      return held(keys.map(key => String(key).toLowerCase()));
    },

    consume(...keys) {
      for (const key of keys) {
        const code = String(key).toLowerCase();
        if (!pressed.has(code)) continue;
        pressed.delete(code);
        return true;
      }
      return false;
    }
  });
})();
