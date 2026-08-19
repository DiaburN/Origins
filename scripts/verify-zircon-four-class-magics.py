#!/usr/bin/env python3
"""Verify the ORIGINS-DxR four-class magic catalog against pinned Zircon source.

This deliberately validates source identity only. DB presence and runtime handler
coverage are separate checks and must not be inferred from enum presence.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

CLASS_RANGES = {
    "Warrior": (100, 199),
    "Wizard": (200, 299),
    "Taoist": (300, 399),
    "Assassin": (400, 499),
}


def enum_body(text: str, enum_name: str) -> str:
    match = re.search(rf"public\s+enum\s+{re.escape(enum_name)}\s*\{{", text)
    if not match:
        raise ValueError(f"enum {enum_name} not found")
    start = match.end() - 1
    depth = 0
    for index in range(start, len(text)):
        char = text[index]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start + 1:index]
    raise ValueError(f"enum {enum_name} has unbalanced braces")


def parse_magic_types(text: str) -> list[dict[str, object]]:
    body = enum_body(text, "MagicType")
    rows: list[dict[str, object]] = []
    current = -1
    for raw_line in body.splitlines():
        comment = ""
        code = raw_line
        if "//" in raw_line:
            code, comment = raw_line.split("//", 1)
        code = code.strip()
        if not code or code.startswith("["):
            continue
        match = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s*(?:=\s*([0-9]+))?\s*,?\s*$", code)
        if not match:
            continue
        name, explicit = match.groups()
        current = int(explicit) if explicit is not None else current + 1
        status = "ENUM_DEFINED"
        upper_comment = comment.upper()
        if "NOT CODED" in upper_comment:
            status = "UPSTREAM_NOT_CODED"
        elif "UNUSED" in upper_comment:
            status = "UPSTREAM_UNUSED"
        rows.append({"id": current, "name": name, "status": status})
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=pathlib.Path, required=True)
    parser.add_argument("--catalog", type=pathlib.Path, required=True)
    args = parser.parse_args()

    source_rows = parse_magic_types(args.source.read_text(encoding="utf-8-sig"))
    catalog = json.loads(args.catalog.read_text(encoding="utf-8"))

    if catalog.get("source", {}).get("commit") != "cbf1aa919083bc13fc3f23f93772a8ab8370632d":
        raise SystemExit("catalog does not pin the approved Zircon commit")

    failures: list[str] = []
    total = 0

    for class_name, (minimum, maximum) in CLASS_RANGES.items():
        expected = [row for row in source_rows if minimum <= int(row["id"]) <= maximum]
        actual = catalog.get("classes", {}).get(class_name, [])
        total += len(actual)
        if actual != expected:
            failures.append(
                f"{class_name}: catalog differs from Zircon source "
                f"(catalog={len(actual)}, source={len(expected)})"
            )

    if total != 195:
        failures.append(f"catalog total is {total}, expected 195")

    expected_not_coded = sum(
        1
        for row in source_rows
        if 100 <= int(row["id"]) <= 499 and row["status"] == "UPSTREAM_NOT_CODED"
    )
    expected_unused = sum(
        1
        for row in source_rows
        if 100 <= int(row["id"]) <= 499 and row["status"] == "UPSTREAM_UNUSED"
    )
    if expected_not_coded != 6:
        failures.append(f"source NOT CODED count changed: {expected_not_coded} != 6")
    if expected_unused != 1:
        failures.append(f"source UNUSED count changed: {expected_unused} != 1")

    if failures:
        for failure in failures:
            print(f"ERROR: {failure}", file=sys.stderr)
        return 1

    print(
        "Zircon four-class MagicType catalog verified: "
        "Warrior=38, Wizard=47, Taoist=52, Assassin=58, total=195; "
        "NOT_CODED=6, UNUSED=1"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
