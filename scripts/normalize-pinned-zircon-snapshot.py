#!/usr/bin/env python3
"""Normalize the committed Zircon snapshot to the pinned Zircon model.

This script is intentionally narrow. The pinned ORIGINS-DxR Zircon commit
cbf1aa919083bc13fc3f23f93772a8ab8370632d does not define
MagicInfo.LevelDelayReduction. The current snapshot contains that legacy field.
We only remove it when every occurrence is the neutral value 0; a non-zero
value aborts so no runtime behaviour can be silently discarded.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

PINNED_ZIRCON = "cbf1aa919083bc13fc3f23f93772a8ab8370632d"
LEGACY_FIELD = "LevelDelayReduction"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--magic-info", type=Path, required=True)
    parser.add_argument("--expected-count", type=int, default=174)
    args = parser.parse_args()

    rows = json.loads(args.magic_info.read_text(encoding="utf-8-sig"))
    if not isinstance(rows, list):
        raise SystemExit("MagicInfo snapshot must be a JSON array")
    if len(rows) != args.expected_count:
        raise SystemExit(
            f"Refusing normalization: expected {args.expected_count} MagicInfo rows, found {len(rows)}"
        )

    present = []
    non_neutral = []
    for row in rows:
        if LEGACY_FIELD not in row:
            continue
        present.append(row)
        value = row[LEGACY_FIELD]
        if value != 0:
            non_neutral.append((row.get("Index"), row.get("Name"), value))

    if non_neutral:
        details = ", ".join(f"{index}:{name}={value}" for index, name, value in non_neutral[:20])
        raise SystemExit(
            f"Refusing to remove {LEGACY_FIELD}: non-zero values exist ({details})"
        )

    if not present:
        print(
            f"Pinned Zircon snapshot normalization: already compatible; "
            f"{LEGACY_FIELD} absent from all {len(rows)} MagicInfo rows."
        )
        return 0

    for row in rows:
        row.pop(LEGACY_FIELD, None)

    args.magic_info.write_text(
        json.dumps(rows, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(
        f"Pinned Zircon snapshot normalization ({PINNED_ZIRCON}): "
        f"removed neutral {LEGACY_FIELD}=0 from {len(present)}/{len(rows)} MagicInfo rows."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
