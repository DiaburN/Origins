#!/usr/bin/env python3
"""Promote deterministic post-constructor states missed by flat C# parsing.

These values come from checked-in Zircon defaults plus constructor method calls
whose side effects the static initializer parser cannot execute (GetAcceptableResize,
OnClientAreaChanged, UpdateButtonLocations and property setters).
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def control(window: dict, name: str) -> dict:
    result = next((item for item in window.get("controls", []) if item.get("name") == name), None)
    if not result:
        raise SystemExit(f"{window.get('field')}: source control {name} missing")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", type=Path, required=True)
    args = parser.parse_args()
    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    by_field = {item.get("field"): item for item in spec.get("windows", [])}

    # BeltDialog.GetAcceptableResize(Size.Empty): with DXItemCell.CellWidth/Height=36
    # and Globals.MaxBeltCount=10, the constructor settles at Size(64,54).
    belt = by_field["BeltBox"]
    belt["root"]["Size"] = "new Size(64, 54)"
    belt["root"]["SourceSizeExpression"] = "GetAcceptableResize(Size.Empty)"
    grid = control(belt, "Grid")
    grid["properties"]["Location"] = "new Point(9, 9)"
    grid["properties"]["GridSize"] = "new Size(1, 1)"
    grid["sourcePostConstructor"] = "OnClientAreaChanged(ClientArea, ClientArea) recreates 1x1 Grid at ClientArea.Location"
    belt["constructorFinalState"] = {
        "size": [64, 54],
        "clientArea": [9, 9, 46, 42],
        "grid": [1, 1],
        "runtimeBeltLinksInvented": False,
    }

    # MiniMapDialog static DefaultMiniMapSize plus OnClientAreaChanged/Area.Inflate.
    mini = by_field["MiniMapBox"]
    mini["root"]["Size"] = "new Size(200, 200)"
    mini["root"]["SourceSizeExpression"] = "DefaultMiniMapSize = new Size(200, 200)"
    panel = control(mini, "Panel")
    panel["properties"]["Location"] = "new Point(3, 31)"
    panel["properties"]["Size"] = "new Size(194, 172)"
    panel["sourcePostConstructor"] = "Area=ClientArea; Area.Inflate(6,6)"
    for name, y in (("SizeButton", 31), ("TransparencyButton", 51), ("BigMapButton", 71)):
        button = control(mini, name)
        button["properties"]["Location"] = f"new Point(177, {y})"
        button["sourcePostConstructor"] = "UpdateButtonLocations(); GameInter button size 20x20; rightPadding=3"
    mini["constructorFinalState"] = {
        "size": [200, 200],
        "clientArea": [9, 37, 182, 160],
        "inflatedMapArea": [3, 31, 194, 172],
        "buttonsInitiallyVisible": False,
        "runtimeMapImageInvented": False,
    }

    # MonsterDialog ends with Expanded = Config.MonsterBoxExpanded; default Config=true.
    monster = by_field["MonsterBox"]
    monster["root"]["Size"] = "new Size(186, 175)"
    monster["root"]["SourceInitialSizeExpression"] = "new Size(186,54); then Expanded=Config.MonsterBoxExpanded"
    expand = control(monster, "ExpandButton")
    expand["properties"]["Index"] = "44"
    expand["sourcePostConstructor"] = "OnExpandedChanged(true): ExpandButton.Index=44"
    details = control(monster, "DetailsPanel")
    details["properties"]["Visible"] = "true"
    details["sourcePostConstructor"] = "OnExpandedChanged(true): DetailsPanel.Visible=true"
    monster["constructorFinalState"] = {
        "expanded": True,
        "size": [186, 175],
        "collapsedSize": [186, 54],
        "configSource": "Config.MonsterBoxExpanded=true",
        "runtimeMonsterDataInvented": False,
    }

    checks = {
        "BeltBox": belt["root"]["Size"],
        "MiniMapBox": mini["root"]["Size"],
        "MonsterBox": monster["root"]["Size"],
    }
    if checks != {
        "BeltBox": "new Size(64, 54)",
        "MiniMapBox": "new Size(200, 200)",
        "MonsterBox": "new Size(186, 175)",
    }:
        raise SystemExit(f"Constructor final-state promotion drifted: {checks}")

    spec["constructorFinalStatePass"] = {
        "windowsPromoted": ["BeltBox", "MiniMapBox", "MonsterBox"],
        "source": "Zircon constructors + checked-in Config.cs defaults + DXWindow GetSize/GetClientArea",
    }
    args.spec.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("Constructor final states promoted: Belt 64x54, MiniMap 200x200, Monster expanded 186x175")


if __name__ == "__main__":
    main()
