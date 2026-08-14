import { gunzipSync } from "node:zlib";

export interface LibHeader {
  version: number;
  imageCount: number;
  frameSeek: number;
  imageOffsets: number[];
}

export interface LibImageMeta {
  index: number;
  offset: number;
  width: number;
  height: number;
  x: number;
  y: number;
  shadowX: number;
  shadowY: number;
  shadow: number;
  compressedLength: number;
  hasMask: boolean;
  mask?: {
    width: number;
    height: number;
    x: number;
    y: number;
    compressedLength: number;
  };
}

function dataView(bytes: Uint8Array): DataView {
  return new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
}

export function readLibHeader(bytes: Uint8Array): LibHeader {
  if (bytes.length < 8) throw new Error("LIB file is too small.");
  const view = dataView(bytes);
  const version = view.getInt32(0, true);
  const imageCount = view.getInt32(4, true);

  if (version < 2) throw new Error(`Unsupported Crystal LIB version ${version}.`);
  if (imageCount < 0) throw new Error("Invalid Crystal LIB image count.");

  let cursor = 8;
  let frameSeek = 0;
  if (version >= 3) {
    frameSeek = view.getInt32(cursor, true);
    cursor += 4;
  }

  if (cursor + imageCount * 4 > bytes.length) throw new Error("Truncated Crystal LIB index table.");

  const imageOffsets: number[] = [];
  for (let i = 0; i < imageCount; i++) {
    imageOffsets.push(view.getInt32(cursor, true));
    cursor += 4;
  }

  return { version, imageCount, frameSeek, imageOffsets };
}

export function readImageMeta(bytes: Uint8Array, header: LibHeader, index: number): LibImageMeta | null {
  if (index < 0 || index >= header.imageCount) return null;
  const offset = header.imageOffsets[index];
  if (offset <= 0 || offset + 17 > bytes.length) return null;

  const view = dataView(bytes);
  let cursor = offset;

  const width = view.getInt16(cursor, true); cursor += 2;
  const height = view.getInt16(cursor, true); cursor += 2;
  const x = view.getInt16(cursor, true); cursor += 2;
  const y = view.getInt16(cursor, true); cursor += 2;
  const shadowX = view.getInt16(cursor, true); cursor += 2;
  const shadowY = view.getInt16(cursor, true); cursor += 2;
  const shadow = bytes[cursor++];
  const compressedLength = view.getInt32(cursor, true); cursor += 4;

  const hasMask = (shadow >> 7) === 1;
  const result: LibImageMeta = {
    index,
    offset,
    width,
    height,
    x,
    y,
    shadowX,
    shadowY,
    shadow,
    compressedLength,
    hasMask,
  };

  if (hasMask) {
    const maskHeader = cursor + compressedLength;
    if (maskHeader + 12 <= bytes.length) {
      result.mask = {
        width: view.getInt16(maskHeader, true),
        height: view.getInt16(maskHeader + 2, true),
        x: view.getInt16(maskHeader + 4, true),
        y: view.getInt16(maskHeader + 6, true),
        compressedLength: view.getInt32(maskHeader + 8, true),
      };
    }
  }

  return result;
}

/**
 * Decodes Crystal's primary image layer into RGBA bytes.
 * Crystal uploads the decompressed bytes to a Direct3D A8R8G8B8 texture;
 * in little-endian memory those bytes are BGRA, so ORIGINS swaps R/B here.
 */
export function decodePrimaryRgba(bytes: Uint8Array, meta: LibImageMeta): Uint8Array {
  const start = meta.offset + 17;
  const end = start + meta.compressedLength;
  if (start < 0 || end > bytes.length) throw new Error(`Image ${meta.index} data is truncated.`);

  const raw = gunzipSync(bytes.subarray(start, end));
  const expected = meta.width * meta.height * 4;
  if (raw.length < expected) {
    throw new Error(`Image ${meta.index} decoded to ${raw.length} bytes; expected at least ${expected}.`);
  }

  const rgba = new Uint8Array(expected);
  for (let i = 0; i < expected; i += 4) {
    rgba[i] = raw[i + 2];
    rgba[i + 1] = raw[i + 1];
    rgba[i + 2] = raw[i];
    rgba[i + 3] = raw[i + 3];
  }
  return rgba;
}
