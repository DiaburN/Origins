#!/usr/bin/env python3
"""Real-HPR entry point for ORIGINS HPR -> Zircon Monster Builder.

This module patches the generic builder with the HispaCrystal v3 layout verified
against real `000.hpr` and `001.hpr` libraries from the ORIGINS Hispa collection.

Verified v3 header/layout:
    0x00  12 bytes   b'HispaCrystal'
    0x0C  uint32     version (=3)
    0x10  uint32     slot count
    0x14  uint32     FrameSet section offset (absolute file offset)
    0x18  uint32[]   one image-record offset per slot

The image offsets are relative to the end of the 12-byte signature, therefore:
    physical_record_offset = stored_offset + 12

For a present image, the record is 17 bytes:
    uint16 width
    uint16 height
    int16  x
    int16  y
    int16  shadow_x
    int16  shadow_y
    uint8  shadow_type
    uint32 compressed_length
    byte[] gzip(BGRA32)

No image records are read through the FrameSet tail.  Slot IDs are the index in
the v3 offset table and are preserved when writing ZL2.
"""
from __future__ import annotations

import gzip
import struct
import sys
from pathlib import Path
from typing import List, Optional, Tuple

import origins_hpr_zircon as core

SIGNATURE = core.SIGNATURE
REAL_V3_LAYOUT = core.HprRecordLayout("hispa_v3_u16_xy_shadow", "<HHhhhhBI", False)
ORIGINAL_DISCOVER = core.discover_image_table


def _decode_record(data: bytes, record_offset: int, index: int, frame_set_offset: int,
                   decode_pixels: bool) -> core.HprImage:
    size = REAL_V3_LAYOUT.size
    if record_offset < 0 or record_offset + size > frame_set_offset:
        raise core.HprError(
            f"slot {index}: record 0x{record_offset:X} outside image section ending 0x{frame_set_offset:X}"
        )
    values = struct.unpack_from(REAL_V3_LAYOUT.fmt, data, record_offset)
    width, height, x, y, sx, sy, shadow_type, compressed = (int(v) for v in values)
    payload_offset = record_offset + size

    if width > 8192 or height > 8192:
        raise core.HprError(f"slot {index}: impossible dimensions {width}x{height}")
    if compressed == 0:
        # Offset-table entries normally use 0 for empty slots.  Accept a zero-size
        # record as a defensive fallback, but never turn it into an image.
        return core.HprImage(
            index=index, present=False, width=width, height=height, x=x, y=y,
            shadow_x=sx, shadow_y=sy, shadow_type=shadow_type, mask=0,
            compressed_length=0, record_offset=record_offset,
            payload_offset=payload_offset,
        )
    if width <= 0 or height <= 0:
        raise core.HprError(f"slot {index}: non-empty record has invalid dimensions {width}x{height}")
    payload_end = payload_offset + compressed
    if payload_end > frame_set_offset:
        raise core.HprError(
            f"slot {index}: gzip payload ends at 0x{payload_end:X}, beyond FrameSet offset 0x{frame_set_offset:X}"
        )
    payload = data[payload_offset:payload_end]
    if not payload.startswith(b"\x1f\x8b"):
        raise core.HprError(f"slot {index}: gzip signature missing at 0x{payload_offset:X}")
    try:
        raw = gzip.decompress(payload)
    except Exception as exc:
        raise core.HprError(f"slot {index}: gzip decompression failed: {exc}") from exc
    expected = width * height * 4
    if len(raw) != expected:
        raise core.HprError(
            f"slot {index}: BGRA payload is {len(raw)} bytes, expected {expected} for {width}x{height}"
        )

    rgba: Optional[bytes] = None
    if decode_pixels:
        # BGRA -> RGBA without changing alpha.
        ba = bytearray(raw)
        for pos in range(0, len(ba), 4):
            ba[pos], ba[pos + 2] = ba[pos + 2], ba[pos]
        rgba = bytes(ba)

    return core.HprImage(
        index=index, present=True, width=width, height=height, x=x, y=y,
        shadow_x=sx, shadow_y=sy, shadow_type=shadow_type, mask=0,
        compressed_length=compressed, record_offset=record_offset,
        payload_offset=payload_offset, rgba=rgba,
    )


