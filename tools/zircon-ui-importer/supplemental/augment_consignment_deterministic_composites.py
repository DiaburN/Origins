#!/usr/bin/env python3
"""Expand fixed Consignment UI omitted by the DX-only base parser.

Source-backed structures covered here:
- ten CreateHeaderLabel(...) controls invoked by ConsignmentDialog constructor,
- ConsignmentItemTypeMenu (root, container, scrollbar, All + ItemType buttons),
- six ConsignmentSearchRow composites,
- six ConsignmentListRow composites.
Marketplace payloads remain absent and all result rows remain hidden.
"""
from __future__ import annotations

import argparse
import json
import sys
from copy import deepcopy
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from augment_combo_options import parse_enum
from build_ui_source_spec import constructor_body, object_initializers, simple_assignments

PREFIX = "deterministic-consignment:"
VISIBLE_ROWS = 6

HEADER_SPECS = (
    ("SortLabel", "SearchTab", (10, 6), (50, 20), "ConsignmentDialogSortByLabel"),
    ("ItemTypesLabel", "SearchTab", (4, 32), (160, 20), "ConsignmentDialogItemTypesLabel"),
    ("SearchNameLabel", "SearchTab", (180, 32), (172, 20), "ConsignmentDialogNameLabel"),
    ("SearchLevelLabel", "SearchTab", (356, 32), (55, 20), "ConsignmentDialogLevelLabel"),
    ("SearchPriceLabel", "SearchTab", (415, 32), (110, 20), "ConsignmentDialogPriceLabel"),
    ("SellerLabel", "SearchTab", (525, 32), (160, 20), "ConsignmentDialogSellerLabel"),
    ("ConsignNameLabel", "ConsignTab", (14, 32), (250, 20), "ConsignmentDialogNameLabel"),
    ("ConsignLevelLabel", "ConsignTab", (260, 32), (60, 20), "ConsignmentDialogLevelLabel"),
    ("ConsignPriceLabel", "ConsignTab", (325, 32), (140, 20), "ConsignmentDialogPriceLabel"),
    ("ConsignDateLabel", "ConsignTab", (479, 32), (200, 20), "ConsignmentDialogConsignDateLabel"),
)

SEARCH_LABELS = (
    ("NameLabel", (52, 10), (120, 20), "TextFormatFlags.VerticalCenter | TextFormatFlags.WordEllipsis"),
    ("LevelLabel", (176, 10), (55, 20), "TextFormatFlags.HorizontalCenter | TextFormatFlags.VerticalCenter"),
    ("PriceLabel", (235, 10), (110, 20), "TextFormatFlags.HorizontalCenter | TextFormatFlags.VerticalCenter"),
    ("SellerLabel", (345, 10), (160, 20), "TextFormatFlags.HorizontalCenter | TextFormatFlags.VerticalCenter | TextFormatFlags.WordEllipsis"),
)

LIST_LABELS = (
    ("NameLabel", (65, 10), (180, 20), "TextFormatFlags.VerticalCenter | TextFormatFlags.WordEllipsis"),
    ("LevelLabel", (250, 10), (54, 20), "TextFormatFlags.HorizontalCenter | TextFormatFlags.VerticalCenter"),
    ("PriceLabel", (307, 10), (145, 20), "TextFormatFlags.HorizontalCenter | TextFormatFlags.VerticalCenter"),
    ("DateLabel", (460, 10), (210, 20), "TextFormatFlags.HorizontalCenter | TextFormatFlags.VerticalCenter"),
)


def english(spec: dict, key: str) -> str:
    value = ((spec.get("language") or {}).get("English") or {}).get(key)
    if value is None:
        raise SystemExit(f"Consignment source language key unresolved: {key}")
    return str(value)


def make(name: str, type_name: str, properties: dict[str, str], *, source_type: str | None = None,
         resolved_text: str | None = None, source: str = "constructor") -> dict:
    control = {
        "name": name,
        "type": type_name,
        "properties": dict(properties),
        "sourceGenerated": PREFIX + source,
        "runtimePayloadInvented": False,
    }
    if source_type:
        control["sourceType"] = source_type
    if resolved_text is not None:
        control["resolvedText"] = resolved_text
    return control


