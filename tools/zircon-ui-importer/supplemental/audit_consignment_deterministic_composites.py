#!/usr/bin/env python3
"""Strict gate for source-created deterministic Consignment composites."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


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
            raise SystemExit(f"Consignment deterministic contract drifted: {key}={contract.get(key)!r}, expected {value!r}")

    by = {str(control.get("name") or ""): control for control in window.get("controls", [])}

    headers = [control for name, control in by.items() if name.startswith("ConsignmentHeaderSource")]
    if len(headers) != 10 or any(not str(control.get("resolvedText") or "").strip() for control in headers):
        raise SystemExit(f"Consignment helper-created header labels incomplete/unresolved: {len(headers)}")

    menu = by.get("ConsignmentItemTypeMenuSource")
    container = by.get("ConsignmentItemTypeMenuSourceContainer")
    scrollbar = by.get("ConsignmentItemTypeMenuSourceScrollBar")
    if menu is None or menu.get("sourceType") != "ConsignmentItemTypeMenu":
        raise SystemExit("ConsignmentItemTypeMenu root missing")
    if props(menu).get("Location") != "new Point(13, 50)" or props(menu).get("Size") != "new Size(160, 268)":
        raise SystemExit(f"Consignment item-type menu geometry drifted: {props(menu)}")
    if props(container).get("Location") != "new Point(0, 5)" or props(container).get("Size") != "new Size(140, 260)":
        raise SystemExit(f"Consignment item-type container geometry drifted: {props(container)}")
    if props(scrollbar).get("VisibleSize") != "12" or props(scrollbar).get("Change") != "1" or props(scrollbar).get("MaxValue") != "38":
        raise SystemExit(f"Consignment item-type scrollbar contract drifted: {props(scrollbar)}")

    buttons = [control for name, control in by.items() if name.startswith("ConsignmentItemTypeButtonSource")]
    if len(buttons) != 38:
        raise SystemExit(f"Consignment item-type button count drifted: {len(buttons)}")
    all_button = by.get("ConsignmentItemTypeButtonSourceAll")
    if props(all_button).get("Index") != "830" or props(all_button).get("Location") != "new Point(0, 0)":
        raise SystemExit(f"Consignment All source selection drifted: {all_button}")
    if not str(all_button.get("resolvedText") or "").strip():
        raise SystemExit("Consignment All source label unresolved")
    non_all = [control for control in buttons if control is not all_button]
    if any(props(control).get("Index") != "831" for control in non_all):
        raise SystemExit("Consignment non-selected item type source index drifted")
    locations = {props(control).get("Location") for control in buttons}
    expected_locations = {f"new Point(0, {i * 21})" for i in range(38)}
    if locations != expected_locations:
        raise SystemExit("Consignment item-type button RowHeight=21 layout drifted")

    for family, parent, x, width, last_label in (
        ("Search", "SearchTab", 180, 512, "SellerLabel"),
        ("List", "ConsignTab", 14, 680, "DateLabel"),
    ):
        for i in range(6):
            row_name = f"Consignment{family}RowSource{i + 1:02d}"
            row = by.get(row_name)
            if row is None:
                raise SystemExit(f"Consignment deterministic row missing: {row_name}")
            p = props(row)
            if p.get("Parent") != parent or p.get("Location") != f"new Point({x}, {58 + i * 42})" or p.get("Size") != f"new Size({width}, 42)":
                raise SystemExit(f"Consignment row geometry drifted: {row_name} -> {p}")
            if p.get("Visible") != "false" or "null in neutral reference" not in str(p.get("RuntimeMarketInfo") or ""):
                raise SystemExit(f"Consignment row runtime-neutral state drifted: {row_name}")
            selected = by.get(f"{row_name}SelectedImage")
            item = by.get(f"{row_name}ItemCell")
            if selected is None or item is None:
                raise SystemExit(f"Consignment row constructor controls incomplete: {row_name}")
            expected_index = "810" if family == "Search" else "811"
            if props(selected).get("Index") != expected_index or props(selected).get("LibraryFile") != "LibraryFile.GameInter":
                raise SystemExit(f"Consignment selected image source asset drifted: {row_name}")
            for suffix in ("NameLabel", "LevelLabel", "PriceLabel", last_label):
                label = by.get(f"{row_name}{suffix}")
                if label is None or label.get("resolvedText") not in ("", None):
                    raise SystemExit(f"Fabricated Consignment marketplace text leaked: {row_name}{suffix}")

    generated = [
        control for control in window.get("controls", [])
        if str(control.get("sourceGenerated") or "").startswith("deterministic-consignment:")
    ]
    if len(generated) != 135:
        raise SystemExit(f"Consignment generated deterministic control count drifted: {len(generated)}")
    if any(control.get("runtimePayloadInvented") is not False for control in generated):
        raise SystemExit("Consignment supplemental introduced runtime marketplace payloads")

    game_inter = {int(value) for value in spec.get("assetRefs", {}).get("GameInter", [])}
    missing = {810, 811, 830, 831} - game_inter
    if missing:
        raise SystemExit(f"Consignment source artwork refs not promoted: {sorted(missing)}")

    spec["consignmentDeterministicAudit"] = {
        "passed": True,
        "deterministicControls": 135,
        "headerLabels": 10,
        "itemTypeButtons": 38,
        "searchRows": 6,
        "consignRows": 6,
        "runtimeMarketInfoInvented": False,
    }
    args.spec.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("Consignment deterministic audit: PASS (135 controls; no marketplace payloads)")


if __name__ == "__main__":
    main()
