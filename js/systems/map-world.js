window.G = window.G || {};

G.MapWorld = (() => {
  const EMPTY_IMAGE = 65536;

  let manifest = null;
  let map = null;
  let status = 'idle';
  let error = null;

  async function load(manifestPath) {
    manifest = null;
    map = null;
    status = 'loading-manifest';
    error = null;

    try {
      const response = await fetch(manifestPath);
      if (!response.ok) throw new Error(`Unable to load map manifest: ${manifestPath}`);

      manifest = await response.json();
      const runtime = manifest.runtime || {};
      if (runtime.ready !== true || !runtime.mapFile) {
        status = 'waiting-source';
        return null;
      }

      status = 'loading-map';
      const mapUrl = new URL(runtime.mapFile, response.url).href;
      map = await G.MirMap.load(mapUrl);

      const source = manifest.source || {};
      if (source.width && source.height && (map.width !== source.width || map.height !== source.height)) {
        throw new Error(`Map dimensions do not match manifest: expected ${source.width}x${source.height}, got ${map.width}x${map.height}`);
      }

      status = 'ready';
      return map;
    } catch (cause) {
      map = null;
      error = cause;
      status = 'error';
      console.error(cause);
      return null;
    }
  }

  function canOccupyWorld(x, y) {
    if (!map) return true;
    const cell = map.worldToCell(x, y);
    return map.isWalkable(cell.x, cell.y);
  }

  function movePoint(entity, dx, dy) {
    if (!map) {
      entity.x += dx;
      entity.y += dy;
      return dx !== 0 || dy !== 0;
    }

    let moved = false;
    const nextX = entity.x + dx;
    if (dx !== 0 && canOccupyWorld(nextX, entity.y)) {
      entity.x = nextX;
      moved = true;
    }

    const nextY = entity.y + dy;
    if (dy !== 0 && canOccupyWorld(entity.x, nextY)) {
      entity.y = nextY;
      moved = true;
    }

    return moved;
  }

  function findSpawn(preferredX = null, preferredY = null, maxRadius = null) {
    if (!map) return null;

    const startX = Number.isInteger(preferredX) ? preferredX : Math.floor(map.width / 2);
    const startY = Number.isInteger(preferredY) ? preferredY : Math.floor(map.height / 2);
    const radiusLimit = Number.isInteger(maxRadius) ? maxRadius : Math.max(map.width, map.height);

    if (map.isWalkable(startX, startY)) return worldCenter(startX, startY);

    for (let radius = 1; radius <= radiusLimit; radius++) {
      const minX = startX - radius;
      const maxX = startX + radius;
      const minY = startY - radius;
      const maxY = startY + radius;

      for (let x = minX; x <= maxX; x++) {
        if (map.isWalkable(x, minY)) return worldCenter(x, minY);
        if (map.isWalkable(x, maxY)) return worldCenter(x, maxY);
      }
      for (let y = minY + 1; y < maxY; y++) {
        if (map.isWalkable(minX, y)) return worldCenter(minX, y);
        if (map.isWalkable(maxX, y)) return worldCenter(maxX, y);
      }
    }

    return null;
  }

  function worldCenter(cellX, cellY) {
    return {
      x: cellX * map.cellWidth + map.cellWidth / 2,
      y: cellY * map.cellHeight + map.cellHeight / 2,
      cellX,
      cellY
    };
  }

  function hasVisibleLayer(image) {
    return image > 0 && image !== EMPTY_IMAGE;
  }

  function drawDebug(ctx) {
    if (!map) return false;

    const left = Math.max(0, Math.floor(G.Camera.left() / map.cellWidth) - 1);
    const top = Math.max(0, Math.floor(G.Camera.top() / map.cellHeight) - 1);
    const right = Math.min(map.width - 1, Math.ceil((G.Camera.left() + G.Camera.width) / map.cellWidth) + 1);
    const bottom = Math.min(map.height - 1, Math.ceil((G.Camera.top() + G.Camera.height) / map.cellHeight) + 1);

    ctx.fillStyle = '#1b221d';
    ctx.fillRect(0, 0, map.pixelWidth, map.pixelHeight);

    for (let y = top; y <= bottom; y++) {
      for (let x = left; x <= right; x++) {
        const cell = map.cell(x, y);
        if (!cell) continue;

        const px = x * map.cellWidth;
        const py = y * map.cellHeight;

        if (!cell.walkable) {
          ctx.fillStyle = '#2e1717';
          ctx.fillRect(px, py, map.cellWidth, map.cellHeight);
        } else if (hasVisibleLayer(cell.frontImage) || hasVisibleLayer(cell.middleImage)) {
          ctx.fillStyle = '#202a24';
          ctx.fillRect(px, py, map.cellWidth, map.cellHeight);
        }
      }
    }

    ctx.strokeStyle = '#384039';
    ctx.lineWidth = 1 / G.Camera.scale;
    ctx.strokeRect(0, 0, map.pixelWidth, map.pixelHeight);
    return true;
  }

  return Object.freeze({
    load,
    canOccupyWorld,
    movePoint,
    findSpawn,
    drawDebug,
    get map() { return map; },
    get manifest() { return manifest; },
    get status() { return status; },
    get error() { return error; }
  });
})();
