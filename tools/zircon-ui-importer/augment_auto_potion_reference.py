#!/usr/bin/env python3
"""Expand AutoPotionDialog's deterministic 8-row constructor loop.

Zircon materialises AutoPotionRow controls inside a for loop, so the flat source
initializer pass cannot see the 8 repeated row subtrees. This pass reconstructs
only constructor-deterministic chrome/state. Linked ItemInfo/player values remain
runtime-only and are never fabricated.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROW_COUNT = 8
ROW_HEIGHT = 46
ROW_STEP = 50


def make(name: str, type_name: str, properties: dict[str, str], *, parent: str | None = None, resolved_text: str | None = None) -> dict:
    props = dict(properties)
    if parent is not None:
        props["Parent"] = parent
    item = {
        "name": name,
        "type": type_name,
        "properties": props,
        "sourceGenerated": "AutoPotionDialog Rows loop + AutoPotionRow constructor",
    }
    if resolved_text is not None:
        item["resolvedText"] = resolved_text
    return item


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", type=Path, required=True)
    args = parser.parse_args()
    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    window = next((item for item in spec.get("windows", []) if item.get("field") == "AutoPotionBox"), None)
    if not window:
        raise SystemExit("AutoPotionBox missing from generated Zircon manifest")

    controls = window.get("controls", [])
    panel = next((item for item in controls if item.get("name") == "panel" and item.get("type") == "DXControl"), None)
    scroll = next((item for item in controls if item.get("name") == "ScrollBar" and item.get("type") == "DXVScrollBar"), None)
    if not panel or not scroll:
        raise SystemExit(f"AutoPotion source panel/scroll parser contract changed: panel={bool(panel)} scroll={bool(scroll)}")

    # Remove only our own prior expansion when the helper is re-run.
    controls = [item for item in controls if not str(item.get("name", "")).startswith("AutoPotionRow")]
    language = (spec.get("language") or {}).get("English") or {}
    health_text = str(language.get("CommonStatusHealth") or "Health") + ":"
    mana_text = str(language.get("CommonStatusMana") or "Mana") + ":"
    enabled_text = str(language.get("AutoPotionEnabledLabel") or "Enabled")

    generated: list[dict] = []
    for i in range(ROW_COUNT):
        row = f"AutoPotionRow{i + 1:02d}"
        generated.append(make(row, "DXControl", {
            "Location": f"new Point(1, {1 + ROW_STEP * i})",
            "Size": f"new Size(260, {ROW_HEIGHT})",
            "Border": "true",
            "BorderColour": "Constants.PrimaryColour",
            "RuntimeIndex": str(i),
        }, parent="panel"))

        generated.append(make(f"{row}UpButton", "DXButton", {
            "LibraryFile": "LibraryFile.Interface",
            "Index": "44",
            "Location": "new Point(5, 5)",
            "Enabled": "true" if i > 0 else "false",
        }, parent=row))
        generated.append(make(f"{row}DownButton", "DXButton", {
            "LibraryFile": "LibraryFile.Interface",
            "Index": "46",
            "Location": "new Point(5, 29)",
            "Enabled": "true" if i < ROW_COUNT - 1 else "false",
        }, parent=row))

        cell = f"{row}ItemCell"
        generated.append(make(cell, "DXItemCell", {
            "Location": "new Point(20, 5)",
            "AllowLink": "true",
            "FixedBorder": "true",
            "Border": "true",
            "GridType": "GridType.AutoPotion",
            "Slot": str(i),
            "RuntimeQuickInfo": "ClientAutoPotionLink.LinkInfoIndex -> Globals.ItemInfoList; null in neutral reference",
        }, parent=row))
        generated.append(make(f"{row}IndexLabel", "DXLabel", {
            "Location": "new Point(-2, -1)",
            "IsControl": "false",
            "Text": f'"{i + 1}"',
        }, parent=cell, resolved_text=str(i + 1)))

        hp = f"{row}HealthTargetBox"
        mp = f"{row}ManaTargetBox"
        for name, y in ((hp, 5), (mp, 25)):
            generated.append(make(name, "DXNumberBox", {
                "Location": f"new Point(105, {y})",
                "Size": "new Size(80, 20)",
                "MinValue": "0",
                "MaxValue": "50000",
                "Value": "0",
                "Change": "10",
                "ValueTextBox.Size": "new Size(40, 18)",
                "UpButton.Location": "new Point(63, 1)",
            }, parent=row))

        # Source locations depend on measured localized label width; keep the
        # source expression so the layout resolver can derive it from each number box.
        generated.append(make(f"{row}HealthLabel", "DXLabel", {
            "Location": f"new Point({hp}.Location.X - {row}HealthLabel.Size.Width, {hp}.Location.Y + ({hp}.Size.Height - {row}HealthLabel.Size.Height) / 2)",
            "IsControl": "false",
            "Text": "CEnvir.Language.CommonStatusHealth + \":\"",
        }, parent=row, resolved_text=health_text))
        generated.append(make(f"{row}ManaLabel", "DXLabel", {
            "Location": f"new Point({mp}.Location.X - {row}ManaLabel.Size.Width, {mp}.Location.Y + ({mp}.Size.Height - {row}ManaLabel.Size.Height) / 2)",
            "IsControl": "false",
            "Text": "CEnvir.Language.CommonStatusMana + \":\"",
        }, parent=row, resolved_text=mana_text))
        generated.append(make(f"{row}EnabledCheckBox", "DXCheckBox", {
            "Location": f"new Point(260 - {row}EnabledCheckBox.Size.Width - 5, 5)",
            "Checked": "false",
            "Label": "CEnvir.Language.AutoPotionEnabledLabel",
        }, parent=row, resolved_text=enabled_text))

    window["controls"] = generated + controls
    window["autoPotionSourceLoop"] = {
        "rowCount": ROW_COUNT,
        "rowSize": [260, ROW_HEIGHT],
        "rowStep": ROW_STEP,
        "scrollMaxValue": ROW_COUNT * ROW_STEP - 2,
        "slotRange": [0, ROW_COUNT - 1],
        "healthRange": [0, 50000],
        "manaRange": [0, 50000],
        "neutralHealth": 0,
        "neutralMana": 0,
        "neutralEnabled": False,
        "runtimeItemLinksInvented": False,
        "networkUpdate": "C.AutoPotionLinkChanged (never executed by reference viewer)",
    }

    if len(generated) != ROW_COUNT * 10:
        raise SystemExit(f"AutoPotion deterministic loop expansion drifted: {len(generated)} != {ROW_COUNT * 10}")
    if window["autoPotionSourceLoop"]["scrollMaxValue"] != 398:
        raise SystemExit("AutoPotion source scroll MaxValue drifted")

    args.spec.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("AutoPotion source loop expanded: 8 rows / 80 controls; item/player/server data neutral")


if __name__ == "__main__":
    main()
