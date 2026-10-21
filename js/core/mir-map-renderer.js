window.G = window.G || {};

G.MirMapRenderer = (() => {
  const EMPTY_IMAGE = 65536;
  const ANIMATION_MS = 100;

  let pack = null;
  let status = 'idle';
  let error = null;
  let baseUrl = null;
  const pageRecords = new Map();

  function reset() {
    pack = null;
    status = 'idle';
    error = null;
    baseUrl = null;
    pageRecords.clear();
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

  function pagePath(libraryId, pageIndex) {
    if (Array.isArray(pack.pages)) return pack.pages[pageIndex] || null;
    const library = pack.libraries[String(libraryId)];
    return library && Array.isArray(library.pages) ? (library.pages[pageIndex] || null) : null;
  }

  function pageKey(libraryId, pageIndex) {
    return Array.isArray(pack.pages) ? `global:${pageIndex}` : `${libraryId}:${pageIndex}`;
  }

  function requestPage(libraryId, pageIndex) {
    const key = pageKey(libraryId, pageIndex);
    if (pageRecords.has(key)) return pageRecords.get(key);

    const path = pagePath(libraryId, pageIndex);
    const record = { image: null, state: path ? 'loading' : 'missing' };
    pageRecords.set(key, record);
    if (!path) return record;

    const image = new Image();
    image.decoding = 'async';
    image.onload = () => {
      record.image = image;
      record.state = 'ready';
    };
    image.onerror = () => {
      record.state = 'missing';
      console.error(new Error(`Unable to load MIR atlas page: ${image.src}`));
    };
    image.src = new URL(path, baseUrl).href;
    return record;
  }

  function frameFor(libraryId, imageIndex) {
    if (!pack || imageIndex < 0) return null;
    const library = pack.libraries[String(libraryId)];
    if (!library || !library.frames) return null;

    const raw = library.frames[String(imageIndex)];
    if (!raw || raw.length < 5) return null;

    const pageRecord = requestPage(libraryId, raw[0]);
    if (pageRecord.state !== 'ready' || !pageRecord.image) return null;

    return {
      page: pageRecord.image,
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

  function isCellSized(frame, map) {
    if (!frame) return false;
    return (
      (frame.width === map.cellWidth && frame.height === map.cellHeight) ||
      (frame.width === map.cellWidth * 2 && frame.height === map.cellHeight * 2)
    );
  }

  function isAnimated(animationByte) {
    return animationByte > 1 && animationByte < 255;
  }

  function drawBackground(ctx, map) {
    if (status !== 'ready' || !pack || !map) return false;

    const bounds = visibleBounds(map);
    const startX = bounds.minX & ~1;
    const startY = bounds.minY & ~1;

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

  function drawStaticFloorLayers(ctx, map) {
    if (status !== 'ready' || !pack || !map) return false;

    const bounds = visibleBounds(map);
    for (let y = bounds.minY; y <= bounds.maxY; y++) {
      for (let x = bounds.minX; x <= bounds.maxX; x++) {
        const cell = map.cell(x, y);
        if (!cell) continue;

        drawStaticFloorLayer(ctx, map, x, y, cell.middleFile, cell.middleImage, cell.middleAnimation);
        drawStaticFloorLayer(ctx, map, x, y, cell.frontFile, cell.frontImage, cell.frontAnimation);
      }
    }
    return true;
  }

  function drawStaticFloorLayer(ctx, map, x, y, libraryId, storedImage, animationByte) {
    if (libraryId === 0 || libraryId === G.MirMap.EMPTY_FILE) return;
    if (storedImage <= 0 || storedImage === EMPTY_IMAGE || isAnimated(animationByte)) return;

    const frame = frameFor(libraryId, storedImage - 1);
    if (!isCellSized(frame, map)) return;

    drawFrame(ctx, frame, x * map.cellWidth, y * map.cellHeight);
  }

  function animationIndex(baseImage, animationByte, tick) {
    if (baseImage <= 0 || baseImage === EMPTY_IMAGE) return -1;

    let index = baseImage - 1;
    if (isAnimated(animationByte)) {
      const count = animationByte & 0x0F;
      if (count > 0) index += tick % count;
    }
    return index;
  }

  function drawObjectLayer(ctx, map, x, y, libraryId, storedImage, animationByte, blend, tick) {
    if (libraryId === 0 || libraryId === G.MirMap.EMPTY_FILE) return;

    const index = animationIndex(storedImage, animationByte, tick);
    if (index < 0) return;

    const frame = frameFor(libraryId, index);
    if (!frame) return;

    const animated = isAnimated(animationByte);
    const cellSized = isCellSized(frame, map);
    if (cellSized && !animated) return;

    const drawY = cellSized
      ? y * map.cellHeight
      : (y + 1) * map.cellHeight - frame.height;

    drawFrame(ctx, frame, x * map.cellWidth, drawY, animated && blend ? 0.5 : 1);
  }

  function drawRow(ctx, map, y, minX, maxX, tick) {
    for (let x = minX; x <= maxX; x++) {
      const cell = map.cell(x, y);
      if (!cell) continue;

      drawObjectLayer(ctx, map, x, y, cell.middleFile, cell.middleImage, cell.middleAnimation, cell.middleAnimationBlend, tick);
      drawObjectLayer(ctx, map, x, y, cell.frontFile, cell.frontImage, cell.frontAnimation, cell.frontAnimationBlend, tick);
    }
  }

  function drawLayers(ctx, map, now = performance.now(), afterRow = null) {
    if (status !== 'ready' || !pack || !map) return false;

    const maxHeight = Number.isFinite(pack.maxFrameHeight) ? pack.maxFrameHeight : map.cellHeight * 20;
    const extraBottomRows = Math.max(1, Math.ceil(maxHeight / map.cellHeight));
    const bounds = visibleBounds(map, extraBottomRows);
    const tick = Math.floor(now / ANIMATION_MS);

    for (let y = bounds.minY; y <= bounds.maxY; y++) {
      drawRow(ctx, map, y, bounds.minX, bounds.maxX, tick);
      if (afterRow) afterRow(y);
    }

    return true;
  }

  function draw(ctx, map, now = performance.now(), afterRow = null) {
    if (!drawBackground(ctx, map)) return false;
    drawStaticFloorLayers(ctx, map);
    drawLayers(ctx, map, now, afterRow);
    return true;
  }

  return Object.freeze({
    load,
    reset,
    draw,
    drawBackground,
    drawStaticFloorLayers,
    drawLayers,
    get status() { return status; },
    get error() { return error; },
    get ready() { return status === 'ready'; },
    get loadedPageCount() {
      let count = 0;
      for (const record of pageRecords.values()) if (record.state === 'ready') count += 1;
      return count;
    }
  });
})();
