window.G = window.G || {};

G.IngameUI = (() => {
  const PANEL_WIDTH = 1024;
  const PANEL_HEIGHT = 68;
  const A = G.GameUiAssets || { sheets: {}, sprites: {}, standalone: {} };

  const BUTTONS = Object.freeze([
    { id: 'character', label: 'Personaje', x: 650, y: 23, asset: 'gameinter-82' },
    { id: 'inventory', label: 'Bolsa', x: 689, y: 23, asset: 'gameinter-87' },
    { id: 'magic', label: 'Magias', x: 728, y: 23, asset: 'gameinter-92' },
    { id: 'quest', label: 'Misiones', x: 767, y: 23, asset: 'gameinter-112' },
    { id: 'mail', label: 'Correo', x: 806, y: 23, asset: 'gameinter-97' },
    { id: 'belt', label: 'Cinturón', x: 845, y: 23, asset: 'gameinter-107' },
    { id: 'group', label: 'Grupo', x: 884, y: 23, asset: 'gameinter-102' },
    { id: 'menu', label: 'Menú', x: 923, y: 23, asset: 'gameinter-117' },
    { id: 'store', label: 'Tienda', x: 972, y: 16, asset: 'gameinter-122' }
  ]);

  const WINDOW_DEFS = Object.freeze({
    character: { art: 'interface-110', className: 'character-window', render: renderCharacter },
    inventory: { art: 'interface-130', className: 'inventory-window', render: renderInventory },
    magic: { className: 'magic-window', render: renderMagic },
    quest: { art: 'interface-291', className: 'quest-window', render: renderQuest },
    mail: { art: 'interface-200', className: 'mail-window', render: renderMail },
    belt: { className: 'belt-window', render: renderBelt },
    group: { art: 'interface-240', className: 'group-window', render: renderGroup },
    menu: { art: 'interface-279', className: 'menu-window', render: renderMenu },
    store: { art: 'interface-310', className: 'store-window', render: renderStore }
  });

  let currentCharacter = null;
  let initialized = false;
  let visible = false;
  let stats = {
    hp: 100, maxHp: 100,
    mp: 75, maxMp: 75,
    focus: 0, maxFocus: 100,
    exp: 0, maxExp: 100,
    fp: 0, cp: 0, ac: 5, dc: 7, mac: 4, mc: 0, sc: 0
  };

  const el = id => document.getElementById(id);

  function init() {
    if (initialized) return;
    initialized = true;
    buildPanel();
    buildWindows();
    bindMinimap();
    addEventListener('resize', layoutWindows);
  }

  function show(character) {
    init();
    currentCharacter = character || G.Session.currentCharacter();
    visible = true;
    const shell = el('ingame-ui');
    if (shell) shell.hidden = false;
    refreshCharacterData();
    updateStats();
    layoutWindows();
    updateMinimap();
  }

  function hide() {
    visible = false;
    const shell = el('ingame-ui');
    if (shell) shell.hidden = true;
  }

  function buildPanel() {
    const panel = el('game-hud');
    if (!panel || panel.querySelector('.panel-button')) return;

    for (const spec of BUTTONS) {
      const s = A.sprites[spec.asset];
      if (!s) continue;
      const button = document.createElement('button');
      button.type = 'button';
      button.className = 'panel-button';
      button.dataset.window = spec.id;
      button.title = spec.label;
      button.setAttribute('aria-label', spec.label);
      button.style.left = `${spec.x}px`;
      button.style.top = `${spec.y}px`;
      button.style.width = `${s.w}px`;
      button.style.height = `${s.h}px`;
      button.appendChild(spriteNode(spec.asset, 'panel-button-art'));
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
      section.dataset.windowId = id;
      section.hidden = true;

      if (def.art) {
        section.appendChild(spriteNode(def.art, 'window-background-art'));
      } else if (id === 'belt') {
        section.appendChild(spriteNode('belt-frame', 'belt-frame-art'));
      }

      const body = document.createElement('div');
      body.className = 'ingame-window-body';
      section.appendChild(body);
      layer.appendChild(section);

      if (id !== 'magic' && id !== 'belt') {
        const close = document.createElement('button');
        close.type = 'button';
        close.className = 'zircon-real-close';
        close.setAttribute('aria-label', 'Cerrar');
        close.appendChild(spriteNode('interface-15'));
        close.addEventListener('click', () => closeWindow(id));
        section.appendChild(close);
      }

      if (id !== 'magic' && id !== 'belt') enableDrag(section);
    }
  }

  function layoutWindows() {
    const vw = innerWidth;
    const vh = innerHeight;

    setDefaultPosition('character', 0, 0);
    setDefaultPosition('inventory', Math.max(0, vw - 264), 200);
    setDefaultPosition('magic', Math.max(0, vw - 420), 0);
    setDefaultPosition('quest', Math.max(0, Math.round((vw - 732) / 2)), Math.max(0, Math.round((vh - 480) / 2)));
    setDefaultPosition('mail', Math.max(0, vw - 296), 0);
    setDefaultPosition('belt', Math.max(0, Math.round((vw - 239) / 2)), Math.max(0, vh - 68 - 58));
    setDefaultPosition('group', 0, 0);
    setDefaultPosition('menu', Math.max(0, vw - 152), Math.max(0, vh - 260 - 68));
    setDefaultPosition('store', Math.max(0, Math.round((vw - 800) / 2)), Math.max(0, Math.round((vh - 515) / 2)));
  }

  function setDefaultPosition(id, x, y) {
    const node = el(`ui-window-${id}`);
    if (!node || node.dataset.userMoved === '1') return;
    node.style.left = `${x}px`;
    node.style.top = `${y}px`;
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
    windowEl.style.zIndex = String(nextWindowZ());
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
    if (body) body.innerHTML = def.render();
    bindWindowContent(id, windowEl);
  }

  let zCounter = 50;
  function nextWindowZ() { return ++zCounter; }

  function enableDrag(windowEl) {
    let drag = null;
    windowEl.addEventListener('pointerdown', event => {
      if (event.button !== 0) return;
      if (event.target.closest('button,input,select,textarea,.window-interactive')) return;
      if (event.clientY > windowEl.getBoundingClientRect().top + 34) return;
      const rect = windowEl.getBoundingClientRect();
      drag = { dx: event.clientX - rect.left, dy: event.clientY - rect.top };
      windowEl.dataset.userMoved = '1';
      windowEl.style.zIndex = String(nextWindowZ());
      windowEl.setPointerCapture?.(event.pointerId);
    });
    windowEl.addEventListener('pointermove', event => {
      if (!drag) return;
      const maxX = Math.max(0, innerWidth - windowEl.offsetWidth);
      const maxY = Math.max(0, innerHeight - windowEl.offsetHeight);
      windowEl.style.left = `${Math.max(0, Math.min(maxX, event.clientX - drag.dx))}px`;
      windowEl.style.top = `${Math.max(0, Math.min(maxY, event.clientY - drag.dy))}px`;
    });
    const stop = () => { drag = null; };
    windowEl.addEventListener('pointerup', stop);
    windowEl.addEventListener('pointercancel', stop);
  }

  function bindWindowContent(id, windowEl) {
    if (id === 'magic') {
      windowEl.querySelector('[data-original-magic-close]')?.addEventListener('click', () => closeWindow('magic'));
    }

    if (id === 'mail') {
      windowEl.querySelectorAll('[data-mail-tab]').forEach(button => {
        button.addEventListener('click', () => {
          const key = button.dataset.mailTab;
          const backgrounds = { friends: 'interface-201', received: 'interface-202', send: 'interface-203', blocked: 'interface-204' };
          const bg = windowEl.querySelector('.mail-tab-background');
          if (bg && backgrounds[key]) applySprite(bg, backgrounds[key]);
          syncTabs(windowEl, '[data-mail-tab]', button);
        });
      });
    }

    if (id === 'quest') {
      windowEl.querySelectorAll('[data-quest-tab]').forEach(button => {
        button.addEventListener('click', () => {
          const type = button.dataset.questTab;
          const arts = { current: 'interface-291', available: 'interface-291', milestone: 'interface-292', mission: 'interface-293' };
          const bg = windowEl.querySelector('.window-background-art');
          if (bg && arts[type]) applySprite(bg, arts[type]);
          syncTabs(windowEl, '[data-quest-tab]', button);
          windowEl.querySelectorAll('[data-quest-tab]').forEach(b => b.classList.toggle('is-selected', b === button));
        });
      });
    }
  }

  function refreshCharacterData() {
    const character = currentCharacter || G.Session.currentCharacter();
    if (!character) return;
    text('panel-class', character.className || '');
    text('panel-level', String(character.level ?? ''));
    for (const id of ['character', 'inventory', 'magic']) {
      const w = el(`ui-window-${id}`);
      if (w && !w.hidden) renderWindow(id);
    }
  }

  function setStats(next = {}) {
    stats = { ...stats, ...next };
    updateStats();
  }

  function updateStats() {
    setCropBar('hud-hp-fill', stats.hp, stats.maxHp, 220);
    setCropBar('hud-mp-fill', stats.mp, stats.maxMp, 220);
    setCropBar('hud-focus-fill', stats.focus, stats.maxFocus, 220);
    setCropBar('hud-exp-fill', stats.exp, stats.maxExp, 980);
    text('hud-hp-text', `${stats.hp}/${stats.maxHp}`);
    text('hud-mp-text', `${stats.mp}/${stats.maxMp}`);
    text('hud-focus-text', stats.maxFocus > 0 ? `${stats.focus}/${stats.maxFocus}` : '');
    text('panel-fp', String(stats.fp ?? 0));
    text('panel-cp', String(stats.cp ?? 0));
    text('panel-ac', String(stats.ac ?? 0));
    text('panel-dc', String(stats.dc ?? 0));
    text('panel-mac', String(stats.mac ?? 0));
    text('panel-mc', String(stats.mc ?? 0));
    text('panel-sc', String(stats.sc ?? 0));
  }

  function setCropBar(id, value, max, fullWidth) {
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

    sizeButton?.addEventListener('click', () => {
      if (!box || !frame) return;
      box.classList.toggle('is-large');
      frame.src = box.classList.contains('is-large')
        ? 'assets/ui/zircon/minimap-frame-300.webp'
        : 'assets/ui/zircon/minimap-frame-200.webp';
      updateMinimap();
    });

    opacityButton?.addEventListener('click', () => box?.classList.toggle('is-transparent'));

    if (bigButton) {
      bigButton.disabled = true;
      bigButton.title = 'Falta MiniMap.Zl para el mapa 3 / índice 145';
    }
  }

  function updateMinimap() {
    if (!visible) return;
    const manifest = G.MapWorld?.manifest;
    const title = el('minimap-title');
    const image = el('minimap-image');
    const marker = el('minimap-player');
    if (title) title.textContent = manifest?.mapInfo?.playerDescription || manifest?.name || 'Sabuk-Prov';

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

  function renderMagic() {
    const c = currentCharacter || G.Session.currentCharacter() || {};
    const className = String(c.className || '').toLowerCase();
    if (className === 'wizard' && G.MagicUI?.render) return G.MagicUI.render();
    return renderOriginalMagicShell(className);
  }

  function renderOriginalMagicShell(className) {
    const header = ({ warrior:160, taoist:162, assassin:163 })[className] || 160;
    const tabSets = {
      warrior: [[166,'Active'],[168,'Passive'],[170,'Toggle'],[172,'Horse']],
      taoist: [[184,'Holy'],[186,'Dark']],
      assassin: [[188,'Physical'],[190,'Atrocity'],[192,'Kill'],[194,'Assassination']]
    };
    const tabs = tabSets[className] || tabSets.warrior;
    return `<div class="origins-magic-original-shell">
      ${spriteHtml(`interface-${header}`, 'original-magic-header')}
      ${spriteHtml('interface-164', 'original-magic-background')}
      <button class="original-magic-close" type="button" data-original-magic-close>${spriteHtml('interface-15')}</button>
      <div class="original-magic-title">MAGIC</div>
      <div class="original-magic-tabs">${tabs.map(([idx,label], i) => `<button class="original-school-tab${i===0?' is-selected':''}" title="${esc(label)}">${spriteHtml(`interface-${idx+(i===0?1:0)}`)}</button>`).join('')}</div>
    </div>`;
  }

  function syncTabs(windowEl, selector, selected) {
    windowEl.querySelectorAll(selector).forEach(button => {
      const isSelected = button === selected;
      button.classList.toggle('is-selected', isSelected);
      const art = button.querySelector('.tab-bg');
      if (art) applySprite(art, isSelected ? 'tab-selected-60' : 'tab-deselected-60');
    });
  }

  function renderCharacter() {
    const c = currentCharacter || G.Session.currentCharacter() || { name: '', className: '', level: 1 };
    return `
      <div class="character-tabs">${tabButton('Character', true)}${tabButton('Discipline')}${tabButton('Hermit')}${tabButton('Crafting')}</div>
      <div class="character-name-panel"><strong>${esc(c.name)}</strong><span>${esc(c.className)} · Lv ${esc(c.level)}</span></div>`;
  }

  function renderInventory() {
    return `
      <div class="inventory-weight">
        <span class="inventory-weight-bar">${spriteHtml('gameinter-360')}</span>
        <span class="inventory-weight-value">0 / 0</span>
      </div>
      <span class="inventory-primary-label">Gold</span><span class="inventory-primary-value">0</span>
      <span class="inventory-secondary-label">GameGold</span><span class="inventory-secondary-value">0</span>
      <button class="inventory-icon-button inventory-sort" title="Ordenar">${spriteHtml('gameinter-364')}</button>
      <button class="inventory-icon-button inventory-trash" title="Eliminar">${spriteHtml('gameinter-358')}</button>`;
  }

  function renderQuest() {
    return `
      <div class="zircon-window-title">QUEST LOG</div>
      <div class="quest-tabs">
        ${tabButton('Current', true, 'data-quest-tab="current"')}
        ${tabButton('Available', false, 'data-quest-tab="available"')}
        ${tabButton('Milestones', false, 'data-quest-tab="milestone"')}
        ${tabButton('Missions', false, 'data-quest-tab="mission"')}
      </div>`;
  }

  function renderMail() {
    return `
      <div class="zircon-window-title">COMMUNICATION</div>
      <div class="mail-tabs">
        ${tabButton('Friends', true, 'data-mail-tab="friends"')}
        ${tabButton('Received', false, 'data-mail-tab="received"')}
        ${tabButton('Send', false, 'data-mail-tab="send"')}
        ${tabButton('Blocked', false, 'data-mail-tab="blocked"')}
      </div>
      ${spriteHtml('interface-201', 'mail-tab-background')}`;
  }

  function renderBelt() {
    return `<div class="belt-slots">${Array.from({ length: 6 }, (_, i) => `<div class="belt-slot"><span>${i + 1}</span></div>`).join('')}</div>`;
  }

  function renderGroup() {
    return `
      <div class="zircon-window-title">GROUP</div>
      <div class="group-member-tab">${tabButton('Members', true)}</div>
      <button class="group-icon group-add" title="Add">${spriteHtml('interface-241')}</button>
      <button class="group-icon group-remove" title="Remove">${spriteHtml('interface-242')}</button>
      <button class="group-icon group-lfg" title="Looking for group">${spriteHtml('interface-243')}</button>
      <button class="group-icon group-bag" title="Group bag">${spriteHtml('gameinter-87')}</button>
      <div class="group-lfg-heading"><span>Group Name</span><span>Status</span></div>`;
  }

  function renderMenu() {
    const labels = ['Settings', 'Help', 'Guild', 'Storage', 'Ranking', 'Companion', 'Leave'];
    return `<div class="zircon-window-title">MENU</div><div class="menu-buttons">${labels.map(label => `<button class="zircon-default-button">${spriteHtml('button-default-100', 'button-bg')}<span>${label}</span></button>`).join('')}</div>`;
  }

  function renderStore() {
    return `
      <div class="zircon-window-title">GAME STORE</div>
      <div class="store-label store-sort">Sort By</div>
      <div class="store-label store-currency">CURRENCY</div>
      <div class="store-label store-top">TOP FIVE</div>
      <button class="store-search-button">${spriteHtml('button-small-68', 'button-bg')}<span>Search</span></button>
      <button class="store-wide-button store-recharge">${spriteHtml('button-default-172', 'button-bg')}<span>Recharge</span></button>
      <button class="store-wide-button store-currency-toggle">${spriteHtml('button-default-172', 'button-bg')}<span>Use Hunt Gold</span></button>`;
  }

  function tabButton(label, selected = false, extra = '') {
    return `<button class="zircon-tab-button${selected ? ' is-selected' : ''}" ${extra}>${spriteHtml(selected ? 'tab-selected-60' : 'tab-deselected-60', 'tab-bg')}<span>${esc(label)}</span></button>`;
  }

  function spriteNode(name, className = '') {
    const node = document.createElement('i');
    node.className = `zircon-sprite ${className}`.trim();
    applySprite(node, name);
    return node;
  }

  function spriteHtml(name, className = '') {
    const s = A.sprites[name];
    if (!s) return '';
    const sheet = A.sheets[s.sheet];
    return `<i class="zircon-sprite ${className}" style="width:${s.w}px;height:${s.h}px;background-image:url('${sheet}');background-position:-${s.x}px -${s.y}px"></i>`;
  }

  function applySprite(node, name) {
    const s = A.sprites[name];
    if (!node || !s) return;
    node.dataset.sprite = name;
    node.style.width = `${s.w}px`;
    node.style.height = `${s.h}px`;
    node.style.backgroundImage = `url('${A.sheets[s.sheet]}')`;
    node.style.backgroundPosition = `-${s.x}px -${s.y}px`;
  }

  function text(id, value) {
    const node = el(id);
    if (node) node.textContent = value;
  }

  function esc(value) {
    return String(value ?? '').replace(/[&<>'"]/g, ch => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' })[ch]);
  }

  return Object.freeze({ init, show, hide, toggleWindow, closeWindow, setStats, refreshCharacterData, updateMinimap });
})();

addEventListener('DOMContentLoaded', () => {
  G.IngameUI.init();
  const play = document.getElementById('play-character');
  if (play) play.addEventListener('click', () => setTimeout(() => G.IngameUI.show(G.Session.currentCharacter()), 0));
}, { once: true });
