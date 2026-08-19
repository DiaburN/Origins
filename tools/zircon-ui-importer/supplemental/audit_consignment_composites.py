#!/usr/bin/env python3
"""Compatibility audit for the current deterministic Consignment expansion.

This keeps the original Consignment gate name alive while validating the modern
single-owner pass: 10 helper headers, 38 ItemType buttons through SocketGem, and
six search + six consign row composites. The deeper geometry audit runs later as
audit_consignment_deterministic_composites.py.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ASSET_IDS = {810, 811, 830, 831}


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

    contract = window.get("deterministicConsignmentComposites") or {}
    expected = {
        "passed": True,
        "controlsAdded": 135,
        "headerLabels": 10,
        "itemTypeMenuControls": 41,
        "itemTypeButtons": 38,
        "searchRows": 6,
        "searchRowControls": 42,
        "consignRows": 6,
        "consignRowControls": 42,
        "neutralRowsVisible": False,
        "runtimeMarketInfoInvented": False,
        "runtimeItemsInvented": False,
        "runtimeSellersInvented": False,
        "runtimePricesInvented": False,
    }
    for key, value in expected.items():
        if contract.get(key) != value:
            raise SystemExit(f"Consignment compatibility contract drifted: {key}={contract.get(key)!r}, expected {value!r}")

    by = {str(control.get("name") or ""): control for control in window.get("controls", [])}
    headers = [control for name, control in by.items() if name.startswith("ConsignmentHeaderSource")]
    if len(headers) != 10 or any(not str(control.get("resolvedText") or "").strip() for control in headers):
        raise SystemExit("Consignment helper-created source headers incomplete")

    menu = by.get("ConsignmentItemTypeMenuSource")
    scroll = by.get("ConsignmentItemTypeMenuSourceScrollBar")
    if menu is None or menu.get("sourceType") != "ConsignmentItemTypeMenu":
        raise SystemExit("Consignment ItemTypeMenu source root missing")
    if props(scroll).get("VisibleSize") != "12" or props(scroll).get("Change") != "1" or props(scroll).get("MaxValue") != "38":
        raise SystemExit(f"Consignment ItemType scrollbar current contract drifted: {props(scroll)}")

    buttons = [control for name, control in by.items() if name.startswith("ConsignmentItemTypeButtonSource")]
    if len(buttons) != 38:
        raise SystemExit(f"Consignment current ItemType button count drifted: {len(buttons)}")
    all_button = by.get("ConsignmentItemTypeButtonSourceAll")
    socket = by.get("ConsignmentItemTypeButtonSourceSocketGem")
    if props(all_button).get("Index") != "830" or props(all_button).get("Tag") != "null":
        raise SystemExit(f"Consignment All initial selection drifted: {all_button}")
    if props(socket).get("Index") != "831" or props(socket).get("Tag") != "ItemType.SocketGem":
        raise SystemExit(f"Consignment current ItemType tail must be SocketGem: {socket}")
    if any(not str(control.get("resolvedText") or "").strip() for control in buttons):
        raise SystemExit("Consignment current ItemType labels incomplete")

    for family in ("Search", "List"):
        rows = [by.get(f"Consignment{family}RowSource{i + 1:02d}") for i in range(6)]
        if any(row is None or props(row).get("Visible") != "false" for row in rows):
            raise SystemExit(f"Consignment {family} neutral rows incomplete/visible")

    generated = [
        control for control in window.get("controls", [])
        if str(control.get("sourceGenerated") or "").startswith("deterministic-consignment:")
    ]
    if len(generated) != 135:
        raise SystemExit(f"Consignment deterministic current control count drifted: {len(generated)}")
    if any(control.get("runtimePayloadInvented") is not False for control in generated):
        raise SystemExit("Consignment current pass introduced runtime marketplace payloads")

    game_inter = {int(value) for value in spec.get("assetRefs", {}).get("GameInter", [])}
    missing = ASSET_IDS - game_inter
    if missing:
        raise SystemExit(f"Consignment current source artwork refs missing: {sorted(missing)}")

    spec["consignmentCompositeAudit"] = {
        "passed": True,
        "contractVersion": 2,
        "deterministicControls": 135,
        "headerLabels": 10,
        "itemTypeButtons": 38,
        "searchRows": 6,
        "consignRows": 6,
        "runtimeMarketInfoInvented": False,
        "runtimeItemsInvented": False,
        "sourceAssets": sorted(ASSET_IDS),
    }
    args.spec.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("Consignment compatibility audit: PASS v2 (135 controls / 38 ItemType buttons)")


if __name__ == "__main__":
    main()
