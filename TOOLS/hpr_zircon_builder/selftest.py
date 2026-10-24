#!/usr/bin/env python3
from __future__ import annotations

import gzip
import json
import struct
import tempfile
from pathlib import Path

from origins_hpr_zircon import (
    ActionProfile,
    HPR_DIRECTION_NAMES,
    MonsterProfile,
    build_one,
    parse_hpr,
    validate_zl2,
)


def bgra_pixel_bytes(width: int, height: int, seed: int) -> bytes:
    out = bytearray()
    for y in range(height):
        for x in range(width):
            b = (seed + x * 7) & 0xFF
            g = (seed + y * 11) & 0xFF
            r = (seed + x + y * 3) & 0xFF
            a = 255 if (x + y) % 3 else 180
            out.extend((b, g, r, a))
    return bytes(out)


def record(width: int, height: int, x: int, y: int, sx: int, sy: int,
           shadow: int, mask: int, raw_bgra: bytes | None) -> bytes:
    if raw_bgra is None:
        return struct.pack("<HHhhhhBBI", width, height, x, y, sx, sy, shadow, mask, 0)
    payload = gzip.compress(raw_bgra, compresslevel=9)
    return struct.pack(
        "<HHhhhhBBI", width, height, x, y, sx, sy, shadow, mask, len(payload)
    ) + payload


def make_synthetic_hpr(path: Path) -> None:
    # Parser intentionally ignores unknown bytes before the verified image table.
    header = b"HispaCrystal" + bytes([3]) + b"SELFTEST_FRAME_HEADER" + bytes(17)
    body = b"".join([
        record(6, 5, -3, -7, 1, 2, 1, 0, bgra_pixel_bytes(6, 5, 10)),
        record(5, 4, -2, -6, 1, 1, 1, 0, bgra_pixel_bytes(5, 4, 40)),
        record(0, 0, 0, 0, 0, 0, 0, 0, None),
        record(4, 3, 2, -4, 0, 1, 0, 1, bgra_pixel_bytes(4, 3, 80)),
    ])
    path.write_bytes(header + body)


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="origins_hpr_selftest_") as tmp:
        root = Path(tmp)
        hpr = root / "9999.hpr"
        make_synthetic_hpr(hpr)

        profile = MonsterProfile(
            hpr="9999",
            status="AUTO_CUSTOM",
            slot_count=4,
            nonempty_image_count=3,
            actions=[
                ActionProfile(
                    visual_action="Standing",
                    zircon_animation_slot="Standing",
                    start=0,
                    count=1,
                    stride=1,
                    delay_ms=500,
                    semantic="Standing",
                    semantic_source="safe-structural",
                ),
                ActionProfile(
                    visual_action="Attack1",
                    zircon_animation_slot="Combat1",
                    start=1,
                    count=1,
                    stride=1,
                    delay_ms=100,
                    semantic="UNKNOWN_VISUAL_ONLY",
                    semantic_source="not-inferred",
                ),
            ],
            source="selftest",
        )
        parsed = parse_hpr(hpr, profile, semantics={})
        assert parsed.version == 3
        assert parsed.image_record_layout == "u16_xy_shadow_mask"
        assert len(parsed.images) == 4
        assert sum(x.present for x in parsed.images) == 3
        assert parsed.images[0].x == -3
        assert parsed.images[0].y == -7
        assert parsed.images[2].present is False
        assert parsed.images[3].mask == 1

        result = build_one(parsed, root / "OUT", write_zl=True, export_png=True)
        zl = root / "OUT" / result.zl_file
        check = validate_zl2(zl)
        assert check["slot_count"] == 4
        assert check["entry_count"] == 3

        profile_json = json.loads(
            (root / "OUT" / "MONSTERS" / "9999" / "CURSOR_PROFILE.json").read_text(encoding="utf-8")
        )
        assert profile_json["actions"][0]["source_indices_by_direction"][HPR_DIRECTION_NAMES[0]] == [0]
        assert profile_json["mir2_to_zircon_direction_shift"] == 3

        pngs = list((root / "OUT" / "MONSTERS" / "9999" / "FRAMES_PNG").glob("*.png"))
        assert len(pngs) == 3
        print("SELFTEST OK")
        print(f"HPR layout: {parsed.image_record_layout}")
        print(f"ZL2: slots={check['slot_count']} entries={check['entry_count']} size={check['size_bytes']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
