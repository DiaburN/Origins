#!/usr/bin/env python3
"""Materialise CompanionDialog's seven target-typed CompanionBonusStat rows.

Zircon uses `BonusStats.Add(bonusStat = new() { ... })`, so neither the DX-only
base parser nor an explicit `new Type` inventory can see these rows. The seven
row shells and their constructor-created labels are deterministic. Their bonus
stat text/value is populated later from the live companion and remains empty in
the neutral reference.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from copy import deepcopy
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from build_ui_source_spec import constructor_body, object_initializers, simple_assignments

PREFIX = "deterministic-companion-bonus:"
LEVELS = (3, 5, 7, 10, 11, 13, 15)
ROW_ROOT_KEYS = {"Size", "Visible", "Border", "BackColour", "DrawTexture"}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--zircon-root", type=Path, required=True)
    args = parser.parse_args()

    source_path = args.zircon_root / "Client/Scenes/Views/CompanionDialog.cs"
    source = source_path.read_text(encoding="utf-8-sig")
    ctor = constructor_body(source, "CompanionBonusStat")
    if not ctor:
        raise SystemExit("CompanionBonusStat constructor missing")
    root_defaults = simple_assignments(ctor, ROW_ROOT_KEYS)
    children = object_initializers(ctor)
    child_names = {str(child.get("name") or "") for child in children}
    if child_names != {"LevelLabel", "StatLabel"}:
        raise SystemExit(f"CompanionBonusStat constructor child set drifted: {sorted(child_names)}")
    if root_defaults.get("Size") != "new Size(215, 57)":
        raise SystemExit(f"CompanionBonusStat source size drifted: {root_defaults}")

    outer_ctor = constructor_body(source, "CompanionDialog")
    pattern = re.compile(
        r"BonusStats\.Add\(bonusStat\s*=\s*new\(\)\s*\{(.*?)\}\s*\);",
        re.S,
    )
    blocks = pattern.findall(outer_ctor)
    if len(blocks) != 7:
        raise SystemExit(f"Companion target-typed bonus row count drifted: {len(blocks)} != 7")
    parsed_levels = []
    for block in blocks:
        match = re.search(r"\bLevel\s*=\s*(\d+)", block)
        if not match:
            raise SystemExit("Companion target-typed bonus row lost Level initializer")
        parsed_levels.append(int(match.group(1)))
    if tuple(parsed_levels) != LEVELS:
        raise SystemExit(f"Companion bonus level sequence drifted: {parsed_levels}")
    if "BonusScrollBar.MaxValue = (BonusStats.Count * 57) + 15;" not in outer_ctor:
        raise SystemExit("Companion bonus scrollbar source range formula drifted")

    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    window = next((w for w in spec.get("windows", []) if w.get("field") == "CompanionBox"), None)
    if window is None:
        raise SystemExit("CompanionBox missing")
    controls = [
        control for control in window.get("controls", [])
        if not str(control.get("sourceGenerated") or "").startswith(PREFIX)
    ]
    generated: list[dict] = []

    for index, level in enumerate(LEVELS):
        row_name = f"CompanionBonusStatSource{index + 1:02d}"
        row_props = dict(root_defaults)
        row_props.update({
            "Parent": "BonusControl",
            "Location": f"new Point(0, {5 + index * 57})",
            "Index": str(index),
            "Level": str(level),
            "RuntimeBonusStats": "live companion bonus; absent in neutral reference",
        })
        generated.append({
            "name": row_name,
            "type": "DXControl",
            "sourceType": "CompanionBonusStat",
            "properties": row_props,
            "sourceGenerated": PREFIX + "CompanionDialog target-typed new() row",
            "runtimePayloadInvented": False,
        })
        for template in children:
            child = deepcopy(template)
            original = str(child.get("name") or "")
            child["name"] = f"{row_name}{original}"
            props = child.setdefault("properties", {})
            if props.get("Parent", "this") == "this":
                props["Parent"] = row_name
            # SetBonus()/Update() supplies runtime text; constructor labels start empty.
            if child.get("type") == "DXLabel":
                props.setdefault("Text", '""')
                child["resolvedText"] = ""
            child["sourceGenerated"] = PREFIX + "CompanionBonusStat constructor"
            child["runtimePayloadInvented"] = False
            generated.append(child)

    if len(generated) != 21:
        raise SystemExit(f"Companion bonus deterministic control count error: {len(generated)} != 21")
    window["controls"] = generated + controls
    window["deterministicCompanionBonusRows"] = {
        "passed": True,
        "rows": 7,
        "childrenPerRow": 2,
        "controlsAdded": 21,
        "levels": list(LEVELS),
        "rowHeight": 57,
        "firstY": 5,
        "scrollMax": 7 * 57 + 15,
        "runtimeBonusStatsInvented": False,
        "runtimeBonusTextInvented": False,
        "targetTypedNewSource": True,
    }
    args.spec.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("Companion bonus rows expanded: 7 rows / 21 controls; no live companion stats")


if __name__ == "__main__":
    main()
