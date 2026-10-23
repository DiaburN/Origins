window.G = window.G || {};

G.IngameUI = (() => {
  const PANEL_WIDTH = 1024;
  const PANEL_HEIGHT = 68;

  const BUTTONS = Object.freeze([
    { id: 'character', label: 'Personaje', x: 650, y: 23, w: 36, h: 34 },
    { id: 'inventory', label: 'Bolsa', x: 689, y: 23, w: 36, h: 34 },
    { id: 'magic', label: 'Magias', x: 728, y: 23, w: 36, h: 34 },
    { id: 'quest', label: 'Misiones', x: 767, y: 23, w: 36, h: 34 },
    { id: 'mail', label: 'Correo', x: 806, y: 23, w: 36, h: 34 },
    { id: 'belt', label: 'Cinturón', x: 845, y: 23, w: 36, h: 34 },
    { id: 'group', label: 'Grupo', x: 884, y: 23, w: 36, h: 34 },
    { id: 'menu', label: 'Menú', x: 923, y: 23, w: 36, h: 34 },
    { id: 'store', label: 'Tienda', x: 972, y: 16, w: 48, h: 48 }
  ]);

  let currentCharacter = null;
  let initialized = false;
  let visible = false;
  let stats = { hp: 100, maxHp: 100, mp: 75, maxMp: 75, focus: 0, maxFocus: 100, exp: 0, maxExp: 100 };

  const el = id => document.getElementById(id);

  function init() {
    if (initialized) return;
    initialized = true;
    buildPanelHotspots();
    buildMagicWindow();
    bindMinimap();
  }

  function show(character) {
    init();
    currentCharacter = character || G.Session.currentCharacter();
    visible = true;
    const shell = el('ingame-ui');
    if (shell) shell.hidden = false;
    refreshCharacterData();
    updateStats();
    updateMinimap();
  }

  function hide() {
    visible = false;
    const shell = el('ingame-ui');
    if (shell) shell.hidden = true;
  }

  function buildPanelHotspots() {
    const panel = el('game-hud');
    if (!panel || panel.querySelector('.panel-hotspot')) return;

    for (const spec of BUTTONS) {
      const button = document.createElement('button');
      button.type = 'button';
      button.className = 'panel-hotspot';
      button.dataset.window = spec.id;
      button.title = spec.label;
      button.setAttribute('aria-label', spec.label);
      button.style.left = `${spec.x}px`;
      button.style.top = `${spec.y}px`;
      button.style.width = `${spec.w}px`;
      button.style.height = `${spec.h}px`;
      button.addEventListener('click', () => {
        if (spec.id === 'magic') toggleWindow('magic');
      });
      panel.appendChild(button);
    }
  }

  function buildMagicWindow() {
    const layer = el('ui-window-layer');
    if (!layer || el('ui-window-magic')) return;

    const section = document.createElement('section');
    section.id = 'ui-window-magic';
    section.className = 'ingame-window magic-window';
    section.hidden = true;
    section.innerHTML = '<div class="ingame-window-body"></div>';
    layer.appendChild(section);
  }

  function toggleWindow(id) {
    if (id !== 'magic') return;

    const character = currentCharacter || G.Session.currentCharacter();
    if (!character || String(character.className).toLowerCase() !== 'wizard') return;

    const windowEl = el('ui-window-magic');
    if (!windowEl) return;

    if (!windowEl.hidden) {
      windowEl.hidden = true;
      return;
    }

    const body = windowEl.querySelector('.ingame-window-body');
    if (body) body.innerHTML = G.MagicUI?.render?.() || '';
    windowEl.hidden = false;
  }

  function closeWindow(id) {
    const windowEl = el(`ui-window-${id}`);
    if (windowEl) windowEl.hidden = true;
  }

  function refreshCharacterData() {
    const character = currentCharacter || G.Session.currentCharacter();
    if (!character) return;

    const classLabel = el('panel-class');
    const levelLabel = el('panel-level');
    if (classLabel) classLabel.textContent = character.className || '';
    if (levelLabel) levelLabel.textContent = String(character.level ?? '');
  }

  function setStats(next = {}) {
    stats = { ...stats, ...next };
    updateStats();
  }

  function updateStats() {
    setBar('hud-hp-fill', stats.hp, stats.maxHp, 220);
    setBar('hud-mp-fill', stats.mp, stats.maxMp, 220);
    setBar('hud-focus-fill', stats.focus, stats.maxFocus, 220);
    setBar('hud-exp-fill', stats.exp, stats.maxExp, 980);

    const hp = el('hud-hp-text');
    const mp = el('hud-mp-text');
    const focus = el('hud-focus-text');
    if (hp) hp.textContent = `${stats.hp}/${stats.maxHp}`;
    if (mp) mp.textContent = `${stats.mp}/${stats.maxMp}`;
    if (focus) focus.textContent = stats.maxFocus > 0 ? `${stats.focus}/${stats.maxFocus}` : '';
  }

  function setBar(id, value, max, fullWidth) {
    const node = el(id);
    if (!node) return;
    const percent = max > 0 ? Math.max(0, Math.min(1, value / max)) : 0;
    node.style.width = `${Math.round(fullWidth * percent)}px`;
  }

  function bindMinimap() {
    const sizeButton = el('minimap-size');
    const opacityButton = el('minimap-opacity');
    const bigButton = el('minimap-bigmap');
    const box = el('minimap-box');
    const frame = el('minimap-frame');

    if (sizeButton) {
      sizeButton.addEventListener('click', () => {
        if (!box || !frame) return;
        box.classList.toggle('is-large');
        frame.src = box.classList.contains('is-large')
          ? 'assets/ui/zircon/minimap-frame-300.webp'
          : 'assets/ui/zircon/minimap-frame-200.webp';
      });
    }

    if (opacityButton) {
      opacityButton.addEventListener('click', () => box?.classList.toggle('is-transparent'));
    }

    if (bigButton) {
      bigButton.disabled = true;
      bigButton.title = 'Pendiente de MiniMap.Zl';
    }
  }

  function updateMinimap() {
    if (!visible) return;

    const manifest = G.MapWorld?.manifest;
    const title = el('minimap-title');
    const image = el('minimap-image');
    const marker = el('minimap-player');

    if (title) {
      title.textContent = manifest?.mapInfo?.playerDescription || manifest?.name || '';
    }

    const minimapRuntime = manifest?.runtime?.minimapImage;
    if (!minimapRuntime) {
      if (image) image.hidden = true;
      if (marker) marker.hidden = true;
      return;
    }

    if (image) {
      const source = G.MapWorld.resolveAsset(minimapRuntime);
      if (image.dataset.src !== source) {
        image.dataset.src = source;
        image.src = source;
      }
      image.hidden = false;
    }

    const map = G.MapWorld?.map;
    const player = G.Game?.player;
    if (!marker || !map || !player) return;

    marker.hidden = false;
    marker.style.left = `${Math.max(0, Math.min(100, (player.x / map.pixelWidth) * 100))}%`;
    marker.style.top = `${Math.max(0, Math.min(100, (player.y / map.pixelHeight) * 100))}%`;
  }

  return Object.freeze({ init, show, hide, toggleWindow, closeWindow, setStats, refreshCharacterData, updateMinimap });
})();

addEventListener('DOMContentLoaded', () => {
  G.IngameUI.init();
  const play = document.getElementById('play-character');
  if (play) play.addEventListener('click', () => setTimeout(() => G.IngameUI.show(G.Session.currentCharacter()), 0));
}, { once: true });
