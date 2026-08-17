#!/usr/bin/env python3
"""Promote deterministic post-constructor states missed by flat C# parsing.

These values come from checked-in Zircon defaults plus constructor method calls
whose side effects the static initializer parser cannot execute (GetAcceptableResize,
SetDefaultSize, OnSizeChanged, OnClientAreaChanged, UpdateButtonLocations and
property setters). Runtime player/map/quest/monster data is never fabricated.
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

    # ChatTextBox calls SetDefaultSize() after creating its controls. With the
    # initial TextBox 350x100, ChatMode 60 and Options 50, SetClientSize receives
    # 475x100. No title/top/footer => DXWindow overhead is 18x18, final 493x118.
    chat = by_field["ChatTextBox"]
    chat["root"]["Size"] = "new Size(493, 118)"
    chat["root"]["SourceSizeExpression"] = "SetDefaultSize(): SetClientSize(new Size(350 + 60 + 15 + 50, 100))"
    chat_mode = control(chat, "ChatModeButton")
    chat_mode["properties"]["Location"] = "new Point(9, 8)"
    chat_mode["sourcePostConstructor"] = "after SetDefaultSize: ClientArea.Location + y - 1"
    chat_text = control(chat, "TextBox")
    chat_text["properties"]["Location"] = "new Point(74, 9)"
    chat_text["properties"]["Size"] = "new Size(355, 100)"
    chat_text["sourcePostConstructor"] = "OnSizeChanged after SetClientSize: client width 475 - 60 - 10 - 50"
    chat_options = control(chat, "OptionsButton")
    chat_options["properties"]["Location"] = "new Point(434, 8)"
    chat_options["sourcePostConstructor"] = "after SetDefaultSize: ClientArea.X + TextBox.Width + ChatMode.Width + 10"
    chat["constructorFinalState"] = {
        "size": [493, 118],
        "clientArea": [9, 9, 475, 100],
        "canResizeWidth": True,
        "canResizeHeight": False,
        "runtimeChatTextInvented": False,
    }

    # QuestTracker creates ScrollBar/TextPanel before setting Size=250x100. The
    # final Size assignment invokes OnSizeChanged and overwrites both geometries.
    tracker = by_field["QuestTrackerBox"]
    tracker["root"]["Size"] = "new Size(250, 100)"
    scroll = control(tracker, "ScrollBar")
    scroll["properties"].update({
        "Location": "new Point(227, 9)",
        "Size": "new Size(14, 82)",
        "VisibleSize": "82",
        "HideWhenNoScroll": "true",
    })
    scroll["sourcePostConstructor"] = "OnSizeChanged(Size=250x100); ResizeBuffer=9"
    text_panel = control(tracker, "TextPanel")
    text_panel["properties"]["Location"] = "new Point(0, 9)"
    text_panel["properties"]["Size"] = "new Size(226, 82)"
    text_panel["sourcePostConstructor"] = "OnSizeChanged(Size=250x100); width=250-14-1-9, height=100-18"
    tracker["constructorFinalState"] = {
        "size": [250, 100],
        "scrollBar": [227, 9, 14, 82],
        "textPanel": [0, 9, 226, 82],
        "opacityIdle": 0.0,
        "opacityHover": 0.3,
        "runtimeQuestLinesInvented": False,
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
        "ChatTextBox": chat["root"]["Size"],
        "QuestTrackerBox": tracker["root"]["Size"],
        "MonsterBox": monster["root"]["Size"],
    }
    expected = {
        "BeltBox": "new Size(64, 54)",
        "MiniMapBox": "new Size(200, 200)",
        "ChatTextBox": "new Size(493, 118)",
        "QuestTrackerBox": "new Size(250, 100)",
        "MonsterBox": "new Size(186, 175)",
    }
    if checks != expected:
        raise SystemExit(f"Constructor final-state promotion drifted: {checks}")

    spec["constructorFinalStatePass"] = {
        "windowsPromoted": ["BeltBox", "MiniMapBox", "ChatTextBox", "QuestTrackerBox", "MonsterBox"],
        "source": "Zircon constructors + checked-in Config.cs defaults + DXWindow GetSize/GetClientArea",
    }
    args.spec.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("Constructor final states promoted: Belt, MiniMap, ChatTextBox, QuestTracker, MonsterBox")


if __name__ == "__main__":
    main()