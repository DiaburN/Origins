#!/usr/bin/env python3
"""Compatibility gate for Consignment CreateHeaderLabel call sites.

The complete modern Consignment expansion is owned by
augment_consignment_deterministic_composites.py, including all ten constructor
CreateHeaderLabel(...) controls. This legacy pass must not emit duplicate labels;
it only verifies source call sites and that the modern pass already owns them.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


HEADER_NAMES = (
    "SortLabel", "ItemTypesLabel", "SearchNameLabel", "SearchLevelLabel",
    "SearchPriceLabel", "SellerLabel", "ConsignNameLabel", "ConsignLevelLabel",
    "ConsignPriceLabel", "ConsignDateLabel",
)


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

    contract = window.get("deterministicConsignmentComposites") or {}
    if contract.get("passed") is not True or contract.get("headerLabels") != 10 or contract.get("controlsAdded") != 135:
        raise SystemExit(
            "Modern Consignment deterministic pass must own header labels before legacy compatibility gate: "
            f"{contract}"
        )
    by_name = {str(control.get("name") or ""): control for control in window.get("controls", [])}
    missing = [name for name in HEADER_NAMES if f"ConsignmentHeaderSource{name}" not in by_name]
    if missing:
        raise SystemExit(f"Modern Consignment header controls missing before compatibility gate: {missing}")

    # This pass intentionally changes no controls and writes no alternate identity.
    window["consignmentHeaderCompatibility"] = {
        "passed": True,
        "callSites": 10,
        "modernOwner": "augment_consignment_deterministic_composites.py",
        "controlsAddedByCompatibilityPass": 0,
        "duplicateHeadersInvented": False,
    }
    args.spec.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("Legacy Consignment header compatibility: PASS -> modern pass owns 10 source labels; emitted=0")


if __name__ == "__main__":
    main()
