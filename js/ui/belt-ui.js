window.G = window.G || {};

G.BeltUI = (() => {
  const MAX_BELT_COUNT = 10;
  const CELL = 36;
  let scheduled = false;

  function windowSizeFromClient(clientWidth, clientHeight, metrics) {
    // DXWindow.GetSize for HasTopBorder=false, HasFooter=false.
    return {
      width: clientWidth + 18,
      height: clientHeight + 12 + (metrics.noHeaderSize || 0) + (metrics.noFooterSize || 0)
    };
  }

  function acceptableDefaultSize() {
    const p = G.ZirconPrimitives;
    const metrics = G.ZirconPrimitiveAssets?.metrics || {};
    const area = p?.getClientArea?.(0, 0, { hasTopBorder:false, hasTitle:false, hasFooter:false }) || { width:-18, height:-12 };

    let x = Math.ceil((area.width - 10) / CELL);
    let y = Math.ceil((area.height - 10) / CELL);
    if (area.height > area.width) x = 0;
    else y = 0;

    x = Math.max(1, Math.min(MAX_BELT_COUNT, x)) * (CELL - 1) + 1;
    y = Math.max(1, Math.min(MAX_BELT_COUNT, y)) * (CELL - 1) + 1;
    if (x >= y) x += 10;
    else y += 10;

    return windowSizeFromClient(x, y, metrics);
  }

  function buildGrid(body, area) {
    const old = body.querySelector('.belt-exact-grid');
    old?.remove();

    const cols = Math.max(1, Math.floor(area.width / (CELL - 1)));
    const rows = Math.max(1, Math.floor(area.height / (CELL - 1)));
    const grid = document.createElement('div');
    grid.className = 'belt-exact-grid';
    grid.style.left = `${area.x}px`;
    grid.style.top = `${area.y}px`;
    grid.style.width = `${cols * (CELL - 1) + 1}px`;
    grid.style.height = `${rows * (CELL - 1) + 1}px`;

    for (let i = 0; i < cols * rows; i++) {
      const x = i % cols;
      const y = Math.floor(i / cols);
      const cell = document.createElement('div');
      cell.className = 'belt-exact-cell';
      cell.style.left = `${x * (CELL - 1)}px`;
      cell.style.top = `${y * (CELL - 1)}px`;
      const label = document.createElement('span');
      label.textContent = String((i + 1) % 10);
      cell.appendChild(label);
      grid.appendChild(cell);
    }
    body.appendChild(grid);
  }

  async function render() {
    const windowEl = document.getElementById('ui-window-belt');
    if (!windowEl || windowEl.hidden) return;
    const body = windowEl.querySelector('.ingame-window-body');
    if (!body) return;

    await G.ZirconPrimitives?.ready?.();
    const size = acceptableDefaultSize();
    windowEl.style.width = `${size.width}px`;
    windowEl.style.height = `${size.height}px`;
    body.style.width = `${size.width}px`;
    body.style.height = `${size.height}px`;
    body.replaceChildren();
    windowEl.querySelector('.belt-frame-art')?.remove();
    windowEl.querySelector('.zircon-primitive-window-art')?.remove();

    const chrome = G.ZirconPrimitives?.makeWindowChrome?.(size.width, size.height, {
      hasTopBorder:false,
      hasTitle:false,
      hasFooter:false
    });
    if (chrome) windowEl.insertBefore(chrome, body);

    const area = G.ZirconPrimitives?.getClientArea?.(size.width, size.height, {
      hasTopBorder:false,
      hasTitle:false,
      hasFooter:false
    });
    if (area) buildGrid(body, area);
    body.dataset.exactBelt = '1';
    G.ZirconLayout?.updateScaleAndLayout?.();
  }

  function scheduleRender() {
    if (scheduled) return;
    scheduled = true;
    requestAnimationFrame(async () => {
      scheduled = false;
      await render();
    });
  }

  function init() {
    const layer = document.getElementById('ui-window-layer');
    if (!layer) return;
    new MutationObserver(mutations => {
      for (const mutation of mutations) {
        const target = mutation.target instanceof Element ? mutation.target : mutation.target?.parentElement;
        if (target?.closest?.('#ui-window-belt') || target?.id === 'ui-window-belt') {
          scheduleRender();
          break;
        }
      }
    }).observe(layer, { childList:true, subtree:true, attributes:true, attributeFilter:['hidden'] });
    scheduleRender();
  }

  return Object.freeze({ init, render });
})();

addEventListener('DOMContentLoaded', () => G.BeltUI.init(), { once:true });
