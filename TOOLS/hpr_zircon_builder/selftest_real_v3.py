#!/usr/bin/env python3
from __future__ import annotations

import gzip
import json
import struct
import tempfile
from pathlib import Path

import origins_hpr_zircon as core
import origins_hpr_zircon_v2 as real


def bgra(width: int, height: int, seed: int) -> bytes:
    data = bytearray()
    for y in range(height):
        for x in range(width):
            data.extend(((seed + x) & 255, (seed + y * 3) & 255, (seed + x + y) & 255, 255))
    return bytes(data)


def image_record(width: int, height: int, x: int, y: int, sx: int, sy: int, shadow: int, raw: bytes) -> bytes:
    payload = gzip.compress(raw, compresslevel=9)
    return struct.pack("<HHhhhhBI", width, height, x, y, sx, sy, shadow, len(payload)) + payload


def make_real_v3(path: Path) -> None:
    records = [
        image_record(8, 7, -4, -10, 1, 2, 1, bgra(8, 7, 10)),
        image_record(7, 6, -3, -9, 1, 1, 1, bgra(7, 6, 30)),
        None,
        image_record(5, 4, 2, -7, 0, 1, 0, bgra(5, 4, 70)),
    ]
    count = len(records)
    table_end = 24 + count * 4
    physical = table_end
    stored_offsets = []
    data_records = bytearray()
    for record in records:
        if record is None:
            stored_offsets.append(0)
            continue
        stored_offsets.append(physical - len(core.SIGNATURE))
        data_records.extend(record)
        physical += len(record)
    frame_set_offset = physical
    # Tail bytes deliberately look unlike image records: reader must stop here.
    frame_tail = b"FRAMESET_V3_TEST" + bytes(range(32))
    header = (
        core.SIGNATURE
        + struct.pack("<III", 3, count, frame_set_offset)
        + struct.pack(f"<{count}I", *stored_offsets)
    )
    assert len(header) == table_end
    path.write_bytes(header + data_records + frame_tail)


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="origins_real_v3_") as tmp:
        root = Path(tmp)
        hpr = root / "000.hpr"
        make_real_v3(hpr)
        profile = core.MonsterProfile(
            hpr="000",
            status="AUTO_CUSTOM",
            slot_count=4,
            nonempty_image_count=3,
            actions=[
                core.ActionProfile("Standing", "Standing", 0, 1, 1, 500, semantic="Standing", semantic_source="safe-structural"),
                core.ActionProfile("Attack1", "Combat1", 1, 1, 1, 100),
            ],
            source="real-v3-selftest",
        )
        parsed = core.parse_hpr(hpr, profile, semantics={})
        assert parsed.version == 3
        assert parsed.image_record_layout == "hispa_v3_u16_xy_shadow"
        assert len(parsed.images) == 4
        assert [x.present for x in parsed.images] == [True, True, False, True]
        assert parsed.images[0].x == -4 and parsed.images[0].y == -10
        assert parsed.images[1].shadow_x == 1 and parsed.images[1].shadow_y == 1

        result = core.build_one(parsed, root / "OUT", write_zl=True, export_png=False)
        zl = root / "OUT" / result.zl_file
        check = core.validate_zl2(zl)
        assert check["slot_count"] == 4
        assert check["entry_count"] == 3
        generated = json.loads((root / "OUT" / "MONSTERS" / "000" / "CURSOR_PROFILE.json").read_text())
        assert generated["image_record_layout"] == "hispa_v3_u16_xy_shadow"
        assert generated["actions"][0]["source_indices"][0] == 0
        print("REAL V3 SELFTEST OK")
        print(f"layout={parsed.image_record_layout} slots={len(parsed.images)} present={sum(x.present for x in parsed.images)}")
        print(f"ZL2 slots={check['slot_count']} entries={check['entry_count']} size={check['size_bytes']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
