window.G = window.G || {};

G.ZirconLayout = (() => {
  const DESIGN_WIDTH = 1024;
  const DESIGN_HEIGHT = 768;
  const PANEL_WIDTH = 1024;
  const PANEL_HEIGHT = 68;

  const HUD_ASSETS = Object.freeze({
    'hud-exp-frame': 'gameinter-51',
    'hud-exp-fill': 'gameinter-56',
    'hud-hp-fill': 'gameinter-52',
    'hud-mp-fill': 'gameinter-54',
    'hud-focus-fill': 'gameinter-58',
    'hud-icon-class': 'gameinter-70',
    'hud-icon-level': 'gameinter-71',
    'hud-icon-fp': 'gameinter-72',
    'hud-icon-cp': 'gameinter-73',
    'hud-icon-ac': 'gameinter-66',
    'hud-icon-dc': 'gameinter-65',
    'hud-icon-mac': 'gameinter-63',
    'hud-icon-mc': 'gameinter-62',
    'hud-icon-sc': 'gameinter-64'
  });

  const BUTTON_ASSETS = Object.freeze({
    character: 'gameinter-82',
    inventory: 'gameinter-87',
    magic: 'gameinter-92',
    quest: 'gameinter-112',
    mail: 'gameinter-97',
    belt: 'gameinter-107',
    group: 'gameinter-102',
    menu: 'gameinter-117',
    store: 'gameinter-122'
  });

  let scale = 1;
  let logicalWidth = innerWidth;
  let logicalHeight = innerHeight;

  const el = id => document.getElementById(id);

  function init() {
    applyExactMainPanel();
    installScaledDragging();
    updateScaleAndLayout();

    addEventListener('resize', updateScaleAndLayout);

    const shell = el('ingame-ui');
    if (shell) {
      new MutationObserver(() => {
        if (!shell.hidden) setTimeout(updateScaleAndLayout, 0);
      }).observe(shell, { attributes: true, attributeFilter: ['hidden'] });
    }

    el('minimap-size')?.addEventListener('click', () => setTimeout(updateScaleAndLayout, 0));

    setInterval(updateFocusGlow, 250);
  }

  function computeScale() {
    const fit = Math.min(innerWidth / DESIGN_WIDTH, innerHeight / DESIGN_HEIGHT);
    scale = Math.max(0.65, Math.min(3, fit));
    logicalWidth = innerWidth / scale;
    logicalHeight = innerHeight / scale;

    const root = document.documentElement;
    root.style.setProperty('--zircon-ui-scale', String(scale));
    root.style.setProperty('--zircon-logical-width', `${logicalWidth}px`);
    root.style.setProperty('--zircon-logical-height', `${logicalHeight}px`);
  }

  function updateScaleAndLayout() {
    computeScale();
    syncClassSpecificStats();
    applyExactWindowLayout();
  }

  function syncClassSpecificStats() {
    const character = G.Session?.currentCharacter?.();
    const className = String(character?.className || '').toLowerCase();
    const showMC = className === 'wizard' || className === 'warrior';
    const showSC = className === 'taoist' || className === 'assassin';

    setVisible('hud-icon-mc', showMC);
    setVisible('panel-mc', showMC);
    setVisible('hud-icon-sc', showSC);
    setVisible('panel-sc', showSC);
  }

  function setVisible(id, visible) {
    const node = el(id);
    if (node) node.style.display = visible ? '' : 'none';
  }

  function applyExactWindowLayout() {
    const minimap = el('minimap-box');
    const minimapHeight = minimap?.classList.contains('is-large') ? 300 : 200;
    const panelX = (logicalWidth - PANEL_WIDTH) / 2;
    const panelY = logicalHeight - PANEL_HEIGHT;

    place('character', 0, 0);
    place('inventory', logicalWidth - 264, minimapHeight);
    place('magic', logicalWidth - 420, 0);
    place('quest', (logicalWidth - 732) / 2, (logicalHeight - 480) / 2);
    place('mail', (logicalWidth - 296) / 2, (logicalHeight - 424) / 2);
    place('belt', panelX + PANEL_WIDTH - 239, panelY - 54);

    // Zircon centres GroupBox together with the 264 px GroupBagBox, even when the bag is hidden.
    place('group', (logicalWidth - 240 - 264 - 4) / 2, (logicalHeight - 424) / 2);

    place('menu', logicalWidth - 152, logicalHeight - 260 - PANEL_HEIGHT);
    place('store', (logicalWidth - 800) / 2, (logicalHeight - 515) / 2);
  }

  function place(id, x, y) {
    const node = el(`ui-window-${id}`);
    if (!node || node.dataset.userMoved === '1') return;
    const maxX = Math.max(0, logicalWidth - node.offsetWidth);
    const maxY = Math.max(0, logicalHeight - node.offsetHeight);
    node.style.left = `${Math.max(0, Math.min(maxX, x))}px`;
    node.style.top = `${Math.max(0, Math.min(maxY, y))}px`;
  }

  function applyExactMainPanel() {
    const runtime = G.MainPanelAssets;
    if (!runtime?.sheet || !runtime?.sprites) return;

    for (const [id, asset] of Object.entries(HUD_ASSETS)) {
      applyMainSprite(el(id), asset);
    }

    document.querySelectorAll('.panel-button').forEach(button => {
      const asset = BUTTON_ASSETS[button.dataset.window];
      const art = button.querySelector('.panel-button-art');
      if (asset && art) applyMainSprite(art, asset);
    });

    ensureAlerts();
  }

  function applyMainSprite(node, name) {
    const runtime = G.MainPanelAssets;
    const sprite = runtime?.sprites?.[name];
    if (!node || !sprite) return false;

    node.dataset.gameinter = name;
    node.style.backgroundImage = `url('${runtime.sheet}')`;
    node.style.backgroundPosition = `-${sprite.x}px -${sprite.y}px`;
    node.style.backgroundRepeat = 'no-repeat';
    node.style.width = `${sprite.w}px`;
    node.style.height = `${sprite.h}px`;
    return true;
  }

  function ensureAlerts() {
    const questButton = document.querySelector('.panel-button[data-window="quest"]');
    if (questButton && !questButton.querySelector('[data-mainpanel-alert="quest-available"]')) {
      questButton.appendChild(makeAlert('quest-available', 'gameinter-240', 'quest-available'));
      questButton.appendChild(makeAlert('quest-complete', 'gameinter-241', 'quest-complete'));
    }

    const mailButton = document.querySelector('.panel-button[data-window="mail"]');
    if (mailButton && !mailButton.querySelector('[data-mainpanel-alert="mail"]')) {
      mailButton.appendChild(makeAlert('mail', 'gameinter-240', 'mail'));
    }
  }

  function makeAlert(key, asset, className) {
    const node = document.createElement('i');
    node.className = `mainpanel-alert ${className}`;
    node.dataset.mainpanelAlert = key;
    node.hidden = true;
    applyMainSprite(node, asset);
    return node;
  }

  function setAlert(key, visible) {
    const node = document.querySelector(`[data-mainpanel-alert="${key}"]`);
    if (node) node.hidden = !visible;
  }

  function updateFocusGlow() {
    const node = el('hud-focus-fill');
    if (!node) return;
    const currentWidth = Number.parseFloat(node.style.width || '0');
    if (currentWidth < 219.5) {
      if (node.dataset.gameinter !== 'gameinter-58') {
        const width = node.style.width;
        applyMainSprite(node, 'gameinter-58');
        node.style.width = width;
      }
      return;
    }

    const width = node.style.width;
    const asset = Math.floor(Date.now() / 1000) % 2 === 0 ? 'gameinter-59' : 'gameinter-58';
    applyMainSprite(node, asset);
    node.style.width = width;
  }

  function installScaledDragging() {
    document.querySelectorAll('.ingame-window').forEach(windowEl => {
      if (windowEl.dataset.scaledDrag === '1') return;
      windowEl.dataset.scaledDrag = '1';

      let drag = null;

      windowEl.addEventListener('pointerdown', event => {
        if (event.button !== 0) return;
        if (event.target.closest('button,input,select,textarea,.window-interactive')) return;

        const rect = windowEl.getBoundingClientRect();
        const localY = (event.clientY - rect.top) / scale;
        const isBelt = windowEl.dataset.windowId === 'belt';
        if (!isBelt && localY > 34) return;

        event.stopImmediatePropagation();
        drag = {
          dx: (event.clientX - rect.left) / scale,
          dy: (event.clientY - rect.top) / scale,
          pointerId: event.pointerId
        };
        windowEl.dataset.userMoved = '1';
        windowEl.setPointerCapture?.(event.pointerId);
      }, true);

      windowEl.addEventListener('pointermove', event => {
        if (!drag || event.pointerId !== drag.pointerId) return;
        event.stopImmediatePropagation();

        const maxX = Math.max(0, logicalWidth - windowEl.offsetWidth);
        const maxY = Math.max(0, logicalHeight - windowEl.offsetHeight);
        const x = event.clientX / scale - drag.dx;
        const y = event.clientY / scale - drag.dy;
        windowEl.style.left = `${Math.max(0, Math.min(maxX, x))}px`;
        windowEl.style.top = `${Math.max(0, Math.min(maxY, y))}px`;
      }, true);

      const stop = event => {
        if (!drag) return;
        if (event && event.pointerId !== drag.pointerId) return;
        drag = null;
      };
      windowEl.addEventListener('pointerup', stop, true);
      windowEl.addEventListener('pointercancel', stop, true);
    });
  }

  return Object.freeze({
    init,
    updateScaleAndLayout,
    setAlert,
    get scale() { return scale; },
    get logicalWidth() { return logicalWidth; },
    get logicalHeight() { return logicalHeight; }
  });
})();

addEventListener('DOMContentLoaded', () => {
  G.ZirconLayout.init();
}, { once: true });