def source_contract(root: Path) -> tuple[str, list[dict], list[dict]]:
    path = root / "Client/Scenes/Views/ConsignmentDialog.cs"
    text = path.read_text(encoding="utf-8-sig")
    needles = (
        "public const int VisibleRowCount = 6;",
        "SearchRows = new ConsignmentSearchRow[VisibleRowCount];",
        "ConsignRows = new ConsignmentListRow[VisibleRowCount];",
        "Location = new Point(180, 58 + i * 42)",
        "Location = new Point(14, 58 + i * 42)",
        "ItemTypeMenu = new ConsignmentItemTypeMenu",
        "Location = new Point(13, 50)",
        "Size = new Size(160, 268)",
        "private const int RowHeight = 21;",
        "private const int VisibleRows = 12;",
        "Add(CEnvir.Language.ConsignmentDialogAllLabel, null);",
        "foreach (ItemType itemType in Enum.GetValues(enumType))",
        "if (itemType == ItemType.Nothing) continue;",
        "Index = 831",
        "Size = new Size(136, 18)",
        "button.Index = selected ? 830 : 831;",
        "Buttons[i].Location = new Point(0, (i - ScrollBar.Value) * RowHeight);",
        "public ConsignmentSearchRow()",
        "Size = new Size(512, 42);",
        "public ConsignmentListRow()",
        "Size = new Size(680, 42);",
    )
    for needle in needles:
        if needle not in text:
            raise SystemExit(f"Consignment deterministic source changed: missing {needle!r}")

    search_ctor = constructor_body(text, "ConsignmentSearchRow")
    list_ctor = constructor_body(text, "ConsignmentListRow")
    search_direct = object_initializers(search_ctor)
    list_direct = object_initializers(list_ctor)
    for class_name, controls in (("ConsignmentSearchRow", search_direct), ("ConsignmentListRow", list_direct)):
        names = {str(control.get("name") or "") for control in controls}
        if names != {"SelectedImage", "ItemCell"}:
            raise SystemExit(f"{class_name} direct constructor child set drifted: {sorted(names)}")
    return text, search_direct, list_direct


