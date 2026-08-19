#!/usr/bin/env python3
"""Promote BuffDialog's deterministic neutral constructor state.

GameScene creates the BuffBox visible. The constructor is a 30x30 translucent
DXWindow with no title/top/footer/close. Icons and resized rows are generated
only when live MapObject.User.Buffs arrive through BuffsChanged().
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", type=Path, required=True)
    args = parser.parse_args()

    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    window = next((w for w in spec.get("windows", []) if w.get("field") == "BuffBox"), None)
    if not window:
        raise SystemExit("BuffBox missing from generated manifest")

    root = window.setdefault("root", {})
    root.update({
        "Size": "new Size(30, 30)",
        "Opacity": "0.6F",
        "HasTitle": "false",
        "HasFooter": "false",
        "HasTopBorder": "false",
        "CloseButtonVisible": "false",
        "TitleLabelVisible": "false",
        "SourceNeutralState": "constructor 30x30 root; BuffsChanged creates runtime CBIcon children and resizes",
    })
    window["constructorFinalState"] = {
        "size": [30, 30],
        "opacity": 0.6,
        "visibleInGameScene": True,
        "buffIcons": 0,
        "runtimeBuffsInvented": False,
        "source": "BuffDialog constructor",
    }
    window["runtimeResizeContract"] = {
        "formula": "Size = (3 + min(6,max(1,count))*27, 3 + max(1,1+(count-1)/6)*27)",
        "iconLocation": "(3 + (i%6)*27, 3 + (i/6)*27)",
        "iconLibrary": "CBIcon",
        "runtimeBuffDataInvented": False,
    }

    if root["Size"] != "new Size(30, 30)" or root["Opacity"] != "0.6F":
        raise SystemExit(f"BuffBox neutral source state drifted: {root}")

    spec["buffReferencePass"] = {
        "neutralRootPromoted": True,
        "size": [30, 30],
        "opacity": 0.6,
        "runtimeIconsInvented": False,
    }
    args.spec.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("BuffBox neutral state promoted: 30x30, opacity 0.6, zero runtime buff icons")


if __name__ == "__main__":
    main()
