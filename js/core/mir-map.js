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

    // Zircon reads one background entry for every 2x2 cell block.
    const backWidth = Math.floor(width / 2);
    const backHeight = Math.floor(height / 2);
    const backCount = backWidth * backHeight;
    const cellCount = width * height;
    const cellDataOffset = HEADER_SIZE + backCount * 3;

    // Some valid MIR3 maps omit only the final unused padding byte.
    // Every meaningful byte of the final cell still has to exist.
    const minimumBytes = cellDataOffset + cellCount * CELL_SIZE - 1;
    if (bytes.length < minimumBytes) {
      throw new Error(`Invalid MIR map: expected at least ${minimumBytes} bytes for ${width}x${height}, got ${bytes.length}`);
    }

    const backFile = new Uint8Array(backCount);
    const backImage = new Uint16Array(backCount);

    let offset = HEADER_SIZE;
    for (let x = 0; x < backWidth; x++) {
      for (let y = 0; y < backHeight; y++) {
        const target = y * backWidth + x;
        backFile[target] = bytes[offset];
        backImage[target] = readUInt16LE(bytes, offset + 1);
        offset += 3;
      }
    }

    const rawFlag = new Uint8Array(cellCount);
    const walkable = new Uint8Array(cellCount);
    const middleAnimation = new Uint8Array(cellCount);
    const frontAnimation = new Uint8Array(cellCount);
    const middleFile = new Uint8Array(cellCount);
    const frontFile = new Uint8Array(cellCount);

    // Zircon stores these as int after reading UInt16 and adding +1.
    // 65535 therefore becomes 65536 and must not wrap to 0.
    const middleImage = new Uint32Array(cellCount);
    const frontImage = new Uint32Array(cellCount);
    const light = new Uint8Array(cellCount);

    let walkableCount = 0;
    const libraries = new Set();
    for (let i = 0; i < backCount; i++) libraries.add(backFile[i]);

    for (let x = 0; x < width; x++) {
      for (let y = 0; y < height; y++) {
        const source = cellDataOffset + (x * height + y) * CELL_SIZE;
        const target = y * width + x;
        const flag = bytes[source];

        rawFlag[target] = flag;
        middleAnimation[target] = bytes[source + 1];

        const frontAnim = bytes[source + 2];
        frontAnimation[target] = frontAnim === 255 ? 0 : frontAnim;

        frontFile[target] = bytes[source + 3];
        middleFile[target] = bytes[source + 4];
        middleImage[target] = readUInt16LE(bytes, source + 5) + 1;
        frontImage[target] = readUInt16LE(bytes, source + 7) + 1;
        light[target] = (bytes[source + 12] & 0x0F) * 2;

        // Zircon marks a cell blocked when either of the two movement bits is absent.
        const canWalk = (flag & 0x01) === 0x01 && (flag & 0x02) === 0x02;
        walkable[target] = canWalk ? 1 : 0;
        if (canWalk) walkableCount += 1;

        libraries.add(frontFile[target]);
        libraries.add(middleFile[target]);
      }
    }

    const cellWidth = G.Config.mirCellWidth;
    const cellHeight = G.Config.mirCellHeight;
    const libraryIds = Object.freeze(Array.from(libraries).sort((a, b) => a - b));

    function validCell(x, y) {
      return Number.isInteger(x) && Number.isInteger(y) && x >= 0 && x < width && y >= 0 && y < height;
    }

    function cellIndex(x, y) {
      return y * width + x;
    }

    return Object.freeze({
      width,
      height,
      pixelWidth: width * cellWidth,
      pixelHeight: height * cellHeight,
      cellWidth,
      cellHeight,
      backWidth,
      backHeight,
      walkableCount,
      libraryIds,

      isWalkable(x, y) {
        return validCell(x, y) && walkable[cellIndex(x, y)] === 1;
      },

      isBlocked(x, y) {
        return !this.isWalkable(x, y);
      },

      cell(x, y) {
        if (!validCell(x, y)) return null;
        const index = cellIndex(x, y);
        const middleAnim = middleAnimation[index];
        const frontAnim = frontAnimation[index];

        return {
          flag: rawFlag[index],
          walkable: walkable[index] === 1,
          middleFile: middleFile[index],
          middleImage: middleImage[index],
          middleAnimation: middleAnim,
          middleAnimationCount: middleAnim & 0x0F,
          middleAnimationBlend: (middleAnim & 0x80) !== 0,
          frontFile: frontFile[index],
          frontImage: frontImage[index],
          frontAnimation: frontAnim,
          frontAnimationCount: frontAnim & 0x0F,
          frontAnimationBlend: (frontAnim & 0x80) !== 0,
          light: light[index]
        };
      },

      background(x, y) {
        const bx = Math.floor(x / 2);
        const by = Math.floor(y / 2);
        if (bx < 0 || bx >= backWidth || by < 0 || by >= backHeight) return null;
        const index = by * backWidth + bx;
        return { file: backFile[index], image: backImage[index] };
      },

      worldToCell(x, y) {
        return {
          x: Math.floor(x / cellWidth),
          y: Math.floor(y / cellHeight)
        };
      },

      cellToWorld(x, y) {
        return {
          x: x * cellWidth,
          y: y * cellHeight
        };
      }
    });
  }

  async function load(url) {
    const response = await fetch(url);
    if (!response.ok) throw new Error(`Unable to load MIR map: ${url}`);
    return parse(await response.arrayBuffer());
  }

  return Object.freeze({
    HEADER_SIZE,
    CELL_SIZE,
    parse,
    load
  });
})();
