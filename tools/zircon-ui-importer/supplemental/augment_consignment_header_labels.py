#!/usr/bin/env python3
"""Expand the ten deterministic Consignment CreateHeaderLabel() call sites."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


PREFIX = "deterministic-consignment-headers:"
HEADERS = (
    ("SortLabel", "SearchTab", 10, 6, 50, 20, "ConsignmentDialogSortByLabel"),
    ("ItemTypesLabel", "SearchTab", 4, 32, 160, 20, "ConsignmentDialogItemTypesLabel"),
    ("SearchNameLabel", "SearchTab", 180, 32, 172, 20, "ConsignmentDialogNameLabel"),
    ("SearchLevelLabel", "SearchTab", 356, 32, 55, 20, "ConsignmentDialogLevelLabel"),
    ("SearchPriceLabel", "SearchTab", 415, 32, 110, 20, "ConsignmentDialogPriceLabel"),
    ("SellerLabel", "SearchTab", 525, 32, 160, 20, "ConsignmentDialogSellerLabel"),
    ("ConsignNameLabel", "ConsignTab", 14, 32, 250, 20, "ConsignmentDialogNameLabel"),
    ("ConsignLevelLabel", "ConsignTab", 260, 32, 60, 20, "ConsignmentDialogLevelLabel"),
    ("ConsignPriceLabel", "ConsignTab", 325, 32, 140, 20, "ConsignmentDialogPriceLabel"),
    ("ConsignDateLabel", "ConsignTab", 479, 32, 200, 20, "ConsignmentDialogConsignDateLabel"),
)


def english(spec: dict, key: str) -> str:
    return str(((spec.get("language") or {}).get("English") or {}).get(key) or "")


def assert_source(root: Path) -> None:
    text = (root / "Client/Scenes/Views/ConsignmentDialog.cs").read_text(encoding="utf-8-sig")
    calls = (
        "SortLabel = CreateHeaderLabel(SearchTab, new Point(10, 6), new Size(50, 20), CEnvir.Language.ConsignmentDialogSortByLabel);",
        "ItemTypesLabel = CreateHeaderLabel(SearchTab, new Point(4, 32), new Size(160, 20), CEnvir.Language.ConsignmentDialogItemTypesLabel);",
        "SearchNameLabel = CreateHeaderLabel(SearchTab, new Point(180, 32), new Size(172, 20), CEnvir.Language.ConsignmentDialogNameLabel);",
        "SearchLevelLabel = CreateHeaderLabel(SearchTab, new Point(356, 32), new Size(55, 20), CEnvir.Language.ConsignmentDialogLevelLabel);",
        "SearchPriceLabel = CreateHeaderLabel(SearchTab, new Point(415, 32), new Size(110, 20), CEnvir.Language.ConsignmentDialogPriceLabel);",
        "SellerLabel = CreateHeaderLabel(SearchTab, new Point(525, 32), new Size(160, 20), CEnvir.Language.ConsignmentDialogSellerLabel);",
        "ConsignNameLabel = CreateHeaderLabel(ConsignTab, new Point(14, 32), new Size(250, 20), CEnvir.Language.ConsignmentDialogNameLabel);",
        "ConsignLevelLabel = CreateHeaderLabel(ConsignTab, new Point(260, 32), new Size(60, 20), CEnvir.Language.ConsignmentDialogLevelLabel);",
        "ConsignPriceLabel = CreateHeaderLabel(ConsignTab, new Point(325, 32), new Size(140, 20), CEnvir.Language.ConsignmentDialogPriceLabel);",
        "ConsignDateLabel = CreateHeaderLabel(ConsignTab, new Point(479, 32), new Size(200, 20), CEnvir.Language.ConsignmentDialogConsignDateLabel);",
        "private static DXLabel CreateHeaderLabel(DXControl parent, Point location, Size size, string text)",
        "DrawFormat = TextFormatFlags.HorizontalCenter | TextFormatFlags.VerticalCenter",
        "ForeColour = Constants.PrimaryColour",
        "IsControl = false",
    )
    for needle in calls:
        if needle not in text:
            raise SystemExit(f"Consignment header helper source changed: missing {needle!r}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--zircon-root", type=Path, required=True)
    args = parser.parse_args()

    assert_source(args.zircon_root)
    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    window = next((w for w in spec.get("windows", []) if w.get("field") == "ConsignmentBox"), None)
    if window is None:
        raise SystemExit("ConsignmentBox missing")
    controls = [control for control in window.get("controls", []) if not str(control.get("sourceGenerated") or "").startswith(PREFIX)]
    existing = {str(control.get("name") or "") for control in controls}
    collisions = sorted(existing & {row[0] for row in HEADERS})
    if collisions:
        raise SystemExit(f"Consignment helper headers became parser-materialised; reconcile instead of duplicate: {collisions}")

    generated = []
    for name, parent, x, y, width, height, key in HEADERS:
        text = english(spec, key)
        if not text:
            raise SystemExit(f"Consignment header source text unresolved: {key}")
        generated.append({
            "name": name,
            "type": "DXLabel",
            "properties": {
                "Parent": parent,
                "Location": f"new Point({x}, {y})",
                "Size": f"new Size({width}, {height})",
                "AutoSize": "false",
                "DrawFormat": "TextFormatFlags.HorizontalCenter | TextFormatFlags.VerticalCenter",
                "Text": f"CEnvir.Language.{key}",
                "ForeColour": "Constants.PrimaryColour",
                "IsControl": "false",
            },
            "resolvedText": text,
            "sourceGenerated": PREFIX + "ConsignmentDialog.CreateHeaderLabel call",
            "sourceHelper": "CreateHeaderLabel",
            "runtimePayloadInvented": False,
        })

    window["controls"] = generated + controls
    window["deterministicConsignmentHeaderLabels"] = {
        "passed": True,
        "callSites": 10,
        "controlsAdded": 10,
        "helper": "CreateHeaderLabel",
        "runtimePayloadsInvented": False,
    }
    args.spec.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("Consignment CreateHeaderLabel expanded: 10 exact constructor call sites")


if __name__ == "__main__":
    main()
