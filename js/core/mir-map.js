window.G = window.G || {};

G.MirMap = (() => {
  const HEADER_SIZE = 28;
  const CELL_SIZE = 14;

  function readUInt16LE(bytes, offset) {
    return bytes[offset] | (bytes[offset + 1] << 8);
  }

  function parse(arrayBuffer) {
    if (!(arrayBuffer instanceof ArrayBuffer)) {
      throw new TypeError('MIR map parser expects an ArrayBuffer');
    }

    const bytes = new Uint8Array(arrayBuffer);
    if (bytes.length < HEADER_SIZE) {
      throw new Error('Invalid MIR map: file is smaller than the 28-byte header');
    }

    const width = readUInt16LE(bytes, 22);
    const height = readUInt16LE(bytes, 24);
    if (width <= 0 || height <= 0) {
      throw new Error(`Invalid MIR map dimensions: ${width}x${height}`);
    }

    const cellDataOffset = HEADER_SIZE + Math.floor((width * height) / 4) * 3;
    const requiredBytes = cellDataOffset + width * height * CELL_SIZE;
    if (bytes.length < requiredBytes) {
      throw new Error(`Invalid MIR map: expected at least ${requiredBytes} bytes for ${width}x${height}, got ${bytes.length}`);
    }

    const walkable = new Uint8Array(width * height);
    let walkableCount = 0;

    for (let x = 0; x < width; x++) {
      for (let y = 0; y < height; y++) {
        const sourceIndex = cellDataOffset + (x * height + y) * CELL_SIZE;
        const flag = bytes[sourceIndex];
        const valid = (flag & 0x02) === 0x02 && (flag & 0x01) === 0x01;
        const targetIndex = y * width + x;
        walkable[targetIndex] = valid ? 1 : 0;
        if (valid) walkableCount += 1;
      }
    }

    return Object.freeze({
      width,
      height,
      cellWidth: G.Config.mirCellWidth,
      cellHeight: G.Config.mirCellHeight,
      walkableCount,
      isWalkable(x, y) {
        if (!Number.isInteger(x) || !Number.isInteger(y)) return false;
        if (x < 0 || x >= width || y < 0 || y >= height) return false;
        return walkable[y * width + x] === 1;
      },
      worldToCell(x, y) {
        return {
          x: Math.floor(x / G.Config.mirCellWidth),
          y: Math.floor(y / G.Config.mirCellHeight)
        };
      },
      cellToWorld(x, y) {
        return {
          x: x * G.Config.mirCellWidth,
          y: y * G.Config.mirCellHeight
        };
      }
    });
  }

  async function load(url) {
    const response = await fetch(url);
    if (!response.ok) throw new Error(`Unable to load MIR map: ${url}`);
    return parse(await response.arrayBuffer());
  }

  return Object.freeze({ parse, load });
})();
