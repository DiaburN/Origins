#!/usr/bin/env python3
"""Promote CompanionDialog deterministic empty-slot artwork.

CompanionDialog manually draws Interface #99/#100/#101/#102 at 20% opacity in
its four equipment cells while the cell has no item. The companion model,
health/experience/hunger fills and all numeric values remain runtime-only.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def point(expr: str) -> tuple[int, int] | None:
    match = re.search(r"new\s+Point\(\s*(-?\d+)\s*,\s*(-?\d+)\s*\)", str(expr or ""))
    return (int(match.group(1)), int(match.group(2))) if match else None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", type=Path, required=True)
    args = parser.parse_args()

    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    companion = next((w for w in spec.get("windows", []) if w.get("field") == "CompanionBox"), None)
    if not companion:
        raise SystemExit("CompanionBox missing from generated manifest")

    expected = {
        (198, 17): ("Bag", 99),
        (198, 59): ("Head", 100),
        (198, 103): ("Back", 101),
        (24, 17): ("Food", 102),
    }
    promoted = []
    for control in companion.get("controls", []):
        if control.get("type") != "DXItemCell":
            continue
        props = control.get("properties", {})
        if "GridType.CompanionEquipment" not in str(props.get("GridType", "")):
            continue
        loc = point(props.get("Location", ""))
        if loc not in expected:
            continue
        slot, index = expected[loc]
        control["emptyPlaceholderAsset"] = {
            "library": "Interface",
            "index": index,
            "opacity": 0.2,
            "slot": slot,
            "source": "CompanionDialog.Draw(DXItemCell cell, int index)",
        }
        promoted.append((slot, index, control.get("name")))

    if len(promoted) != 4 or {row[1] for row in promoted} != {99, 100, 101, 102}:
        raise SystemExit(f"Companion empty-slot promotion drifted: {promoted}")

    companion["customDrawContract"] = {
        "mode": "MIXED_DETERMINISTIC_AND_RUNTIME",
        "deterministic": "empty equipment placeholders Interface 99-102 at opacity 0.2",
        "runtimeOnly": [
            "CompanionDisplay MonsterObject body/shadow",
            "HealthBar GameInter 4375 fill",
            "ExperienceBar GameInter 4310 fill",
            "HungerBar GameInter 4311 fill",
            "WeightBar GameInter 4312 fill",
            "name/level/experience/hunger/weight values",
        ],
        "runtimeCompanionDataInvented": False,
    }
    spec["companionReferencePass"] = {
        "emptySlotAssetsPromoted": 4,
        "indices": [99, 100, 101, 102],
        "runtimeCompanionDataInvented": False,
    }
    args.spec.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("Companion empty-slot artwork promoted: Interface 99/100/101/102 at 20% opacity")


if __name__ == "__main__":
    main()
