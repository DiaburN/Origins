#!/usr/bin/env python3
"""Strict gate for deterministic Consignment composite expansion."""
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
        "controlsAdded": 121,
        "itemTypeMenuControls": 37,
        "itemTypeButtons": 34,
        "searchRows": 6,
        "searchRowControls": 42,
        "consignRows": 6,
        "consignRowControls": 42,
        "rowsVisibleInitially": False,
        "runtimeMarketInfoInvented": False,
        "runtimeItemsInvented": False,
        "runtimeSellerInvented": False,
        "runtimePriceInvented": False,
    }
    for key, value in expected.items():
        if contract.get(key) != value:
            raise SystemExit(f"Consignment composite contract drifted: {key}={contract.get(key)!r}, expected {value!r}")

    by = {str(control.get("name") or ""): control for control in window.get("controls", [])}
    menu = by.get("ConsignmentItemTypeMenuSource")
    if menu is None or menu.get("sourceType") != "ConsignmentItemTypeMenu":
        raise SystemExit("Consignment ItemTypeMenu source composite missing")
    if props(menu).get("Location") != "new Point(13, 50)" or props(menu).get("Size") != "new Size(160, 268)":
        raise SystemExit(f"Consignment ItemTypeMenu geometry drifted: {props(menu)}")
    container = by.get("ConsignmentItemTypeContainerSource")
    scroll = by.get("ConsignmentItemTypeScrollBarSource")
    if props(container).get("Location") != "new Point(0, 5)" or props(container).get("Size") != "new Size(140, 260)":
        raise SystemExit(f"Consignment ItemType container drifted: {props(container)}")
    if props(scroll).get("Location") != "new Point(136, 0)" or props(scroll).get("Size") != "new Size(18, 272)":
        raise SystemExit(f"Consignment ItemType scrollbar geometry drifted: {props(scroll)}")
    if props(scroll).get("VisibleSize") != "12" or props(scroll).get("Change") != "1" or props(scroll).get("MaxValue") != "34":
        raise SystemExit(f"Consignment ItemType scrollbar source contract drifted: {props(scroll)}")
    if [props(scroll).get(key) for key in ("UpButton.Index", "DownButton.Index", "PositionBar.Index")] != ["61", "62", "60"]:
        raise SystemExit(f"Consignment ItemType scrollbar artwork drifted: {props(scroll)}")

    buttons = [by.get(f"ConsignmentItemTypeButtonSource{i + 1:02d}") for i in range(34)]
    if any(button is None for button in buttons):
        raise SystemExit("Consignment ItemType menu does not contain 34 deterministic buttons")
    if props(buttons[0]).get("Index") != "830" or props(buttons[0]).get("Tag") != "null" or buttons[0].get("selectedInitially") is not True:
        raise SystemExit(f"Consignment All item type initial selection drifted: {buttons[0]}")
    if not str(buttons[0].get("resolvedText") or "").strip():
        raise SystemExit("Consignment All item type source text unresolved")
    if any(props(button).get("Index") != "831" for button in buttons[1:]):
        raise SystemExit("Consignment non-selected ItemType buttons must start at GameInter 831")
    if any(button.get("selectedInitially") is not False for button in buttons[1:]):
        raise SystemExit("Consignment non-All ItemType button was incorrectly selected")
    if any(not str(button.get("resolvedText") or "").strip() for button in buttons):
        raise SystemExit("Consignment ItemType source labels are incomplete")
    if props(buttons[-1]).get("Tag") != "ItemType.Reel":
        raise SystemExit(f"Consignment ItemType menu must terminate at Reel: {props(buttons[-1])}")
    for i, button in enumerate(buttons):
        if props(button).get("Location") != f"new Point(0, {i * 21})":
            raise SystemExit(f"Consignment ItemType button row geometry drifted at {i}: {props(button)}")
        if props(button).get("Size") != "new Size(136, 18)":
            raise SystemExit(f"Consignment ItemType button size drifted at {i}: {props(button)}")

    search_label_contract = {
        "NameLabel": ("new Point(52, 10)", "new Size(120, 20)"),
        "LevelLabel": ("new Point(176, 10)", "new Size(55, 20)"),
        "PriceLabel": ("new Point(235, 10)", "new Size(110, 20)"),
        "SellerLabel": ("new Point(345, 10)", "new Size(160, 20)"),
    }
    for i in range(6):
        row_name = f"ConsignmentSearchRowSource{i + 1:02d}"
        row = by.get(row_name)
        if row is None or row.get("sourceType") != "ConsignmentSearchRow":
            raise SystemExit(f"Consignment search row missing: {row_name}")
        p = props(row)
        if p.get("Location") != f"new Point(180, {58 + i * 42})" or p.get("Size") != "new Size(512, 42)":
            raise SystemExit(f"Consignment search row geometry drifted: {row_name} -> {p}")
        if p.get("Visible") != "false" or p.get("Loading") != "false":
            raise SystemExit(f"Consignment neutral search row state drifted: {row_name} -> {p}")
        selected = by.get(f"{row_name}SelectedImage")
        cell = by.get(f"{row_name}ItemCell")
        if props(selected).get("Index") != "810" or props(selected).get("Visible") != "false":
            raise SystemExit(f"Consignment search selected-image state drifted: {row_name}")
        if props(cell).get("Location") != "new Point(11, 3)" or props(cell).get("Border") != "false":
            raise SystemExit(f"Consignment search item-cell geometry drifted: {row_name}")
        for suffix, (location, size) in search_label_contract.items():
            label = by.get(f"{row_name}{suffix}")
            if label is None or props(label).get("Location") != location or props(label).get("Size") != size:
                raise SystemExit(f"Consignment search label geometry drifted: {row_name}{suffix}")
            if label.get("resolvedText") not in ("", None):
                raise SystemExit(f"Fabricated Consignment search data leaked: {row_name}{suffix}")

    consign_label_contract = {
        "NameLabel": ("new Point(65, 10)", "new Size(180, 20)"),
        "LevelLabel": ("new Point(250, 10)", "new Size(54, 20)"),
        "PriceLabel": ("new Point(307, 10)", "new Size(145, 20)"),
        "DateLabel": ("new Point(460, 10)", "new Size(210, 20)"),
    }
    for i in range(6):
        row_name = f"ConsignmentListRowSource{i + 1:02d}"
        row = by.get(row_name)
        if row is None or row.get("sourceType") != "ConsignmentListRow":
            raise SystemExit(f"Consignment list row missing: {row_name}")
        p = props(row)
        if p.get("Location") != f"new Point(14, {58 + i * 42})" or p.get("Size") != "new Size(680, 42)":
            raise SystemExit(f"Consignment list row geometry drifted: {row_name} -> {p}")
        if p.get("Visible") != "false":
            raise SystemExit(f"Consignment neutral list row must remain hidden: {row_name}")
        selected = by.get(f"{row_name}SelectedImage")
        cell = by.get(f"{row_name}ItemCell")
        if props(selected).get("Index") != "811" or props(selected).get("Visible") != "false":
            raise SystemExit(f"Consignment list selected-image state drifted: {row_name}")
        if props(cell).get("Location") != "new Point(23, 3)" or props(cell).get("Border") != "true":
            raise SystemExit(f"Consignment list item-cell geometry drifted: {row_name}")
        for suffix, (location, size) in consign_label_contract.items():
            label = by.get(f"{row_name}{suffix}")
            if label is None or props(label).get("Location") != location or props(label).get("Size") != size:
                raise SystemExit(f"Consignment list label geometry drifted: {row_name}{suffix}")
            if label.get("resolvedText") not in ("", None):
                raise SystemExit(f"Fabricated Consignment listing data leaked: {row_name}{suffix}")

    generated = [
        control for control in window.get("controls", [])
        if str(control.get("sourceGenerated") or "").startswith("deterministic-consignment:")
    ]
    if len(generated) != 121:
        raise SystemExit(f"Consignment generated control count drifted: {len(generated)}")
    if any(control.get("runtimePayloadInvented") is not False for control in generated):
        raise SystemExit("Consignment supplemental introduced runtime payloads")

    game_inter = {int(value) for value in spec.get("assetRefs", {}).get("GameInter", [])}
    missing_assets = ASSET_IDS - game_inter
    if missing_assets:
        raise SystemExit(f"Consignment source artwork refs were not promoted: {sorted(missing_assets)}")

    spec["consignmentCompositeAudit"] = {
        "passed": True,
        "deterministicControls": 121,
        "itemTypeButtons": 34,
        "searchRows": 6,
        "consignRows": 6,
        "runtimeMarketInfoInvented": False,
        "runtimeItemsInvented": False,
        "sourceAssets": sorted(ASSET_IDS),
    }
    args.spec.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("Consignment composite audit: PASS (121 controls; no marketplace data)")


if __name__ == "__main__":
    main()
