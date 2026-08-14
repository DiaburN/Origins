import type { MapCell, MirMapFormat, ParsedMap } from "./types";

function i16(view: DataView, offset: number): number {
  return view.getInt16(offset, true);
}

function u16(view: DataView, offset: number): number {
  return view.getUint16(offset, true);
}

function i32(view: DataView, offset: number): number {
  return view.getInt32(offset, true);
}

function asI16(value: number): number {
  return (value << 16) >> 16;
}

function emptyCell(x: number, y: number): MapCell {
  return {
    x,
    y,
    backIndex: -1,
    backImage: 0,
    middleIndex: -1,
    middleImage: 0,
    frontIndex: -1,
    frontImage: 0,
    doorIndex: 0,
    doorOffset: 0,
    frontAnimationFrame: 0,
    frontAnimationTick: 0,
    middleAnimationFrame: 0,
    middleAnimationTick: 0,
    light: 0,
    fishingCell: false,
    sourceBlocked: false,
  };
}

export function detectMapFormat(bytes: Uint8Array): MirMapFormat {
  if (bytes.length < 20) throw new Error("Map file is too small.");

  if (bytes[2] === 0x43 && bytes[3] === 0x23) return "CSHARP_CUSTOM";
  if (bytes[0] === 0) return "WEMADE_MIR3";
  if (bytes[0] === 0x0f && bytes[5] === 0x53 && bytes[14] === 0x33) return "SHANDA_MIR3";
  if (bytes[0] === 0x15 && bytes[4] === 0x32 && bytes[6] === 0x41 && bytes[19] === 0x31)
    return "MIR2_ANTIHACK";
  if (bytes[0] === 0x10 && bytes[2] === 0x61 && bytes[7] === 0x31 && bytes[14] === 0x31)
    return "MIR2_2010";

  if ((bytes[4] === 0x0f || bytes[4] === 0x03) && bytes[18] === 0x0d && bytes[19] === 0x0a) {
    const view = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
    const width = u16(view, 0);
    const height = u16(view, 2);
    return bytes.length > 52 + width * height * 14 ? "SHANDA_MIR2_2012" : "SHANDA_MIR2";
  }

  if (bytes[0] === 0x0d && bytes[1] === 0x4c && bytes[7] === 0x20 && bytes[11] === 0x6d)
    return "HEROES";

  return "MIR2_CLASSIC";
}

export function parseMap(bytes: Uint8Array): ParsedMap {
  const format = detectMapFormat(bytes);

  switch (format) {
    case "MIR2_CLASSIC":
      return parseMir2Classic(bytes);
    case "MIR2_2010":
      return parseMir22010(bytes);
    case "WEMADE_MIR3":
      return parseWemadeMir3(bytes);
    default:
      throw new Error(`Map format ${format} is detected but not implemented in ORIGINS Map Engine V1 yet.`);
  }
}

function parseMir2Classic(bytes: Uint8Array): ParsedMap {
  const view = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
  const width = i16(view, 0);
  const height = i16(view, 2);
  let offset = 52;
  const cells: MapCell[] = [];

  if (width <= 0 || height <= 0) throw new Error("Invalid Mir2 map dimensions.");
  if (offset + width * height * 12 > bytes.length) throw new Error("Truncated Mir2 classic map.");

  for (let x = 0; x < width; x++) {
    for (let y = 0; y < height; y++) {
      const cell = emptyCell(x, y);
      cell.backIndex = 0;
      cell.middleIndex = 1;

      let backImage = i16(view, offset);
      offset += 2;
      cell.middleImage = i16(view, offset);
      offset += 2;
      cell.frontImage = i16(view, offset);
      offset += 2;
      cell.doorIndex = bytes[offset++] & 0x7f;
      cell.doorOffset = bytes[offset++];
      cell.frontAnimationFrame = bytes[offset++];
      cell.frontAnimationTick = bytes[offset++];
      cell.frontIndex = bytes[offset++] + 2;
      cell.light = bytes[offset++];

      const blockedByBackFlag = (backImage & 0x8000) !== 0;
      if (blockedByBackFlag) backImage = (backImage & 0x7fff) | 0x20000000;
      cell.backImage = backImage;
      cell.sourceBlocked = blockedByBackFlag;
      cell.fishingCell = cell.light >= 100 && cell.light <= 119;
      cells.push(cell);
    }
  }

  return { format: "MIR2_CLASSIC", width, height, cells };
}

