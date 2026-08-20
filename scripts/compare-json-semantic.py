#!/usr/bin/env python3
"""Compare two JSON snapshot files by data, not serialization details.

Object member order, indentation, BOM and line endings are irrelevant. Array
order remains significant because Zircon snapshot collection order is part of
the deterministic export contract.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def first_difference(a: Any, b: Any, path: str = "$") -> str | None:
    if type(a) is not type(b):
        return f"{path}: type {type(a).__name__} != {type(b).__name__}"

    if isinstance(a, dict):
        a_keys, b_keys = set(a), set(b)
        if a_keys != b_keys:
            missing = sorted(a_keys - b_keys)
            extra = sorted(b_keys - a_keys)
            return f"{path}: keys differ; missing_in_rebuilt={missing}, extra_in_rebuilt={extra}"
        for key in sorted(a_keys):
            diff = first_difference(a[key], b[key], f"{path}.{key}")
            if diff:
                return diff
        return None

    if isinstance(a, list):
        if len(a) != len(b):
            return f"{path}: length {len(a)} != {len(b)}"
        for index, (left, right) in enumerate(zip(a, b)):
            diff = first_difference(left, right, f"{path}[{index}]")
            if diff:
                return diff
        return None

    if a != b:
        return f"{path}: {a!r} != {b!r}"
    return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("canonical", type=Path)
    parser.add_argument("rebuilt", type=Path)
    args = parser.parse_args()

    canonical = load(args.canonical)
    rebuilt = load(args.rebuilt)
    diff = first_difference(canonical, rebuilt)
    if diff:
        print("SEMANTIC JSON MISMATCH")
        print(diff)
        return 1

    if isinstance(canonical, list):
        count = len(canonical)
        print(f"SEMANTIC JSON MATCH: {count} array rows")
    else:
        print("SEMANTIC JSON MATCH")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
