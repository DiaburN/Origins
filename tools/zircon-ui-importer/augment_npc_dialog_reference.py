#!/usr/bin/env python3
"""Promote NPCDialog's deterministic custom-frame constructor state.

NPCDialog overrides Draw() and does not use DXWindow.DrawEdges(): it composes
GameInter 380 header, zero-to-six 381 rows and 382 footer. The neutral source
state after SetSize(0) is 380x204 with no runtime NPC page text/rows.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def get_control(window: dict, name: str) -> dict:
    control = next((c for c in window.get("controls", []) if c.get("name") == name), None)
    if not control:
        raise SystemExit(f"NPCDialog control missing: {name}")
    return control


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", type=Path, required=True)
    args = parser.parse_args()

    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    npc = next((w for w in spec.get("windows", []) if w.get("field") == "NPCBox"), None)
    if not npc:
        raise SystemExit("NPCBox missing from generated manifest")

    refs = set(spec.setdefault("assetRefs", {}).setdefault("GameInter", []))
    refs.update({380, 381, 382, 385, 387})
    spec["assetRefs"]["GameInter"] = sorted(refs)

    root = npc.setdefault("root", {})
    root["Size"] = "new Size(380, 204)"
    root["CustomFrame"] = "NPCDialog"
    root["SourceSizeExpression"] = "SetSize(0): 380 x (_HeaderHeight 140 + _FooterHeight 64)"

    page_container = get_control(npc, "PageTextContainer")
    page_container["properties"]["Location"] = "new Point(15, 45)"
    page_container["properties"]["Size"] = "new Size(350, 145)"
    page_container["sourcePostConstructor"] = "SetSize(0): viewport height = 204 - 45 - 14"

    page_text = get_control(npc, "PageText")
    page_text["properties"]["Size"] = "new Size(350, 0)"
    page_text["sourcePostConstructor"] = "SetSize(0): no runtime NPC page text in neutral state"

    scroll = get_control(npc, "ScrollBar")
    scroll["properties"]["Size"] = "new Size(14, 145)"
    scroll["sourcePostConstructor"] = "SetSize(0): 204 - ScrollBar.Y 45 - 14"

    close = get_control(npc, "CloseButton")
    close["properties"]["Location"] = "new Point(345, 3)"
    close["sourcePostConstructor"] = "380 - Interface#15 width 32 - 3"

    npc["npcCustomFrame"] = {
        "headerIndex": 380,
        "rowIndex": 381,
        "footerIndex": 382,
        "headerHeight": 140,
        "footerHeight": 64,
        "rowHeight": 20,
        "maxRows": 6,
        "initialRows": 0,
        "initialFooterY": 140,
        "initialSize": [380, 204],
        "runtimePageDataInvented": False,
        "scrollbar": {"up": 387, "down": 385, "thumb": -1},
    }

    required = {380, 381, 382, 385, 387}
    if not required.issubset(set(spec["assetRefs"]["GameInter"])):
        raise SystemExit("NPC custom-frame asset promotion failed")
    if root["Size"] != "new Size(380, 204)":
        raise SystemExit("NPC neutral size promotion failed")

    spec["npcDialogReferencePass"] = {
        "customFramePromoted": True,
        "assetsPromoted": sorted(required),
        "neutralRows": 0,
    }
    args.spec.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("NPCDialog custom frame promoted: GameInter 380/381/382 + scrollbar 385/387; neutral 380x204")


if __name__ == "__main__":
    main()
