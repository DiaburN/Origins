window.G = window.G || {};

G.ZirconPrimitives = (() => {
  const A = () => G.ZirconPrimitiveAssets || { sheet: '', sprites: {}, metrics: {} };
  let imagePromise = null;

  function ready() {
    const assets = A();
    if (!assets.sheet || !Object.keys(assets.sprites || {}).length) return Promise.resolve(null);
    if (imagePromise) return imagePromise;
    imagePromise = new Promise((resolve, reject) => {
      const image = new Image();
      image.onload = () => resolve(image);
      image.onerror = reject;
      image.src = assets.sheet;
    });
    return imagePromise;
  }

  function sprite(name) {
    return A().sprites?.[name] || null;
  }

  // Mirrors MirLibrary.Draw(index, x, y, colour, Rectangle area, ...):
  // Rectangle is a SOURCE CROP. Zircon does not stretch these Interface pieces.
  function drawCrop(ctx, image, name, dx, dy, requestedWidth = null, requestedHeight = null, sourceX = 0, sourceY = 0) {
    const s = sprite(name);
    if (!s || !image) return { width: 0, height: 0 };
    const width = Math.max(0, Math.min(requestedWidth ?? s.w, s.w - sourceX));
    const height = Math.max(0, Math.min(requestedHeight ?? s.h, s.h - sourceY));
    if (!width || !height) return { width: 0, height: 0 };
    ctx.drawImage(image, s.x + sourceX, s.y + sourceY, width, height, dx, dy, width, height);
    return { width, height };
  }

  function canvas(width, height, className = '') {
    const node = document.createElement('canvas');
    node.width = Math.max(1, Math.round(width));
    node.height = Math.max(1, Math.round(height));
    node.className = className;
    node.style.width = `${width}px`;
    node.style.height = `${height}px`;
    node.style.imageRendering = 'pixelated';
    return node;
  }

  function buttonParts(type) {
    switch (type) {
      case 'selected-tab': return ['interface-56', 'interface-58', 'interface-57'];
      case 'deselected-tab': return ['interface-53', 'interface-55', 'interface-54'];
      case 'small': return ['interface-41', 'interface-43', 'interface-42'];
      case 'add': return ['interface-241'];
      case 'remove': return ['interface-242'];
      case 'lfg': return ['interface-243'];
      case 'options': return ['interface-245'];
      default: return ['interface-16', 'interface-18', 'interface-17'];
    }
  }

  async function paintButton(target, type = 'default') {
    const image = await ready();
    if (!image || !target) return;
    const ctx = target.getContext('2d');
    ctx.imageSmoothingEnabled = false;
    ctx.clearRect(0, 0, target.width, target.height);

    const parts = buttonParts(type);
    if (parts.length === 1) {
      drawCrop(ctx, image, parts[0], 0, 0, target.width, target.height);
      return;
    }

    const left = sprite(parts[0]);
    const middle = sprite(parts[1]);
    const right = sprite(parts[2]);
    if (!left || !middle || !right) return;

    drawCrop(ctx, image, parts[0], 0, 0);
    const middleWidth = Math.max(0, target.width - left.w - right.w);
    drawCrop(ctx, image, parts[1], left.w, 0, middleWidth, middle.h);
    drawCrop(ctx, image, parts[2], target.width - right.w, 0);
  }

  function makeButton({ type = 'default', width = 100, height = null, label = '', className = '', selected = false } = {}) {
    const parts = buttonParts(type);
    const first = sprite(parts[0]);
    const naturalHeight = first?.h || A().metrics?.defaultHeight || 24;
    const button = document.createElement('button');
    button.type = 'button';
    button.className = `zircon-primitive-button ${className}`.trim();
    button.style.width = `${width}px`;
    button.style.height = `${height ?? naturalHeight}px`;
    button.dataset.buttonType = type;
    if (selected) button.dataset.selected = '1';

    const art = canvas(width, height ?? naturalHeight, 'zircon-primitive-button-art');
    const text = document.createElement('span');
    text.className = 'zircon-primitive-button-label';
    text.textContent = label;
    button.append(art, text);
    paintButton(art, type);
    return button;
  }

  async function repaintButton(button, type) {
    if (!button) return;
    button.dataset.buttonType = type;
    const art = button.querySelector('canvas.zircon-primitive-button-art');
    await paintButton(art, type);
  }

  async function paintWindow(target, options = {}) {
    const image = await ready();
    if (!image || !target) return;

    const hasTopBorder = options.hasTopBorder !== false;
    const hasTitle = options.hasTitle !== false;
    const hasFooter = options.hasFooter === true;
    const slimFooter = options.slimFooter === true;
    const width = target.width;
    const height = target.height;
    const ctx = target.getContext('2d');
    ctx.imageSmoothingEnabled = false;
    ctx.clearRect(0, 0, width, height);
    ctx.fillStyle = 'rgb(16,8,8)';
    ctx.fillRect(0, 0, width, height);

    let s = sprite(hasTopBorder ? 'interface-0' : 'interface-2');
    if (!s) return;
    drawCrop(ctx, image, hasTopBorder ? 'interface-0' : 'interface-2', 0, 0, width, s.h);
    let y = s.h;

    s = sprite('interface-1');
    const x = s?.w || 0;
    if (s) {
      drawCrop(ctx, image, 'interface-1', 0, y, s.w, height - y);
      drawCrop(ctx, image, 'interface-1', width - s.w, y, s.w, height - y);
    }

    if (hasTitle) {
      s = sprite('interface-3');
      if (s) {
        drawCrop(ctx, image, 'interface-3', x, y, width - x * 2, height);
        y += s.h;
        drawCrop(ctx, image, 'interface-4', 0, y - 3);
        const rightTitle = sprite('interface-5');
        if (rightTitle) drawCrop(ctx, image, 'interface-5', width - rightTitle.w, y - 3);
      }
    }

    if (hasTopBorder) {
      drawCrop(ctx, image, 'interface-11', 0, 0);
      const rightTop = sprite('interface-12');
      if (rightTop) drawCrop(ctx, image, 'interface-12', width - rightTop.w, 0);
    } else {
      drawCrop(ctx, image, 'interface-25', 0, 0);
      const rightTop = sprite('interface-26');
      if (rightTop) drawCrop(ctx, image, 'interface-26', width - rightTop.w, 0);
    }

    if (!hasFooter) {
      if (slimFooter) {
        s = sprite('interface-126');
        if (s) {
          drawCrop(ctx, image, 'interface-126', 0, height - s.h, width, s.h);
          y = s.h - 2;
          const strip = sprite('interface-2');
          if (strip) {
            drawCrop(ctx, image, 'interface-2', 0, height - strip.h - y, width, strip.h);
            const c8 = sprite('interface-8');
            const c9 = sprite('interface-9');
            if (c8) drawCrop(ctx, image, 'interface-8', 0, height - c8.h - y);
            if (c9) drawCrop(ctx, image, 'interface-9', width - c9.w, height - c9.h - y);
          }
        }
      } else {
        const strip = sprite('interface-2');
        if (strip) drawCrop(ctx, image, 'interface-2', 0, height - strip.h, width, strip.h);
        const c8 = sprite('interface-8');
        const c9 = sprite('interface-9');
        if (c8) drawCrop(ctx, image, 'interface-8', 0, height - c8.h);
        if (c9) drawCrop(ctx, image, 'interface-9', width - c9.w, height - c9.h);
      }
    } else {
      const footer = sprite('interface-126');
      if (footer) {
        drawCrop(ctx, image, 'interface-126', 0, height - footer.h, width, footer.h);
        y = footer.h;
      } else y = 0;

      const inner = sprite('interface-10');
      if (inner) {
        drawCrop(ctx, image, 'interface-10', x, height - inner.h - y, width - x * 2, inner.h);
        y += inner.h;
      }

      const strip = sprite('interface-2');
      if (strip) {
        drawCrop(ctx, image, 'interface-2', 0, height - y - strip.h, width, strip.h);
        y += strip.h;
      }

      const c6 = sprite('interface-6');
      const c7 = sprite('interface-7');
      if (c6) drawCrop(ctx, image, 'interface-6', 0, height - y - c6.h + 3);
      if (c7) drawCrop(ctx, image, 'interface-7', width - c7.w, height - y - c7.h + 3);
    }
  }

  function makeWindowChrome(width, height, options = {}) {
    const art = canvas(width, height, 'zircon-primitive-window-art');
    paintWindow(art, options);
    return art;
  }

  function getClientArea(width, height, options = {}) {
    const m = A().metrics || {};
    const hasTopBorder = options.hasTopBorder !== false;
    const hasTitle = options.hasTitle !== false;
    const hasFooter = options.hasFooter === true;
    const slimFooter = options.slimFooter === true;
    const noHeaderSize = m.noHeaderSize || 0;
    const headerSize = m.headerSize || 0;
    const headerBarSize = m.headerBarSize || 0;
    const footerSize = m.footerSize || 0;
    const noFooterSize = m.noFooterSize || 0;
    const slimFooterSize = m.slimFooterSize || 0;

    const x = 9;
    let y = 6;
    if (!hasTopBorder) y += noHeaderSize;
    else if (hasTitle) y += headerSize;
    else y += headerBarSize;

    const w = width - x * 2;
    let h = height - y - 6;
    if (!hasFooter) {
      h += noFooterSize;
      if (slimFooter) h -= slimFooterSize;
    } else h -= footerSize;
    return { x, y, width: w, height: h };
  }

  function makeItemCell({ width = 36, height = 36, className = '' } = {}) {
    const cell = document.createElement('div');
    cell.className = `zircon-item-cell ${className}`.trim();
    cell.style.width = `${width}px`;
    cell.style.height = `${height}px`;
    return cell;
  }

  return Object.freeze({
    ready,
    sprite,
    makeButton,
    repaintButton,
    paintButton,
    makeWindowChrome,
    paintWindow,
    getClientArea,
    makeItemCell
  });
})();
