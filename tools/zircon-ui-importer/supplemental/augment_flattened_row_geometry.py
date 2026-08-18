#!/usr/bin/env python3
"""Rebase source-local geometry inside deterministic flattened custom rows.

DungeonRow and FortuneCheckerRow are real DXControl composites whose constructor
expressions use `this.Size` implicitly and refer to sibling fields by their local
source names. The reference manifest intentionally flattens those children into
stable globally-unique names. This pass translates only those local references
to the already-materialised row/control identities; it does not invent geometry
or runtime data and it adds/removes no controls.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def window(spec: dict, field: str) -> dict:
    item = next((row for row in spec.get("windows", []) if row.get("field") == field), None)
    if item is None:
        raise SystemExit(f"{field} missing from generated manifest")
    return item


def require_source(root: Path) -> None:
    checks = {
        "Client/Scenes/Views/DungeonFinderDialog.cs": [
            "Size = new Size(515, 40);",
            "FavouriteImage.Location = new Point(Size.Width - FavouriteImage.Size.Width - 10, (Size.Height - FavouriteImage.Size.Height) / 2);",
        ],
        "Client/Scenes/Views/FortuneCheckerDialog.cs": [
            "Size = new Size(465, 55);",
            "CountLabelLabel.Location = new Point(320 - CountLabelLabel.Size.Width, 5);",
            "ProgressLabelLabel.Location = new Point(320 - ProgressLabelLabel.Size.Width, 20);",
            "DateLabelLabel.Location = new Point(320 - DateLabelLabel.Size.Width, 35);",
            "Location = new Point(Size.Width - 55, 34)",
        ],
    }
    for relative, needles in checks.items():
        text = (root / relative).read_text(encoding="utf-8-sig")
        for needle in needles:
            if needle not in text:
                raise SystemExit(f"Flattened row geometry source changed: {relative}: missing {needle!r}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--zircon-root", type=Path, required=True)
    args = parser.parse_args()

    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    require_source(args.zircon_root)
    controls_before = sum(len(w.get("controls") or []) for w in spec.get("windows", []))

    dungeon = window(spec, "DungeonFinderBox")
    dungeon_by = {str(c.get("name")): c for c in dungeon.get("controls", [])}
    dungeon_rebased = 0
    for index in range(1, 10):
        row = f"DungeonRowSource{index:02d}"
        favourite = f"{row}FavouriteImage"
        row_control = dungeon_by.get(row)
        favourite_control = dungeon_by.get(favourite)
        if row_control is None or favourite_control is None:
            raise SystemExit(f"Dungeon flattened row incomplete: {row}")
        if row_control.get("properties", {}).get("Size") != "new Size(515, 40)":
            raise SystemExit(f"Dungeon row size drifted: {row}: {row_control.get('properties', {}).get('Size')}")
        favourite_control.setdefault("sourceFlattenedGeometry", {})["Location"] = (
            "new Point(Size.Width - FavouriteImage.Size.Width - 10, (Size.Height - FavouriteImage.Size.Height) / 2)"
        )
        favourite_control.setdefault("properties", {})["Location"] = (
            f"new Point({row}.Size.Width - {favourite}.Size.Width - 10, "
            f"({row}.Size.Height - {favourite}.Size.Height) / 2)"
        )
        dungeon_rebased += 1

    fortune = window(spec, "FortuneCheckerBox")
    fortune_by = {str(c.get("name")): c for c in fortune.get("controls", [])}
    fortune_rebased = 0
    for index in range(1, 10):
        row = f"FortuneRowSource{index:02d}"
        row_control = fortune_by.get(row)
        if row_control is None:
            raise SystemExit(f"Fortune flattened row missing: {row}")
        if row_control.get("properties", {}).get("Size") != "new Size(465, 55)":
            raise SystemExit(f"Fortune row size drifted: {row}: {row_control.get('properties', {}).get('Size')}")

        for suffix, y in (("CountLabelLabel", 5), ("ProgressLabelLabel", 20), ("DateLabelLabel", 35)):
            name = f"{row}{suffix}"
            control = fortune_by.get(name)
            if control is None:
                raise SystemExit(f"Fortune flattened row child missing: {name}")
            control.setdefault("sourceFlattenedGeometry", {})["Location"] = f"new Point(320 - {suffix}.Size.Width, {y})"
            control.setdefault("properties", {})["Location"] = f"new Point(320 - {name}.Size.Width, {y})"
            fortune_rebased += 1

        check_name = f"{row}CheckButton"
        check = fortune_by.get(check_name)
        if check is None:
            raise SystemExit(f"Fortune flattened row child missing: {check_name}")
        check.setdefault("sourceFlattenedGeometry", {})["Location"] = "new Point(Size.Width - 55, 34)"
        check.setdefault("properties", {})["Location"] = f"new Point({row}.Size.Width - 55, 34)"
        fortune_rebased += 1

    controls_after = sum(len(w.get("controls") or []) for w in spec.get("windows", []))
    if controls_after != controls_before:
        raise SystemExit(f"Flattened row geometry changed control count: {controls_before} -> {controls_after}")

    report = {
        "passed": True,
        "version": 1,
        "dungeonLocationsRebased": dungeon_rebased,
        "fortuneLocationsRebased": fortune_rebased,
        "totalLocationsRebased": dungeon_rebased + fortune_rebased,
        "rowLocalThisSizeRebound": True,
        "rowLocalSiblingNamesRebound": True,
        "sourceExpressionsPreserved": True,
        "controlsAdded": 0,
        "controlsRemoved": 0,
        "runtimePayloadsInvented": False,
        "sourceBackedOnly": True,
    }
    spec["flattenedRowGeometryPass"] = report
    args.spec.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(
        "Flattened row geometry: PASS -> "
        f"Dungeon={dungeon_rebased}, Fortune={fortune_rebased}, total={dungeon_rebased + fortune_rebased}; controls +0"
    )


if __name__ == "__main__":
    main()
