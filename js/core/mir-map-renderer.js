window.G = window.G || {};

G.MirMapRenderer = (() => {
  const EMPTY_IMAGE = 65536;
  const ANIMATION_MS = 100;

  let pack = null;
  let status = 'idle';
  let error = null;
  let baseUrl = null;
  const pages = new Map();

  function reset() {
    pack = null;
    status = 'idle';
    error = null;
    baseUrl = null;
    pages.clear();
  }

  async function load(url) {
    reset();
    status = 'loading-pack';

    try {
      const response = await fetch(url);
      if (!response.ok) throw new Error(`Unable to load MIR render pack: ${url}`);

      const data = await response.json();
      validatePack(data);
      pack = data;
      baseUrl = response.url;

      status = 'loading-pages';
      await preloadPages();
      status = 'ready';
      return pack;
    } catch (cause) {
      error = cause;
      status = 'error';
      console.error(cause);
      return null;
    }
  }

  function validatePack(data) {
    if (!data || data.version !== 1 || !data.libraries) {
      throw new Error('Invalid MIR render pack');
    }
  }

  async function preloadPages() {
    const jobs = [];

    for (const [libraryId, library] of Object.entries(pack.libraries)) {
      if (!library || !Array.isArray(library.pages)) continue;

      library.pages.forEach((path, pageIndex) => {
        const key = `${libraryId}:${pageIndex}`;
        jobs.push(loadImage(new URL(path, baseUrl).href).then(image => pages.set(key, image)));
      });
    }

    await Promise.all(jobs);
  }

  function loadImage(url) {
    return new Promise((resolve, reject) => {
      const image = new Image();
      image.decoding = 'async';
      image.onload = () => resolve(image);
      image.onerror = () => reject(new Error(`Unable to load MIR atlas page: ${url}`));
      image.src = url;
    });
  }

  function frameFor(libraryId, imageIndex) {
    if (!pack || imageIndex < 0) return null;
    const library = pack.libraries[String(libraryId)];
    if (!library || !library.frames) return null;

    const raw = library.frames[String(imageIndex)];
    if (!raw || raw.length < 5) return null;

    const page = pages.get(`${libraryId}:${raw[0]}`);
    if (!page) return null;

    return {
      page,
      sx: raw[1],
      sy: raw[2],
      width: raw[3],
      height: raw[4]
    };
  }

  function visibleBounds(map, extraBottomRows = 0) {
    const cw = map.cellWidth;
    const ch = map.cellHeight;
    const left = G.Camera.left();
    const top = G.Camera.top();
    const right = left + G.Camera.width;
    const bottom = top + G.Camera.height;

    return {
      minX: Math.max(0, Math.floor(left / cw) - 1),
      minY: Math.max(0, Math.floor(top / ch) - 1),
      maxX: Math.min(map.width - 1, Math.ceil(right / cw) + 1),
      maxY: Math.min(map.height - 1, Math.ceil(bottom / ch) + 1 + extraBottomRows)
    };
  }

  function drawFrame(ctx, frame, dx, dy, alpha = 1) {
    if (!frame || frame.width <= 0 || frame.height <= 0) return false;

    const previousAlpha = ctx.globalAlpha;
    if (alpha !== 1) ctx.globalAlpha = previousAlpha * alpha;

    ctx.drawImage(
      frame.page,
      frame.sx,
      frame.sy,
      frame.width,
      frame.height,
      dx,
      dy,
      frame.width,
      frame.height
    );

    if (alpha !== 1) ctx.globalAlpha = previousAlpha;
    return true;
  }

  function drawBackground(ctx, map) {
    if (status !== 'ready' || !pack || !map) return false;

    const bounds = visibleBounds(map);
    let startX = bounds.minX & ~1;
    let startY = bounds.minY & ~1;

    for (let y = startY; y <= bounds.maxY; y += 2) {
      for (let x = startX; x <= bounds.maxX; x += 2) {
        const tile = map.background(x, y);
        if (!tile || tile.file === G.MirMap.EMPTY_FILE) continue;

        const frame = frameFor(tile.file, tile.image);
        if (!frame) continue;
        drawFrame(ctx, frame, x * map.cellWidth, y * map.cellHeight);
      }
    }

    return true;
  }

  function animationIndex(baseImage, animationByte, tick) {
    if (baseImage <= 0 || baseImage === EMPTY_IMAGE) return -1;

    let index = baseImage - 1;
    if (animationByte > 1 && animationByte < 255) {
      const count = animationByte & 0x0F;
      if (count > 0) index += tick % count;
    }
    return index;
  }

  function drawMapFrame(ctx, frame, x, y, map, blend) {
    if (!frame) return;

    const normalCell = frame.width === map.cellWidth && frame.height === map.cellHeight;
    const doubleCell = frame.width === map.cellWidth * 2 && frame.height === map.cellHeight * 2;
    const drawY = normalCell || doubleCell
      ? y * map.cellHeight
      : (y + 1) * map.cellHeight - frame.height;

    drawFrame(ctx, frame, x * map.cellWidth, drawY, blend ? 0.5 : 1);
  }

  function drawLayers(ctx, map, now = performance.now()) {
    if (status !== 'ready' || !pack || !map) return false;

    const maxHeight = Number.isFinite(pack.maxFrameHeight) ? pack.maxFrameHeight : map.cellHeight * 20;
    const extraBottomRows = Math.max(1, Math.ceil(maxHeight / map.cellHeight));
    const bounds = visibleBounds(map, extraBottomRows);
    const tick = Math.floor(now / ANIMATION_MS);

    for (let y = bounds.minY; y <= bounds.maxY; y++) {
      for (let x = bounds.minX; x <= bounds.maxX; x++) {
        const cell = map.cell(x, y);
        if (!cell) continue;

        // Zircon does not draw Tilesc as a Middle/Front object layer.
        if (cell.middleFile !== 0 && cell.middleFile !== G.MirMap.EMPTY_FILE) {
          const index = animationIndex(cell.middleImage, cell.middleAnimation, tick);
          if (index >= 0) {
            const frame = frameFor(cell.middleFile, index);
            drawMapFrame(ctx, frame, x, y, map, cell.middleAnimationBlend);
          }
        }

        if (cell.frontFile !== 0 && cell.frontFile !== G.MirMap.EMPTY_FILE) {
          const index = animationIndex(cell.frontImage, cell.frontAnimation, tick);
          if (index >= 0) {
            const frame = frameFor(cell.frontFile, index);
            drawMapFrame(ctx, frame, x, y, map, cell.frontAnimationBlend);
          }
        }
      }
    }

    return true;
  }

  function draw(ctx, map, now = performance.now()) {
    if (!drawBackground(ctx, map)) return false;
    drawLayers(ctx, map, now);
    return true;
  }

  return Object.freeze({
    load,
    reset,
    draw,
    drawBackground,
    drawLayers,
    get status() { return status; },
    get error() { return error; },
    get ready() { return status === 'ready'; }
  });
})();
