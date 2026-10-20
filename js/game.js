window.G = window.G || {};

G.Game = (() => {
  let canvas;
  let ctx;
  let player;
  let lastTime = 0;
  let dpr = 1;

  function init() {
    canvas = document.getElementById('game');
    if (!canvas) throw new Error('Missing #game canvas');

    ctx = canvas.getContext('2d', { alpha: false });
    ctx.imageSmoothingEnabled = false;

    player = new G.Player();

    resize();
    G.Camera.snapTo(player);

    addEventListener('resize', resize);
    lastTime = performance.now();
    requestAnimationFrame(loop);
  }

  function resize() {
    const width = canvas.clientWidth;
    const height = canvas.clientHeight;
    dpr = Math.min(G.Config.maxDpr, window.devicePixelRatio || 1);

    canvas.width = Math.max(1, Math.round(width * dpr));
    canvas.height = Math.max(1, Math.round(height * dpr));
    ctx.imageSmoothingEnabled = false;

    G.Camera.resize(width, height, dpr);
  }

  function loop(now) {
    requestAnimationFrame(loop);

    const elapsed = Math.max(0, (now - lastTime) / 1000);
    const dt = Math.min(G.Config.maxDelta, elapsed || 0);
    lastTime = now;

    update(dt);
    draw();
  }

  function update(dt) {
    G.Movement.updatePlayer(player, dt);
    player.update(dt);
    G.Camera.follow(player, dt);
  }

  function draw() {
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.fillStyle = '#151719';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    G.Camera.apply(ctx);
    drawMirGrid();
    player.draw(ctx);

    if (G.Config.debug) drawDebug();
  }

  function drawMirGrid() {
    const cw = G.Config.mirCellWidth;
    const ch = G.Config.mirCellHeight;
    const left = G.Camera.left();
    const top = G.Camera.top();
    const right = left + G.Camera.width;
    const bottom = top + G.Camera.height;

    ctx.strokeStyle = '#24282b';
    ctx.lineWidth = 1 / G.Camera.scale;
    ctx.beginPath();

    for (let x = Math.floor(left / cw) * cw; x <= right + cw; x += cw) {
      ctx.moveTo(x, top - ch);
      ctx.lineTo(x, bottom + ch);
    }

    for (let y = Math.floor(top / ch) * ch; y <= bottom + ch; y += ch) {
      ctx.moveTo(left - cw, y);
      ctx.lineTo(right + cw, y);
    }

    ctx.stroke();

    ctx.strokeStyle = '#4b5054';
    ctx.beginPath();
    ctx.moveTo(-12, 0);
    ctx.lineTo(12, 0);
    ctx.moveTo(0, -12);
    ctx.lineTo(0, 12);
    ctx.stroke();
  }

  function drawDebug() {
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.fillStyle = '#f1f1f1';
    ctx.font = '12px monospace';
    ctx.textAlign = 'left';
    ctx.fillText('WASD / arrows', 12, 20);
    ctx.fillText(`pos ${player.x.toFixed(1)}, ${player.y.toFixed(1)}`, 12, 38);
    ctx.fillText(`dir ${player.direction}  action ${player.action}`, 12, 56);
    ctx.fillText(`MIR frame ${player.animator.logicalFrame()}`, 12, 74);
  }

  return Object.freeze({
    init,
    get player() {
      return player;
    }
  });
})();

addEventListener('DOMContentLoaded', () => G.Game.init(), { once: true });