function parseMir22010(bytes: Uint8Array): ParsedMap {
  const view = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);

  let cursor = 21;
  const encodedWidth = i16(view, cursor); cursor += 2;
  const xorKey = i16(view, cursor); cursor += 2;
  const encodedHeight = i16(view, cursor);

  const width = encodedWidth ^ xorKey;
  const height = encodedHeight ^ xorKey;
  let offset = 54;
  const cells: MapCell[] = [];

  if (width <= 0 || height <= 0) throw new Error("Invalid Mir2 2010 map dimensions.");
  if (offset + width * height * 15 > bytes.length) throw new Error("Truncated Mir2 2010 map.");

  for (let x = 0; x < width; x++) {
    for (let y = 0; y < height; y++) {
      const cell = emptyCell(x, y);
      cell.backIndex = 0;
      cell.middleIndex = 1;

      cell.backImage = i32(view, offset) ^ 0xaa38aa38;
      offset += 4;
      cell.middleImage = asI16(i16(view, offset) ^ xorKey);
      offset += 2;
      cell.frontImage = asI16(i16(view, offset) ^ xorKey);
      offset += 2;

      cell.doorIndex = bytes[offset++] & 0x7f;
      cell.doorOffset = bytes[offset++];
      cell.frontAnimationFrame = bytes[offset++];
      cell.frontAnimationTick = bytes[offset++];
      cell.frontIndex = bytes[offset++] + 2;
      cell.light = bytes[offset++];
      offset++; // unknown byte

      if (cell.frontIndex === 102) cell.frontIndex = 90;
      if (cell.frontIndex >= 255) cell.frontIndex = -1;

      // Preserve raw map data. ORIGINS creates a new collision layer when composing rooms.
      cell.sourceBlocked = false;
      cell.fishingCell = cell.light >= 100 && cell.light <= 119;
      cells.push(cell);
    }
  }

  return { format: "MIR2_2010", width, height, cells };
}

function parseWemadeMir3(bytes: Uint8Array): ParsedMap {
  const view = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
  const width = i16(view, 22);
  const height = i16(view, 24);

  if (width <= 0 || height <= 0) throw new Error("Invalid Wemade Mir3 map dimensions.");

  const grid: MapCell[][] = Array.from({ length: width }, (_, x) =>
    Array.from({ length: height }, (_, y) => emptyCell(x, y)),
  );

  // Wemade Mir3 stores one background tile record for a 2x2 cell block.
  let offset = 28;
  const blockWidth = Math.ceil(width / 2);
  const blockHeight = Math.floor(height / 2);

  for (let bx = 0; bx < blockWidth; bx++) {
    for (let by = 0; by < blockHeight; by++) {
      if (offset + 3 > bytes.length) throw new Error("Truncated Wemade Mir3 background layer.");
      const rawIndex = bytes[offset];
      const backIndex = rawIndex !== 255 ? rawIndex + 200 : -1;
      const backImage = u16(view, offset + 1) + 1;

      for (let i = 0; i < 4; i++) {
        const x = bx * 2 + (i % 2);
        const y = by * 2 + Math.floor(i / 2);
        if (x < width && y < height) {
          grid[x][y].backIndex = backIndex;
          grid[x][y].backImage = backImage;
        }
      }
      offset += 3;
    }
  }

  // Crystal's source uses this exact offset expression for the per-cell data.
  offset = 28 + 3 * Math.ceil(width / 2) * Math.floor(height / 2);

  for (let x = 0; x < width; x++) {
    for (let y = 0; y < height; y++) {
      if (offset + 14 > bytes.length) throw new Error("Truncated Wemade Mir3 cell layer.");
      const cell = grid[x][y];
      const flag = bytes[offset++];

      cell.middleAnimationFrame = bytes[offset++];
      cell.frontAnimationFrame = bytes[offset] === 255 ? 0 : bytes[offset];
      cell.frontAnimationFrame &= 0x8f;
      offset++;

      cell.frontIndex = bytes[offset] !== 255 ? bytes[offset] + 200 : -1;
      offset++;
      cell.middleIndex = bytes[offset] !== 255 ? bytes[offset] + 200 : -1;
      offset++;

      cell.middleImage = u16(view, offset) + 1;
      offset += 2;
      cell.frontImage = u16(view, offset) + 1;
      offset += 2;

      if (cell.frontImage === 1 && cell.frontIndex === 200) cell.frontIndex = -1;

      // Mir3 map records contain door-related bytes, but Crystal ignores them here.
      offset += 3;
      cell.light = bytes[offset] & 0x0f;
      offset += 2;

      const blockedByBackFlag = (flag & 0x01) !== 0x01;
      const blockedByFrontFlag = (flag & 0x02) !== 0x02;
      if (blockedByBackFlag) cell.backImage |= 0x20000000;
      if (blockedByFrontFlag) cell.frontImage |= 0x8000;

      cell.sourceBlocked = blockedByBackFlag || blockedByFrontFlag;
      cell.fishingCell = cell.light >= 100 && cell.light <= 119;
      if (!cell.fishingCell) cell.light *= 2;
    }
  }

  const cells: MapCell[] = [];
  for (let x = 0; x < width; x++) for (let y = 0; y < height; y++) cells.push(grid[x][y]);

  return { format: "WEMADE_MIR3", width, height, cells };
}
