#!/usr/bin/env python3
"""Materialize MarketPlaceHistoryDialog's four deterministic CreateLabel controls.

Zircon constructs these labels unconditionally in the dialog constructor through
CreateLabel(y). Their displayed values are assigned only by Show/Apply runtime
market data, so the neutral reference keeps text empty while preserving exact
source geometry and styling.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


SOURCE_PATH = "Client/Scenes/Views/ConsignmentDialog.cs"
SOURCE_CLASS = "MarketPlaceHistoryDialog"
FIELDS = (
    ("ItemLabel", 0),
    ("SaleCountLabel", 28),
    ("LastPriceLabel", 52),
    ("AveragePriceLabel", 76),
)
SOURCE_EVIDENCE = (
    "ItemLabel = CreateLabel(0);",
    "SaleCountLabel = CreateLabel(28);",
    "LastPriceLabel = CreateLabel(52);",
    "AveragePriceLabel = CreateLabel(76);",
    "private DXLabel CreateLabel(int y)",
    "Location = new Point(ClientArea.X, ClientArea.Y + y)",
    "Size = new Size(ClientArea.Width, 20)",
    "AutoSize = false",
    "DrawFormat = TextFormatFlags.VerticalCenter",
    "ForeColour = Color.White",
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--zircon-root", type=Path, required=True)
    args = parser.parse_args()

    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    source_file = args.zircon_root / SOURCE_PATH
    source = source_file.read_text(encoding="utf-8-sig")
    missing_evidence = [needle for needle in SOURCE_EVIDENCE if needle not in source]
    if missing_evidence:
        raise SystemExit(
            "MarketPlaceHistoryDialog CreateLabel source contract changed:\n- "
            + "\n- ".join(missing_evidence)
        )

    owner = next(
        (
            window
            for window in spec.get("nestedWindows") or []
            if (window.get("sourceClass") or window.get("class")) == SOURCE_CLASS
        ),
        None,
    )
    if owner is None:
        raise SystemExit("MarketPlaceHistoryDialog missing from nestedWindows")
    if str(owner.get("sourcePath") or "") != SOURCE_PATH:
        raise SystemExit(
            f"MarketPlaceHistoryDialog source path drifted: {owner.get('sourcePath')!r}"
        )

    controls = owner.get("controls") or []
    by_name = {str(control.get("name") or ""): control for control in controls}
    existing = [name for name, _ in FIELDS if name in by_name]
    if existing and len(existing) != len(FIELDS):
        raise SystemExit(
            "MarketPlaceHistoryDialog partially reconstructed; refusing duplicate helper materialization: "
            + repr(existing)
        )

    added = 0
    if not existing:
        for name, y in FIELDS:
            location = (
                "new Point(ClientArea.X, ClientArea.Y)"
                if y == 0
                else f"new Point(ClientArea.X, ClientArea.Y + {y})"
            )
            controls.append(
                {
                    "name": name,
                    "sourceName": name,
                    "sourceType": "DXLabel",
                    "type": "DXLabel",
                    "properties": {
                        "Parent": "this",
                        "Location": location,
                        "Size": "new Size(ClientArea.Width, 20)",
                        "AutoSize": "false",
                        "DrawFormat": "TextFormatFlags.VerticalCenter",
                        "ForeColour": "Color.White",
                    },
                    "resolvedText": "",
                    "sourceGenerated": "MarketPlaceHistoryDialog.CreateLabel",
                    "sourceGeneratedReason": "constructor-reachable deterministic CreateLabel helper omitted by base nested parser",
                    "deterministicHelperControl": True,
                    "helper": "CreateLabel",
                    "runtimeTextBound": True,
                    "runtimePayloadInvented": False,
                }
            )
            added += 1
        owner["controls"] = controls

    by_name = {str(control.get("name") or ""): control for control in controls}
    failures: list[str] = []
    for name, y in FIELDS:
        control = by_name.get(name)
        if control is None:
            failures.append(f"missing {name}")
            continue
        expected_location = (
            "new Point(ClientArea.X, ClientArea.Y)"
            if y == 0
            else f"new Point(ClientArea.X, ClientArea.Y + {y})"
        )
        props = control.get("properties") or {}
        expected = {
            "Parent": "this",
            "Location": expected_location,
            "Size": "new Size(ClientArea.Width, 20)",
            "AutoSize": "false",
            "DrawFormat": "TextFormatFlags.VerticalCenter",
            "ForeColour": "Color.White",
        }
        for key, value in expected.items():
            if str(props.get(key) or "") != value:
                failures.append(f"{name}.{key}={props.get(key)!r} != {value!r}")
        if str(control.get("resolvedText") or ""):
            failures.append(f"{name} fabricated runtime text: {control.get('resolvedText')!r}")
        if control.get("runtimePayloadInvented") is not False:
            failures.append(f"{name} runtimePayloadInvented must be false")

    if failures:
        raise SystemExit(
            "MarketPlaceHistoryDialog helper materialization failed:\n- "
            + "\n- ".join(failures)
        )

    for inventory in (spec.get("nestedWindowInventory") or {}).get("windows") or []:
        if inventory.get("sourceClass") == SOURCE_CLASS:
            inventory["controlCount"] = len(controls)
            break

    report = {
        "passed": True,
        "sourceClass": SOURCE_CLASS,
        "sourcePath": SOURCE_PATH,
        "labels": [name for name, _ in FIELDS],
        "labelCount": len(FIELDS),
        "controlsAdded": added,
        "controlsRemoved": 0,
        "sourceHelper": "CreateLabel",
        "constructorReachable": True,
        "geometryPreservesClientAreaExpressions": True,
        "runtimeTextNeutral": True,
        "runtimePayloadsInvented": False,
        "sourceBackedOnly": True,
    }
    spec["marketPlaceHistoryLabelMaterialization"] = report
    args.spec.write_text(
        json.dumps(spec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(
        "MarketPlaceHistoryDialog labels: PASS "
        f"(4 deterministic DXLabel; added={added}; runtime text neutral)"
    )


if __name__ == "__main__":
    main()
