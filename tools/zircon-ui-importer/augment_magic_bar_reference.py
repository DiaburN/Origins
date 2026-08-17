#!/usr/bin/env python3
"""Expand MagicBarDialog's deterministic constructor loop in the final manifest.

The generic C# initializer parser cannot materialize dictionary entries created
inside `for (int i = 0; i < 24; i++)`.  With Zircon's checked-in default
`Config.ShowMagicBarFrames = true`, all geometry for the empty/source-neutral
bar is deterministic. Magic assignments, school border indices and cooldowns
remain runtime player data and are intentionally not fabricated.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def control(name: str, type_name: str, properties: dict[str, str], *, generated: str) -> dict:
    return {
        "name": name,
        "type": type_name,
        "properties": properties,
        "sourceGenerated": generated,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", type=Path, required=True)
    args = parser.parse_args()

    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    window = next((item for item in spec.get("windows", []) if item.get("field") == "MagicBarBox"), None)
    if not window:
        raise SystemExit("MagicBarBox missing from generated Zircon manifest")

    root = window.setdefault("root", {})
    root["ClientSize"] = "new Size(628, 47)"
    root["Size"] = "new Size(646, 65)"
    root["SourceClientSizeExpression"] = "new Size(iconSpacing * 12 + 15 + 25, iconSpacing - 2)"
    root["SourceConfigAssumption"] = "Config.ShowMagicBarFrames=true (checked-in Config.cs default)"

    existing = []
    removed_loop_stub = 0
    for item in window.get("controls", []):
        if item.get("name") == "label" and item.get("properties", {}).get("Parent") == "pair.Value":
            removed_loop_stub += 1
            continue
        if str(item.get("name", "")).startswith("MagicBarSlot"):
            continue
        existing.append(item)

    generated = []
    icon_spacing = 49
    row_spacing = 54
    group_spacing = 5
    client_x = 9
    client_y = 9
    for i in range(24):
        slot = i + 1
        row = i // 12
        col = i % 12
        x_offset = col * icon_spacing + (col // 4) * group_spacing
        y_offset = row * row_spacing
        visible = "true" if i < 12 else "false"
        border_name = f"MagicBarSlotBorder{slot:02d}"
        icon_name = f"MagicBarSlotIcon{slot:02d}"
        generated.append(control(
            border_name,
            "DXImageControl",
            {
                "Parent": "this",
                "LibraryFile": "LibraryFile.GameInter2",
                "Location": f"new Point({client_x + x_offset}, {client_y + y_offset})",
                "Size": "new Size(48, 46)",
                "Visible": visible,
                "BackColour": "Color.FromArgb(20, 20, 20)",
                "Border": "true",
                "BorderColour": "Constants.PrimaryColour",
            },
            generated="MagicBarDialog constructor IconBorders loop",
        ))
        generated.append(control(
            icon_name,
            "DXImageControl",
            {
                "Parent": border_name,
                "LibraryFile": "LibraryFile.MagicIcon",
                "Location": "new Point(6, 5)",
                "DrawTexture": "true",
                "Border": "false",
                "Size": "new Size(36, 36)",
                "Opacity": "0.6F",
                "Visible": "true",
                "RuntimeIndex": "magic.Info.Icon or -1",
            },
            generated="MagicBarDialog constructor Icons loop",
        ))

    window["controls"] = generated + existing
    window["magicBarSourceLoop"] = {
        "slots": 24,
        "initialVisibleSlots": 12,
        "iconsPerRow": 12,
        "iconSpacing": icon_spacing,
        "rowSpacing": row_spacing,
        "groupSpacing": group_spacing,
        "frameSize": [48, 46],
        "iconSize": [36, 36],
        "iconOffset": [6, 5],
        "slotLabelFormula": "count.ToString(); bottom-right inside 36x36 icon",
        "cooldownContract": "34x34 runtime overlay; hidden when no player magic",
        "spellSetInitial": 1,
        "spellSetRange": [1, 4],
        "runtimeMagicDataInvented": False,
        "removedGenericLoopLabelStub": removed_loop_stub,
    }

    if len(generated) != 48 or removed_loop_stub != 1:
        raise SystemExit(f"MagicBar deterministic loop expansion drifted: generated={len(generated)} stub={removed_loop_stub}")
    if root.get("Size") != "new Size(646, 65)":
        raise SystemExit(f"MagicBar source-default size lost: {root}")

    args.spec.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("MagicBar source loop expanded: 24 borders/icons; default root 646x65; runtime magic data neutral")


if __name__ == "__main__":
    main()