def add_row_family(generated: list[dict], templates: list[dict], *, family: str, parent: str,
                   x: int, width: int, labels: tuple, source_type: str) -> None:
    for i in range(VISIBLE_ROWS):
        row = f"Consignment{family}RowSource{i + 1:02d}"
        generated.append(make(row, "DXControl", {
            "Parent": parent,
            "Location": f"new Point({x}, {58 + i * 42})",
            "Size": f"new Size({width}, 42)",
            "Visible": "false",
            "RuntimeMarketInfo": "ClientMarketPlaceInfo; null in neutral reference",
        }, source_type=source_type, source=f"{source_type} fixed rows"))

        for template in templates:
            child = deepcopy(template)
            child_name = str(child.get("name") or "")
            child["name"] = f"{row}{child_name}"
            props = child.setdefault("properties", {})
            if props.get("Parent", "this") == "this":
                props["Parent"] = row
            child["sourceGenerated"] = PREFIX + f"{source_type} constructor"
            child["runtimePayloadInvented"] = False
            generated.append(child)

        for label_name, location, size, draw_format in labels:
            generated.append(make(f"{row}{label_name}", "DXLabel", {
                "Parent": row,
                "Location": f"new Point({location[0]}, {location[1]})",
                "Size": f"new Size({size[0]}, {size[1]})",
                "AutoSize": "false",
                "DrawFormat": draw_format,
                "ForeColour": "Color.White",
                "IsControl": "false",
                "Text": '""',
            }, resolved_text="", source=f"{source_type}.CreateLabel"))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--zircon-root", type=Path, required=True)
    args = parser.parse_args()

    _text, search_templates, list_templates = source_contract(args.zircon_root)
    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    window = next((w for w in spec.get("windows", []) if w.get("field") == "ConsignmentBox"), None)
    if window is None:
        raise SystemExit("ConsignmentBox missing")

    controls = [
        control for control in window.get("controls", [])
        if not str(control.get("sourceGenerated") or "").startswith(PREFIX)
    ]
    generated: list[dict] = []

    # Helper-created source header labels.
    for name, parent, location, size, key in HEADER_SPECS:
        text = english(spec, key)
        generated.append(make(f"ConsignmentHeaderSource{name}", "DXLabel", {
            "Parent": parent,
            "Location": f"new Point({location[0]}, {location[1]})",
            "Size": f"new Size({size[0]}, {size[1]})",
            "AutoSize": "false",
            "DrawFormat": "TextFormatFlags.HorizontalCenter | TextFormatFlags.VerticalCenter",
            "Text": f"CEnvir.Language.{key}",
            "ForeColour": "Constants.PrimaryColour",
            "IsControl": "false",
        }, resolved_text=text, source="ConsignmentDialog.CreateHeaderLabel"))

    # Custom item-type menu: deterministic enum-backed source UI, no marketplace data.
    menu = "ConsignmentItemTypeMenuSource"
    container = f"{menu}Container"
    scrollbar = f"{menu}ScrollBar"
    generated.append(make(menu, "DXControl", {
        "Parent": "SearchTab",
        "Location": "new Point(13, 50)",
        "Size": "new Size(160, 268)",
        "RuntimeMarketplaceData": "none; ItemType enum only",
    }, source_type="ConsignmentItemTypeMenu", source="ConsignmentItemTypeMenu constructor"))
    generated.append(make(container, "DXControl", {
        "Parent": menu,
        "Location": "new Point(0, 5)",
        "Size": "new Size(140, 260)",
        "PassThrough": "true",
    }, source="ConsignmentItemTypeMenu.Container"))

    enum_members = [member for member in parse_enum(args.zircon_root, "ItemType") if member["name"] != "Nothing"]
    if len(enum_members) != 37:
        raise SystemExit(f"ItemType enum count changed for Consignment menu: {len(enum_members)} != 37")
    button_rows = [("All", "null", english(spec, "ConsignmentDialogAllLabel"))] + [
        (member["name"], f"ItemType.{member['name']}", str(member["label"])) for member in enum_members
    ]
    if len(button_rows) != 38:
        raise SystemExit(f"Consignment menu button count changed: {len(button_rows)}")

    generated.append(make(scrollbar, "DXVScrollBar", {
        "Parent": menu,
        "Location": "new Point(136, 0)",
        "Size": "new Size(18, 272)",
        "VisibleSize": "12",
        "Change": "1",
        "MaxValue": str(len(button_rows)),
        "BackColour": "Color.Empty",
        "Border": "false",
        "UpButton": "{ Index = 61, LibraryFile = LibraryFile.Interface }",
        "DownButton": "{ Index = 62, LibraryFile = LibraryFile.Interface }",
        "PositionBar": "{ Index = 60, LibraryFile = LibraryFile.Interface }",
        "ShowBackgroundSlider": "true",
    }, source="ConsignmentItemTypeMenu.ScrollBar"))

    for index, (name, tag, label) in enumerate(button_rows):
        selected = index == 0
        generated.append(make(f"ConsignmentItemTypeButtonSource{name}", "DXButton", {
            "Parent": container,
            "LibraryFile": "LibraryFile.GameInter",
            "Index": "830" if selected else "831",
            "Size": "new Size(136, 18)",
            "Location": f"new Point(0, {index * 21})",
            "Label": f'{{ Text = {json.dumps(label, ensure_ascii=False)}, ForeColour = {"Constants.ActiveTabColour" if selected else "Constants.InactiveTabColour"} }}',
            "Tag": tag,
        }, resolved_text=label, source="ConsignmentItemTypeMenu.Add/Select"))

    add_row_family(generated, search_templates, family="Search", parent="SearchTab", x=180, width=512,
                   labels=SEARCH_LABELS, source_type="ConsignmentSearchRow")
    add_row_family(generated, list_templates, family="List", parent="ConsignTab", x=14, width=680,
                   labels=LIST_LABELS, source_type="ConsignmentListRow")

    expected = 10 + 41 + 42 + 42
    if expected != 135 or len(generated) != expected:
        raise SystemExit(f"Consignment deterministic expansion internal count error: {len(generated)} != 135")

    window["controls"] = generated + controls
    window["deterministicConsignmentComposites"] = {
        "passed": True,
        "controlsAdded": len(generated),
        "headerLabels": 10,
        "itemTypeMenuControls": 41,
        "itemTypeButtons": 38,
        "searchRows": VISIBLE_ROWS,
        "searchRowControls": 42,
        "consignRows": VISIBLE_ROWS,
        "consignRowControls": 42,
        "neutralRowsVisible": False,
        "runtimeMarketInfoInvented": False,
        "runtimeItemsInvented": False,
        "runtimeSellersInvented": False,
        "runtimePricesInvented": False,
    }
    args.spec.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("Consignment deterministic composites expanded: 135 controls; no marketplace payloads")


if __name__ == "__main__":
    main()
