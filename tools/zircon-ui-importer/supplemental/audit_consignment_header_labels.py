#!/usr/bin/env python3
"""Strict compatibility gate for the ten Consignment CreateHeaderLabel calls.

The controls are emitted by augment_consignment_deterministic_composites.py.
This audit preserves the older focused contract without creating a second set.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


HEADERS = {
    "SortLabel": ("SearchTab", "new Point(10, 6)", "new Size(50, 20)"),
    "ItemTypesLabel": ("SearchTab", "new Point(4, 32)", "new Size(160, 20)"),
    "SearchNameLabel": ("SearchTab", "new Point(180, 32)", "new Size(172, 20)"),
    "SearchLevelLabel": ("SearchTab", "new Point(356, 32)", "new Size(55, 20)"),
    "SearchPriceLabel": ("SearchTab", "new Point(415, 32)", "new Size(110, 20)"),
    "SellerLabel": ("SearchTab", "new Point(525, 32)", "new Size(160, 20)"),
    "ConsignNameLabel": ("ConsignTab", "new Point(14, 32)", "new Size(250, 20)"),
    "ConsignLevelLabel": ("ConsignTab", "new Point(260, 32)", "new Size(60, 20)"),
    "ConsignPriceLabel": ("ConsignTab", "new Point(325, 32)", "new Size(140, 20)"),
    "ConsignDateLabel": ("ConsignTab", "new Point(479, 32)", "new Size(200, 20)"),
}


def props(control: dict | None) -> dict:
    return (control or {}).get("properties") or {}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--zircon-root", type=Path, required=True)
    args = parser.parse_args()

    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    window = next((w for w in spec.get("windows", []) if w.get("field") == "ConsignmentBox"), None)
    if window is None:
        raise SystemExit("ConsignmentBox missing")

    modern = window.get("deterministicConsignmentComposites") or {}
    compat = window.get("consignmentHeaderCompatibility") or {}
    if modern.get("passed") is not True or modern.get("headerLabels") != 10 or modern.get("controlsAdded") != 135:
        raise SystemExit(f"Modern Consignment header ownership incomplete: {modern}")
    if compat.get("passed") is not True or compat.get("callSites") != 10 or compat.get("controlsAddedByCompatibilityPass") != 0:
        raise SystemExit(f"Consignment header compatibility contract incomplete: {compat}")
    if compat.get("duplicateHeadersInvented") is not False:
        raise SystemExit(f"Consignment compatibility pass introduced duplicate headers: {compat}")

    by = {str(control.get("name") or ""): control for control in window.get("controls", [])}
    for source_name, (parent, location, size) in HEADERS.items():
        name = f"ConsignmentHeaderSource{source_name}"
        label = by.get(name)
        if label is None or label.get("type") != "DXLabel":
            raise SystemExit(f"Consolidated Consignment helper header missing: {name}")
        p = props(label)
        expected = {
            "Parent": parent,
            "Location": location,
            "Size": size,
            "AutoSize": "false",
            "DrawFormat": "TextFormatFlags.HorizontalCenter | TextFormatFlags.VerticalCenter",
            "ForeColour": "Constants.PrimaryColour",
            "IsControl": "false",
        }
        for key, value in expected.items():
            if p.get(key) != value:
                raise SystemExit(f"Consignment header source property drifted: {name}.{key}={p.get(key)!r}, expected {value!r}")
        if "ConsignmentDialog.CreateHeaderLabel" not in str(label.get("sourceGenerated") or ""):
            raise SystemExit(f"Consignment header helper provenance missing: {name}")
        if label.get("runtimePayloadInvented") is not False:
            raise SystemExit(f"Consignment header unexpectedly carries runtime payload: {name}")
        if not str(label.get("resolvedText") or "").strip():
            raise SystemExit(f"Consignment header source text unresolved: {name}")

    legacy = [
        control.get("name") for control in window.get("controls", [])
        if str(control.get("sourceGenerated") or "").startswith("deterministic-consignment-headers:")
    ]
    if legacy:
        raise SystemExit(f"Legacy duplicate Consignment header controls remain: {legacy}")

    spec["consignmentHeaderHelperAudit"] = {
        "passed": True,
        "callSites": 10,
        "deterministicControls": 10,
        "modernOwner": "augment_consignment_deterministic_composites.py",
        "duplicateControls": 0,
        "runtimePayloadsInvented": False,
    }
    args.spec.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("Consignment header helper audit: PASS -> 10 modern-owned labels, no duplicates")


if __name__ == "__main__":
    main()
