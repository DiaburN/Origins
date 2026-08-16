const stage = document.querySelector('#stage');
let zCounter = 100;

function isWindow(element) {
  return element instanceof HTMLElement && (element.classList.contains('window') || element.classList.contains('generic-window'));
}

function focusWindow(root) {
  if (!isWindow(root)) return;
  zCounter += 1;
  root.style.zIndex = String(zCounter);
  document.querySelectorAll('.window.focused,.generic-window.focused').forEach(element => {
    if (element !== root) element.classList.remove('focused');
  });
  root.classList.add('focused');
}

function storageKey(root) {
  return root.id ? `origins-zircon-window:${root.id}` : null;
}

function restorePosition(root) {
  const key = storageKey(root);
  if (!key) return;
  try {
    const saved = JSON.parse(sessionStorage.getItem(key) || 'null');
    if (!saved || !Number.isFinite(saved.x) || !Number.isFinite(saved.y)) return;
    root.style.left = `${saved.x}px`;
    root.style.top = `${saved.y}px`;
  } catch {
    // A malformed transient browser value must never break the UI reference.
  }
}

function savePosition(root) {
  const key = storageKey(root);
  if (!key) return;
  const x = Number.parseFloat(root.style.left || '0');
  const y = Number.parseFloat(root.style.top || '0');
  if (!Number.isFinite(x) || !Number.isFinite(y)) return;
  sessionStorage.setItem(key, JSON.stringify({x, y}));
}

function isInteractiveTarget(target) {
  return target instanceof Element && Boolean(target.closest('button,input,textarea,select,.close,.ui-button,.dx-generated-button,.dx-checkbox,.dx-scrollbar'));
}

function installDrag(root) {
  if (!isWindow(root) || root.dataset.originsDesktopRuntime === '1') return;
  root.dataset.originsDesktopRuntime = '1';
  restorePosition(root);
  focusWindow(root);

  root.addEventListener('origins:focus', () => focusWindow(root));
  root.addEventListener('pointerdown', event => {
    focusWindow(root);
    if (event.button !== 0 || isInteractiveTarget(event.target)) return;

    const rect = root.getBoundingClientRect();
    const localY = event.clientY - rect.top;
    const explicitHandle = event.target instanceof Element && Boolean(event.target.closest('.window-title,.generic-window-header'));
    if (!explicitHandle && localY > 34) return;

    event.preventDefault();
    root.setPointerCapture?.(event.pointerId);

    const stageRect = stage.getBoundingClientRect();
    const startX = event.clientX;
    const startY = event.clientY;
    const startLeft = Number.parseFloat(root.style.left || '0');
    const startTop = Number.parseFloat(root.style.top || '0');

    const move = moveEvent => {
      const width = root.offsetWidth;
      const height = root.offsetHeight;
      const rawX = startLeft + (moveEvent.clientX - startX);
      const rawY = startTop + (moveEvent.clientY - startY);
      const maxX = Math.max(0, stageRect.width - Math.min(width, stageRect.width));
      const maxY = Math.max(0, stageRect.height - Math.min(34, height));
      root.style.left = `${Math.round(Math.max(0, Math.min(maxX, rawX)))}px`;
      root.style.top = `${Math.round(Math.max(0, Math.min(maxY, rawY)))}px`;
    };

    const end = endEvent => {
      root.releasePointerCapture?.(endEvent.pointerId);
      root.removeEventListener('pointermove', move);
      root.removeEventListener('pointerup', end);
      root.removeEventListener('pointercancel', end);
      savePosition(root);
    };

    root.addEventListener('pointermove', move);
    root.addEventListener('pointerup', end);
    root.addEventListener('pointercancel', end);
  });
}

function scan(node) {
  if (!(node instanceof Element)) return;
  if (isWindow(node)) installDrag(node);
  node.querySelectorAll?.('.window,.generic-window').forEach(installDrag);
}

new MutationObserver(records => {
  for (const record of records) {
    record.addedNodes.forEach(scan);
  }
}).observe(stage, {childList: true, subtree: true});

stage.querySelectorAll('.window,.generic-window').forEach(installDrag);

document.querySelector('#reset-layout')?.addEventListener('click', () => {
  for (const key of Object.keys(sessionStorage)) {
    if (key.startsWith('origins-zircon-window:')) sessionStorage.removeItem(key);
  }
});
