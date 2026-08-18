#!/usr/bin/env python3
"""Produce a conservative Crystal -> Zircon spell comparison.

Name equality is evidence for a candidate only, never automatic behavioral
verification. This script intentionally refuses to turn unmatched names into
new MagicInfo rows.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
from typing import Any


def norm(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.lower())


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("crystal_catalog", type=pathlib.Path)
    parser.add_argument("zircon_magic_snapshot", type=pathlib.Path)
    parser.add_argument("output", type=pathlib.Path)
    args = parser.parse_args()

    crystal = json.loads(args.crystal_catalog.read_text(encoding="utf-8"))
    zircon_rows = json.loads(args.zircon_magic_snapshot.read_text(encoding="utf-8"))

    zircon_by_norm: dict[str, list[dict[str, Any]]] = {}
    for row in zircon_rows:
        name = row.get("Name") or ""
        zircon_by_norm.setdefault(norm(name), []).append(row)

    entries: list[dict[str, Any]] = []
    for spell in crystal["spells"]:
        kind = spell["kind"]
        matches = zircon_by_norm.get(norm(spell["name"]), [])
        if kind == "map_event":
            status = "excluded_map_event"
        elif kind == "deferred_class":
            status = "deferred_unsupported_class"
        elif kind == "none":
            status = "excluded_none"
        elif len(matches) == 1:
            status = "name_match_needs_behavior_check"
        elif len(matches) > 1:
            status = "ambiguous_name_match"
        else:
            status = "needs_semantic_and_behavior_review"

        entry = {
            "crystal": {
                "name": spell["name"],
                "spellId": spell["spellId"],
                "category": spell["category"],
                "kind": kind,
                "hasDefaultMagicInfo": spell.get("hasDefaultMagicInfo", False)
            },
            "status": status,
            "verified": False,
            "zirconNameMatches": [
                {
                    "index": row.get("Index"),
                    "name": row.get("Name"),
                    "magicTypeNumeric": row.get("Magic"),
                    "classNumeric": row.get("Class")
                }
                for row in matches
            ]
        }
        entries.append(entry)

    counts: dict[str, int] = {}
    for entry in entries:
        counts[entry["status"]] = counts.get(entry["status"], 0) + 1

    output = {
        "schemaVersion": 1,
        "policy": {
            "nameMatchIsVerification": False,
            "automaticMagicInfoCreation": False,
            "requiredBeforeVerified": [
                "compare Crystal server call path",
                "compare Zircon MagicObject behavior",
                "decide native/adapted/Crystal-adapted",
                "map Crystal numeric data into Zircon fields deliberately"
            ]
        },
        "counts": counts,
        "entries": entries
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("Crystal/Zircon comparison: " + ", ".join(f"{k}={v}" for k, v in sorted(counts.items())))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
