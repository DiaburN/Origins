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

  const WINDOW_DEFS = Object.freeze({
    character: { title: 'PERSONAJE', className: 'character-window', render: renderCharacter },
    inventory: { title: 'BOLSA', className: 'inventory-window', render: renderInventory },
    magic: { title: 'MAGIAS', className: 'magic-window', render: renderMagic },
    quest: { title: 'MISIONES', className: 'quest-window', render: () => renderListPlaceholder('No hay misiones activas todavía.') },
    mail: { title: 'CORREO', className: 'mail-window', render: () => renderListPlaceholder('No hay mensajes. El correo se conectará al servidor más adelante.') },
    belt: { title: 'CINTURÓN', className: 'belt-window', render: renderBelt },
    group: { title: 'GRUPO', className: 'group-window', render: renderGroup },
    menu: { title: 'MENÚ', className: 'menu-window', render: renderMenu },
    store: { title: 'TIENDA', className: 'store-window', render: () => renderListPlaceholder('Tienda preparada. El catálogo llegará con la base de datos.') },
    bigmap: { title: 'MAPA', className: 'bigmap-window', render: renderBigMap }
  });

  let currentCharacter = null;
  let initialized = false;
  let visible = false;
  let mapLoopStarted = false;
  let stats = { hp: 100, maxHp: 100, mp: 75, maxMp: 75, focus: 0, maxFocus: 100, exp: 0, maxExp: 100 };

  const el = id => document.getElementById(id);

  function init() {
    if (initialized) return;
    initialized = true;
    buildPanelHotspots();
    buildWindows();
    bindMinimap();
    if (!mapLoopStarted) {
      mapLoopStarted = true;
      requestAnimationFrame(updateLoop);
    }
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
      button.setAttribute('aria-label', spec.label);
      button.title = spec.label;
      button.style.left = `${(spec.x / PANEL_WIDTH) * 100}%`;
      button.style.top = `${(spec.y / PANEL_HEIGHT) * 100}%`;
      button.style.width = `${(spec.w / PANEL_WIDTH) * 100}%`;
      button.style.height = `${(spec.h / PANEL_HEIGHT) * 100}%`;
      button.addEventListener('click', () => toggleWindow(spec.id));
      panel.appendChild(button);
    }
  }

  function buildWindows() {
    const layer = el('ui-window-layer');
    if (!layer || layer.children.length) return;
    for (const [id, def] of Object.entries(WINDOW_DEFS)) {
      const section = document.createElement('section');
      section.id = `ui-window-${id}`;
      section.className = `ingame-window ${def.className}`;
      section.hidden = true;
      section.innerHTML = `
        <header class="ingame-window-title"><span>${def.title}</span><button type="button" class="ingame-window-close" aria-label="Cerrar">×</button></header>
        <div class="ingame-window-body"></div>`;
      section.querySelector('.ingame-window-close').addEventListener('click', () => closeWindow(id));
      layer.appendChild(section);
    }
  }

  function toggleWindow(id) {
    const windowEl = el(`ui-window-${id}`);
    if (!windowEl) return;
    if (!windowEl.hidden) {
      windowEl.hidden = true;
      return;
    }
    renderWindow(id);
    windowEl.hidden = false;
  }

  function closeWindow(id) {
    const windowEl = el(`ui-window-${id}`);
    if (windowEl) windowEl.hidden = true;
  }

  function renderWindow(id) {
    const def = WINDOW_DEFS[id];
    const windowEl = el(`ui-window-${id}`);
    if (!def || !windowEl) return;
    const body = windowEl.querySelector('.ingame-window-body');
    body.innerHTML = def.render();
  }

  function refreshCharacterData() {
    const character = currentCharacter || G.Session.currentCharacter();
    if (!character) return;
    const name = el('panel-character-name');
    const classLabel = el('panel-class');
    const level = el('panel-level');
    if (name) name.textContent = character.name;
    if (classLabel) classLabel.textContent = character.className;
    if (level) level.textContent = `Nv ${character.level}`;
    for (const id of ['character', 'inventory', 'magic']) {
      const windowEl = el(`ui-window-${id}`);
      if (windowEl && !windowEl.hidden) renderWindow(id);
    }
  }

  function setStats(next = {}) {
    stats = { ...stats, ...next };
    updateStats();
  }

  function updateStats() {
    setBar('hud-hp-fill', stats.hp, stats.maxHp);
    setBar('hud-mp-fill', stats.mp, stats.maxMp);
    setBar('hud-focus-fill', stats.focus, stats.maxFocus);
    setBar('hud-exp-fill', stats.exp, stats.maxExp);
    const hp = el('hud-hp-text');
    const mp = el('hud-mp-text');
    if (hp) hp.textContent = `${stats.hp}/${stats.maxHp}`;
    if (mp) mp.textContent = `${stats.mp}/${stats.maxMp}`;
  }

  function setBar(id, value, max) {
    const node = el(id);
    if (!node) return;
    const percent = max > 0 ? Math.max(0, Math.min(1, value / max)) : 0;
    node.style.width = `${percent * 100}%`;
  }

  function bindMinimap() {
    const sizeButton = el('minimap-size');
    const opacityButton = el('minimap-opacity');
    const bigButton = el('minimap-bigmap');
    const box = el('minimap-box');
    if (sizeButton) sizeButton.addEventListener('click', () => box?.classList.toggle('is-large'));
    if (opacityButton) opacityButton.addEventListener('click', () => box?.classList.toggle('is-transparent'));
    if (bigButton) bigButton.addEventListener('click', () => toggleWindow('bigmap'));
  }

  function updateLoop() {
    if (visible) updateMinimap();
    requestAnimationFrame(updateLoop);
  }

  function updateMinimap() {
    const map = G.MapWorld?.map;
    const manifest = G.MapWorld?.manifest;
    const player = G.Game?.player;
    const title = el('minimap-title');
    const status = el('minimap-status');
    const marker = el('minimap-player');
    if (title) title.textContent = manifest?.name || '3.map · Inicio';
    if (status) {
      const state = G.MapWorld?.status || 'idle';
      status.textContent = state === 'ready' ? 'Mapa cargado' : state === 'waiting-source' ? '3.map pendiente de runtime' : state;
    }
    if (!marker) return;
    if (map && player) {
      const x = Math.max(2, Math.min(98, (player.x / map.pixelWidth) * 100));
      const y = Math.max(2, Math.min(98, (player.y / map.pixelHeight) * 100));
      marker.style.left = `${x}%`;
      marker.style.top = `${y}%`;
    } else {
      marker.style.left = '50%';
      marker.style.top = '50%';
    }
  }

  function renderCharacter() {
    const character = currentCharacter || G.Session.currentCharacter();
    if (!character) return '<p>Sin personaje seleccionado.</p>';
    return `
      <div class="character-sheet">
        <div class="character-portrait"><strong>${escapeHtml(character.name)}</strong><span>${escapeHtml(character.className)} · Nivel ${character.level}</span></div>
        <div class="character-stats">
          ${statRow('HP', stats.maxHp)}${statRow('MP', stats.maxMp)}${statRow('AC', 5)}${statRow('MAC', 4)}${statRow('DC', 7)}${statRow('MC', 0)}${statRow('SC', 0)}${statRow('Accuracy', 5)}
        </div>
        <div class="equipment-grid">${Array.from({ length: 12 }, (_, i) => `<div class="equipment-slot" title="Equipo ${i + 1}"></div>`).join('')}</div>
      </div>`;
  }

  function statRow(label, value) {
    return `<div class="stat-row"><span>${label}</span><strong>${value}</strong></div>`;
  }

  function renderInventory() {
    return `
      <div class="window-summary">Bolsa · <strong>0 / 40</strong></div>
      <div class="inventory-grid">${Array.from({ length: 40 }, (_, i) => `<button type="button" class="inventory-slot" title="Ranura ${i + 1}"></button>`).join('')}</div>
      <div class="inventory-money">Oro: <strong>0</strong></div>`;
  }

  function renderMagic() {
    return `
      <div class="window-tabs"><button class="is-active" type="button">Magias</button><button type="button">Pasivas</button></div>
      <div class="magic-grid">${Array.from({ length: 16 }, (_, i) => `<button type="button" class="magic-slot"><span>${i + 1}</span></button>`).join('')}</div>
      <p class="window-help">Aquí conectaremos el catálogo real de magias MIR3 y sus niveles.</p>`;
  }

  function renderBelt() {
    return `<div class="belt-grid">${Array.from({ length: 6 }, (_, i) => `<button type="button" class="belt-slot"><span>${i + 1}</span></button>`).join('')}</div><p class="window-help">Accesos rápidos para pociones, teleports y consumibles.</p>`;
  }

  function renderGroup() {
    return `<div class="group-empty"><strong>Sin grupo</strong><span>Invitaciones, miembros y reparto de loot se conectarán al servidor.</span><button type="button" disabled>CREAR GRUPO</button></div>`;
  }

  function renderMenu() {
    return `<div class="menu-list"><button type="button" disabled>Opciones</button><button type="button" disabled>Atajos</button><button type="button" disabled>Volver a selección</button><button type="button" disabled>Salir</button></div><p class="window-help">Estructura lista; activaremos cada acción cuando exista servidor/estado persistente.</p>`;
  }

  function renderBigMap() {
    return `<div class="big-map-canvas"><div class="big-map-grid"></div><div class="big-map-player"></div><span>3.map · mapa grande</span></div>`;
  }

  function renderListPlaceholder(message) {
    return `<div class="list-placeholder">${escapeHtml(message)}</div>`;
  }

  function escapeHtml(value) {
    return String(value ?? '').replace(/[&<>'"]/g, char => ({ '&':'&amp;', '<':'&lt;', '>':'&gt;', "'":'&#39;', '"':'&quot;' })[char]);
  }

  return Object.freeze({ init, show, hide, toggleWindow, closeWindow, setStats, refreshCharacterData });
})();

addEventListener('DOMContentLoaded', () => {
  G.IngameUI.init();
  const play = document.getElementById('play-character');
  if (play) play.addEventListener('click', () => setTimeout(() => G.IngameUI.show(G.Session.currentCharacter()), 0));
}, { once: true });
