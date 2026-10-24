window.G = window.G || {};

G.InventoryUI = (() => {
  let scheduled = false;

  function spriteNode(name, className = '') {
    const assets = G.GameUiAssets || {};
    const s = assets.sprites?.[name];
    const sheet = s ? assets.sheets?.[s.sheet] : null;
    if (!s || !sheet) return null;
    const node = document.createElement('i');
    node.className = `inventory-source-sprite ${className}`.trim();
    node.style.width = `${s.w}px`;
    node.style.height = `${s.h}px`;
    node.style.backgroundImage = `url('${sheet}')`;
    node.style.backgroundPosition = `-${s.x}px -${s.y}px`;
    node.style.backgroundRepeat = 'no-repeat';
    node.style.imageRendering = 'pixelated';
    return node;
  }

  function mountGrid(host) {
    host.replaceChildren();
    const step = 36 - 1 + 2; // DXItemCell.CellWidth - 1 + GridPadding*2 = 37
    for (let y = 0; y < 8; y++) {
      for (let x = 0; x < 6; x++) {
        const cell = document.createElement('div');
        cell.className = 'inventory-exact-cell';
        cell.dataset.slot = String(y * 6 + x);
        cell.style.left = `${1 + x * step}px`;
        cell.style.top = `${1 + y * step}px`;
        host.appendChild(cell);
      }
    }
  }

  function iconButton(name, className, title) {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = `inventory-exact-icon ${className}`;
    button.title = title;
    const art = spriteNode(name);
    if (art) button.appendChild(art);
    return button;
  }

  function render() {
    const windowEl = document.getElementById('ui-window-inventory');
    if (!windowEl || windowEl.hidden) return;
    const body = windowEl.querySelector('.ingame-window-body');
    if (!body) return;
    if (body.dataset.exactInventory === '1') return;

    body.dataset.exactInventory = '1';
    body.innerHTML = `
      <div class="inventory-exact-grid" data-inventory-grid></div>
      <div class="inventory-exact-weight">
        <div class="inventory-exact-weight-fill" data-inventory-weight-fill></div>
        <span class="inventory-exact-weight-text">0 / 0</span>
      </div>
      <span class="inventory-exact-currency-title primary">Gold</span>
      <span class="inventory-exact-currency-value primary">0</span>
      <span class="inventory-exact-currency-title secondary">GameGold</span>
      <span class="inventory-exact-currency-value secondary">0</span>
      <button class="inventory-wallet-hitbox" type="button" title="Wallet"></button>`;

    mountGrid(body.querySelector('[data-inventory-grid]'));

    const weight = spriteNode('gameinter-360', 'inventory-weight-source');
    if (weight) body.querySelector('[data-inventory-weight-fill]')?.appendChild(weight);
    body.appendChild(iconButton('gameinter-364', 'inventory-exact-sort', 'Sort'));
    body.appendChild(iconButton('gameinter-358', 'inventory-exact-trash', 'Delete'));
  }

  function scheduleRender() {
    if (scheduled) return;
    scheduled = true;
    requestAnimationFrame(() => {
      scheduled = false;
      render();
    });
  }

  function init() {
    const layer = document.getElementById('ui-window-layer');
    if (!layer) return;
    new MutationObserver(mutations => {
      for (const mutation of mutations) {
        const target = mutation.target instanceof Element ? mutation.target : mutation.target?.parentElement;
        if (target?.closest?.('#ui-window-inventory') || target?.id === 'ui-window-inventory') {
          const body = document.querySelector('#ui-window-inventory .ingame-window-body');
          if (body && !body.querySelector('.inventory-exact-grid')) body.dataset.exactInventory = '0';
          scheduleRender();
          break;
        }
      }
    }).observe(layer, { childList: true, subtree: true, attributes: true, attributeFilter: ['hidden'] });
    scheduleRender();
  }

  return Object.freeze({ init, render });
})();

addEventListener('DOMContentLoaded', () => G.InventoryUI.init(), { once: true });