def discover_real_v3(data: bytes, decode_pixels: bool = True) -> Tuple[int, core.HprRecordLayout, List[core.HprImage]]:
    if not data.startswith(SIGNATURE):
        raise core.HprError("Not a HispaCrystal HPR")
    if len(data) < 24:
        raise core.HprError("Truncated HispaCrystal v3 header")

    version, count, frame_set_offset = struct.unpack_from("<III", data, 12)
    if version != 3:
        raise core.HprError(f"discover_real_v3 called for version {version}")
    if count <= 0 or count > 1_000_000:
        raise core.HprError(f"Invalid v3 slot count {count}")
    table_start = 24
    table_end = table_start + count * 4
    if table_end > len(data):
        raise core.HprError(
            f"v3 offset table requires 0x{table_end:X} bytes but file is only 0x{len(data):X}"
        )
    if frame_set_offset < table_end or frame_set_offset > len(data):
        raise core.HprError(
            f"Invalid v3 FrameSet offset 0x{frame_set_offset:X}; table ends 0x{table_end:X}, file ends 0x{len(data):X}"
        )

    stored_offsets = struct.unpack_from(f"<{count}I", data, table_start)
    images: List[core.HprImage] = []
    present_physical: List[int] = []
    for index, stored in enumerate(stored_offsets):
        if stored == 0:
            images.append(core.HprImage(index=index, present=False))
            continue
        # Verified on real 000/001: offsets are relative to the signature length.
        physical = int(stored) + len(SIGNATURE)
        if physical < table_end or physical >= frame_set_offset:
            raise core.HprError(
                f"slot {index}: stored offset 0x{stored:X} -> physical 0x{physical:X} "
                f"outside image data 0x{table_end:X}..0x{frame_set_offset:X}"
            )
        image = _decode_record(data, physical, index, frame_set_offset, decode_pixels)
        images.append(image)
        if image.present:
            present_physical.append(physical)

    if not any(image.present for image in images):
        raise core.HprError("v3 offset table contains no valid images")

    # Strong structural validation: sorted records must not overlap and every
    # offset must identify its own record. Gaps are allowed (some libraries may
    # contain padding/auxiliary bytes), but overlap is never accepted.
    present_images = sorted((img for img in images if img.present), key=lambda x: x.record_offset)
    previous_end = table_end
    for image in present_images:
        if image.record_offset < previous_end:
            raise core.HprError(
                f"slot {image.index}: record at 0x{image.record_offset:X} overlaps previous record ending 0x{previous_end:X}"
            )
        previous_end = image.payload_offset + image.compressed_length
    if previous_end > frame_set_offset:
        raise core.HprError("image data overlaps FrameSet section")

    image_table_offset = present_images[0].record_offset if present_images else table_end
    return image_table_offset, REAL_V3_LAYOUT, images


def discover_image_table(data: bytes, decode_pixels: bool = True):
    if data.startswith(SIGNATURE) and len(data) >= 16:
        version = struct.unpack_from("<I", data, 12)[0]
        if version == 3:
            return discover_real_v3(data, decode_pixels=decode_pixels)
    # Keep old safe probing for non-v3 sources; it will fail rather than invent
    # a layout when the bytes cannot be proven.
    return ORIGINAL_DISCOVER(data, decode_pixels=decode_pixels)


# Patch only the reader.  The already-tested profile handling, ZL2 writer,
# Cursor files and MasterSheet generator stay exactly the same.
core.discover_image_table = discover_image_table


def main() -> int:
    return core.main()


if __name__ == "__main__":
    raise SystemExit(main())
