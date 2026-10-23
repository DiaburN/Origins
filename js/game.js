window.G = window.G || {};

G.Game = (() => {
  const MAP_MANIFEST = 'assets/maps/start-3/manifest.json';

  let canvas;
  let ctx;
  let player;
  let lastTime = 0;
  let dpr = 1;
  let debugCombat = 3;
  let initialized = false;

  function init() {
    if (initialized) return;
    initialized = true;

    canvas = document.getElementById('game');
    if (!canvas) throw new Error('Missing #game canvas');

    ctx = canvas.getContext('2d', { alpha: false });
    ctx.imageSmoothingEnabled = false;

    player = new G.Player();

    resize();
    G.Camera.snapTo(player);

    G.MapWorld.load(MAP_MANIFEST).then(async loadedMap => {
      if (!loadedMap) return;

      const renderPack = G.MapWorld.manifest?.runtime?.renderPack;
      if (renderPack) {
        await G.MirMapRenderer.load(G.MapWorld.resolveAsset(renderPack));
      }

      const spawn = G.MapWorld.findSpawn();
      if (!spawn) return;

      player.x = spawn.x;
      player.y = spawn.y;
      G.Camera.snapTo(player);
    });

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
    draw(now);
  }

  function update(dt) {
    if (G.Config.debug) updateDebugActions();
    G.Movement.updatePlayer(player, dt);
    player.update(dt);
    G.Camera.follow(player, dt);
  }

  function updateDebugActions() {
    if (G.Input.consume('keyq')) debugCombat = debugCombat <= 1 ? 15 : debugCombat - 1;
    if (G.Input.consume('keye')) debugCombat = debugCombat >= 15 ? 1 : debugCombat + 1;

    if (G.Input.consume('space')) player.attack(G.MirAnimation[`Combat${debugCombat}`]);
    if (G.Input.consume('digit1')) player.spell(G.MirAnimation.Combat1);
    if (G.Input.consume('digit2')) player.spell(G.MirAnimation.Combat2);
    if (G.Input.consume('keyh')) player.state.harvest();
    if (G.Input.consume('keyj')) player.struck();
    if (G.Input.consume('keyp')) player.pushed();
    if (G.Input.consume('keyk')) player.die();
    if (G.Input.consume('keyr')) player.revive();
    if (G.Input.consume('keyc')) player.state.setCreeping(!player.state.creeping);
    if (G.Input.consume('keym')) player.state.setMounted(!player.state.mounted);
    if (G.Input.consume('keyv')) { if (!player.state.endChannel()) player.state.beginChannel(); }
    if (G.Input.consume('keyb')) { if (!player.state.endDragonRepulse()) player.state.beginDragonRepulse(); }
    if (G.Input.consume('keyf')) { if (!player.state.reelFishing()) player.state.beginFishing(); }
    if (G.Input.consume('keyt')) { if (!player.state.stopTaming()) player.state.beginTaming(); }
  }

  function draw(now) {
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.fillStyle = '#000';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    G.Camera.apply(ctx);

    const map = G.MapWorld.map;
    let playerDrawn = false;

    if (map) {
      const playerRow = map.worldToCell(player.x, player.y).y;
      G.MirMapRenderer.draw(ctx, map, now, row => {
        if (!playerDrawn && row === playerRow && player.assetState === 'ready') {
          player.draw(ctx);
          playerDrawn = true;
        }
      });
    }

    if (!playerDrawn && player.assetState === 'ready') player.draw(ctx);
    if (G.Config.debug) drawDebug();
  }

  function drawDebug() {
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.fillStyle = '#f1f1f1';
    ctx.font = '12px monospace';
    ctx.textAlign = 'left';

    const loadedMap = G.MapWorld.map;
    const mapText = loadedMap
      ? `${G.MapWorld.status} ${loadedMap.width}x${loadedMap.height}`
      : G.MapWorld.status;

    const lines = [
      'WASD move | Shift run | C creep | M mount',
      `Q/E choose Combat${debugCombat} | Space play | 1/2 spell`,
      'H harvest | J struck | P pushed | K die | R revive',
      'V channel | B dragon repulse | F fishing | T taming',
      `map ${mapText} | renderer ${G.MirMapRenderer.status}`,
      `pos ${player.x.toFixed(1)}, ${player.y.toFixed(1)} dir ${player.direction}`,
      `state ${player.state.action} anim ${player.state.animation}`,
      `body ${player.assetState}`
    ];

    for (let i = 0; i < lines.length; i++) ctx.fillText(lines[i], 12, 20 + i * 18);
  }

  return Object.freeze({
    init,
    get player() { return player; }
  });
})();
