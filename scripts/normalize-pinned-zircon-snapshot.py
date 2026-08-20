#!/usr/bin/env python3
"""Normalize the committed Zircon snapshot to the pinned Zircon model.

The normalizer is deliberately conservative. It only removes fields that are
absent from the pinned Zircon commit and only when every stored value is the
known neutral/default value. Any non-neutral value aborts, so runtime behaviour
can never be silently discarded.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

PINNED_ZIRCON = "cbf1aa919083bc13fc3f23f93772a8ab8370632d"

MAGIC_RULES: dict[str, Any] = {
    "LevelDelayReduction": 0,
}

MAP_RULES: dict[str, Any] = {
    "FireWallCount": 0,
    "FireWallLimit": False,
    "NoPets": False,
    "NoTeleport": False,
}


def load_rows(path: Path, label: str) -> list[dict[str, Any]]:
    rows = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
        raise SystemExit(f"{label} snapshot must be a JSON array of objects")
    return rows


def validate_rules(
    rows: list[dict[str, Any]],
    rules: dict[str, Any],
    label: str,
    identity_key: str,
) -> dict[str, int]:
    counts: dict[str, int] = {}
    failures: list[str] = []

    for field, neutral in rules.items():
        present = [row for row in rows if field in row]
        counts[field] = len(present)
        for row in present:
            value = row[field]
            if value != neutral or type(value) is not type(neutral):
                identity = row.get(identity_key, row.get("Index"))
                failures.append(f"{label}[{row.get('Index')}:{identity}].{field}={value!r}")

    if failures:
        details = ", ".join(failures[:30])
        raise SystemExit(
            "Refusing pinned-Zircon normalization because non-neutral unsupported values exist: "
            + details
        )

    return counts


def strip_rules(rows: list[dict[str, Any]], rules: dict[str, Any]) -> bool:
    changed = False
    for row in rows:
        for field in rules:
            if field in row:
                del row[field]
                changed = True
    return changed


def write_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text(json.dumps(rows, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--magic-info", type=Path, required=True)
    parser.add_argument("--map-info", type=Path)
    parser.add_argument("--expected-magic-count", type=int, default=174)
    args = parser.parse_args()

    map_info = args.map_info or args.magic_info.with_name(
        "LibraryCore__Library_SystemModels_MapInfo.json"
    )

    magic_rows = load_rows(args.magic_info, "MagicInfo")
    map_rows = load_rows(map_info, "MapInfo")

    if len(magic_rows) != args.expected_magic_count:
        raise SystemExit(
            f"Refusing normalization: expected {args.expected_magic_count} MagicInfo rows, "
            f"found {len(magic_rows)}"
        )

    magic_counts = validate_rules(magic_rows, MAGIC_RULES, "MagicInfo", "Name")
    map_counts = validate_rules(map_rows, MAP_RULES, "MapInfo", "Description")

    magic_changed = strip_rules(magic_rows, MAGIC_RULES)
    map_changed = strip_rules(map_rows, MAP_RULES)

    if magic_changed:
        write_rows(args.magic_info, magic_rows)
    if map_changed:
        write_rows(map_info, map_rows)

    print(f"Pinned Zircon snapshot compatibility: {PINNED_ZIRCON}")
    print(f"MagicInfo rows: {len(magic_rows)}; unsupported neutral fields seen: {magic_counts}")
    print(f"MapInfo rows: {len(map_rows)}; unsupported neutral fields seen: {map_counts}")
    print(f"Files changed: MagicInfo={magic_changed}, MapInfo={map_changed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
