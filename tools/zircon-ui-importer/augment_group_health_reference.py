#!/usr/bin/env python3
"""Promote GroupHealthDialog's deterministic neutral constructor state.

The dialog is created visible by GameScene, but its constructor sets Size=150x500
and Opacity=0. Member rows are created only from live group membership. The
neutral source reference therefore keeps the real invisible root and zero rows.
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
    window = next((w for w in spec.get("windows", []) if w.get("field") == "GroupHealthBox"), None)
    if not window:
        raise SystemExit("GroupHealthBox missing from generated manifest")

    root = window.setdefault("root", {})
    root.update({
        "Size": "new Size(150, 500)",
        "Opacity": "0F",
        "HasTitle": "false",
        "HasFooter": "false",
        "HasTopBorder": "false",
        "Movable": "false",
        "CloseButtonVisible": "false",
        "TitleLabelVisible": "false",
        "SourceNeutralState": "constructor root only; group member controls are runtime-created",
    })
    window["constructorFinalState"] = {
        "size": [150, 500],
        "opacity": 0.0,
        "visibleInGameScene": True,
        "memberRows": 0,
        "runtimeGroupMembersInvented": False,
        "source": "GroupHealthDialog constructor in GroupDialog.cs",
    }
    window["customDrawContract"] = {
        "mode": "RUNTIME_GROUP_HEALTH",
        "deterministic": "150x500 invisible root, no title/top/footer/close",
        "runtimeOnly": "member rows, names, HP fills and values",
        "runtimeGroupDataInvented": False,
    }

    if root["Size"] != "new Size(150, 500)" or root["Opacity"] != "0F":
        raise SystemExit(f"GroupHealth neutral source state drifted: {root}")

    spec["groupHealthReferencePass"] = {
        "neutralRootPromoted": True,
        "size": [150, 500],
        "opacity": 0.0,
        "runtimeRowsInvented": False,
    }
    args.spec.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("GroupHealth neutral state promoted: 150x500, opacity 0, zero runtime member rows")


if __name__ == "__main__":
    main()
