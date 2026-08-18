#!/usr/bin/env python3
"""Expand deterministic Consignment custom composites omitted by the DX-only parser.

ConsignmentDialog always constructs:
- one ConsignmentItemTypeMenu with a source enum-driven button list,
- six ConsignmentSearchRow controls,
- six ConsignmentListRow controls.
The marketplace payloads remain null/empty; only constructor structure is emitted.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from augment_combo_options import parse_enum  # noqa: E402


PREFIX = "deterministic-consignment:"


def english(spec: dict, key: str, fallback: str = "") -> str:
    return str(((spec.get("language") or {}).get("English") or {}).get(key) or fallback)


def make(name: str, type_name: str, properties: dict[str, str], *, source: str,
         source_type: str | None = None, resolved_text: str | None = None) -> dict:
    item = {
        "name": name,
        "type": type_name,
        "properties": dict(properties),
        "sourceGenerated": source,
        "runtimePayloadInvented": False,
    }
    if source_type:
        item["sourceType"] = source_type
    if resolved_text is not None:
        item["resolvedText"] = resolved_text
    return item


def assert_source(root: Path) -> None:
    text = (root / "Client/Scenes/Views/ConsignmentDialog.cs").read_text(encoding="utf-8-sig")
    needles = (
        "public const int VisibleRowCount = 6;",
        "ItemTypeMenu = new ConsignmentItemTypeMenu",
        "Location = new Point(13, 50)",
        "Size = new Size(160, 268)",
        "SearchRows = new ConsignmentSearchRow[VisibleRowCount];",
        "Location = new Point(180, 58 + i * 42)",
        "ConsignRows = new ConsignmentListRow[VisibleRowCount];",
        "Location = new Point(14, 58 + i * 42)",
        "public sealed class ConsignmentItemTypeMenu : DXControl",
        "private const int RowHeight = 21;",
        "private const int VisibleRows = 12;",
        "Container = new DXControl",
        "Location = new Point(0, 5)",
        "Size = new Size(140, 260)",
        "ScrollBar = new DXVScrollBar",
        "Location = new Point(136, 0)",
        "Size = new Size(18, 272)",
        "VisibleSize = VisibleRows",
        "Add(CEnvir.Language.ConsignmentDialogAllLabel, null);",
        "foreach (ItemType itemType in Enum.GetValues(enumType))",
        "if (itemType == ItemType.Nothing) continue;",
        "Index = 831",
        "Size = new Size(136, 18)",
        "button.Index = selected ? 830 : 831;",
        "Buttons[i].Location = new Point(0, (i - ScrollBar.Value) * RowHeight);",
        "public sealed class ConsignmentSearchRow : DXControl",
        "Size = new Size(512, 42);",
        "Visible = false;",
        "Index = 810",
        "Location = new Point(11, 3)",
        "NameLabel = CreateLabel(new Point(52, 10), new Size(120, 20)",
        "LevelLabel = CreateLabel(new Point(176, 10), new Size(55, 20)",
        "PriceLabel = CreateLabel(new Point(235, 10), new Size(110, 20)",
        "SellerLabel = CreateLabel(new Point(345, 10), new Size(160, 20)",
        "public sealed class ConsignmentListRow : DXControl",
        "Size = new Size(680, 42);",
        "Index = 811",
        "Location = new Point(23, 3)",
        "NameLabel = CreateLabel(new Point(65, 10), new Size(180, 20)",
        "LevelLabel = CreateLabel(new Point(250, 10), new Size(54, 20)",
        "PriceLabel = CreateLabel(new Point(307, 10), new Size(145, 20)",
        "DateLabel = CreateLabel(new Point(460, 10), new Size(210, 20)",
    )
    for needle in needles:
        if needle not in text:
            raise SystemExit(f"Consignment composite source changed: missing {needle!r}")


def add_label(generated: list[dict], row: str, suffix: str, location: str, size: str,
              draw_format: str, source: str) -> None:
    generated.append(make(f"{row}{suffix}", "DXLabel", {
        "Parent": row,
        "Location": location,
        "Size": size,
        "AutoSize": "false",
        "DrawFormat": draw_format,
        "ForeColour": "Color.White",
        "IsControl": "false",
        "Text": '""',
    }, source=source, resolved_text=""))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--zircon-root", type=Path, required=True)
    args = parser.parse_args()

    assert_source(args.zircon_root)
    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    window = next((w for w in spec.get("windows", []) if w.get("field") == "ConsignmentBox"), None)
    if window is None:
        raise SystemExit("ConsignmentBox missing from manifest")

    controls = [
        control for control in window.get("controls", [])
        if not str(control.get("sourceGenerated") or "").startswith(PREFIX)
    ]
    generated: list[dict] = []

    members = parse_enum(args.zircon_root, "ItemType")
    if len(members) != 34 or members[0].get("name") != "Nothing" or members[-1].get("name") != "Reel":
        raise SystemExit(f"ItemType source enum contract changed: count={len(members)} first={members[:1]} last={members[-1:]}")
    selectable = [member for member in members if member.get("name") != "Nothing"]

    menu_source = PREFIX + "ConsignmentItemTypeMenu constructor/Add/Select"
    menu = "ConsignmentItemTypeMenuSource"
    generated.append(make(menu, "DXControl", {
        "Parent": "SearchTab",
        "Location": "new Point(13, 50)",
        "Size": "new Size(160, 268)",
        "SelectedItemType": "null",
    }, source=menu_source, source_type="ConsignmentItemTypeMenu"))
    generated.append(make("ConsignmentItemTypeContainerSource", "DXControl", {
        "Parent": menu,
        "Location": "new Point(0, 5)",
        "Size": "new Size(140, 260)",
        "PassThrough": "true",
    }, source=menu_source))
    generated.append(make("ConsignmentItemTypeScrollBarSource", "DXVScrollBar", {
        "Parent": menu,
        "Location": "new Point(136, 0)",
        "Size": "new Size(18, 272)",
        "VisibleSize": "12",
        "Change": "1",
        "MaxValue": "34",
        "BackColour": "Color.Empty",
        "Border": "false",
        "UpButton.Index": "61",
        "UpButton.LibraryFile": "LibraryFile.Interface",
        "DownButton.Index": "62",
        "DownButton.LibraryFile": "LibraryFile.Interface",
        "PositionBar.Index": "60",
        "PositionBar.LibraryFile": "LibraryFile.Interface",
        "ShowBackgroundSlider": "true",
    }, source=menu_source))

    all_label = english(spec, "ConsignmentDialogAllLabel", "All")
    option_rows = [
        {"label": all_label, "source": "CEnvir.Language.ConsignmentDialogAllLabel", "tag": "null"},
        *[
            {
                "label": str(member.get("label") or member["name"]),
                "source": f"ItemType.{member['name']}" + (" [Description]" if member.get("label") != member["name"] else ""),
                "tag": f"ItemType.{member['name']}",
            }
            for member in selectable
        ],
    ]
    if len(option_rows) != 34:
        raise SystemExit(f"Consignment ItemType menu option count internal error: {len(option_rows)}")
    for i, option in enumerate(option_rows):
        name = f"ConsignmentItemTypeButtonSource{i + 1:02d}"
        selected = i == 0
        control = make(name, "DXButton", {
            "Parent": "ConsignmentItemTypeContainerSource",
            "LibraryFile": "LibraryFile.GameInter",
            "Index": "830" if selected else "831",
            "Location": f"new Point(0, {i * 21})",
            "Size": "new Size(136, 18)",
            "Label.Text": json.dumps(option["label"], ensure_ascii=False),
            "Label.ForeColour": "Constants.ActiveTabColour" if selected else "Constants.InactiveTabColour",
            "Tag": option["tag"],
        }, source=menu_source, resolved_text=option["label"])
        control["sourceOption"] = option["source"]
        control["selectedInitially"] = selected
        generated.append(control)

    search_source = PREFIX + "ConsignmentDialog SearchRows + ConsignmentSearchRow constructor/CreateLabel"
    for i in range(6):
        row = f"ConsignmentSearchRowSource{i + 1:02d}"
        generated.append(make(row, "DXControl", {
            "Parent": "SearchTab",
            "Location": f"new Point(180, {58 + i * 42})",
            "Size": "new Size(512, 42)",
            "Visible": "false",
            "RuntimeMarketInfo": "ClientMarketPlaceInfo; null in neutral reference",
            "Loading": "false",
        }, source=search_source, source_type="ConsignmentSearchRow"))
        generated.append(make(f"{row}SelectedImage", "DXImageControl", {
            "Parent": row,
            "LibraryFile": "LibraryFile.GameInter",
            "Index": "810",
            "IsControl": "false",
            "Visible": "false",
        }, source=search_source))
        generated.append(make(f"{row}ItemCell", "DXItemCell", {
            "Parent": row,
            "Location": "new Point(11, 3)",
            "ReadOnly": "true",
            "Border": "false",
            "FixedBorder": "false",
            "FixedBorderColour": "true",
            "BorderColour": "Color.Empty",
            "ItemGrid": "new ClientUserItem[1]",
            "Slot": "0",
            "ShowCountLabel": "true",
            "RuntimeItem": "ClientMarketPlaceInfo.Item; absent",
        }, source=search_source))
        add_label(generated, row, "NameLabel", "new Point(52, 10)", "new Size(120, 20)",
                  "TextFormatFlags.VerticalCenter | TextFormatFlags.WordEllipsis", search_source)
        add_label(generated, row, "LevelLabel", "new Point(176, 10)", "new Size(55, 20)",
                  "TextFormatFlags.HorizontalCenter | TextFormatFlags.VerticalCenter", search_source)
        add_label(generated, row, "PriceLabel", "new Point(235, 10)", "new Size(110, 20)",
                  "TextFormatFlags.HorizontalCenter | TextFormatFlags.VerticalCenter", search_source)
        add_label(generated, row, "SellerLabel", "new Point(345, 10)", "new Size(160, 20)",
                  "TextFormatFlags.HorizontalCenter | TextFormatFlags.VerticalCenter | TextFormatFlags.WordEllipsis", search_source)

    consign_source = PREFIX + "ConsignmentDialog ConsignRows + ConsignmentListRow constructor/CreateLabel"
    for i in range(6):
        row = f"ConsignmentListRowSource{i + 1:02d}"
        generated.append(make(row, "DXControl", {
            "Parent": "ConsignTab",
            "Location": f"new Point(14, {58 + i * 42})",
            "Size": "new Size(680, 42)",
            "Visible": "false",
            "RuntimeMarketInfo": "ClientMarketPlaceInfo; null in neutral reference",
        }, source=consign_source, source_type="ConsignmentListRow"))
        generated.append(make(f"{row}SelectedImage", "DXImageControl", {
            "Parent": row,
            "LibraryFile": "LibraryFile.GameInter",
            "Index": "811",
            "IsControl": "false",
            "Visible": "false",
        }, source=consign_source))
        generated.append(make(f"{row}ItemCell", "DXItemCell", {
            "Parent": row,
            "Location": "new Point(23, 3)",
            "ReadOnly": "true",
            "Border": "true",
            "FixedBorder": "false",
            "FixedBorderColour": "true",
            "BorderColour": "Color.Empty",
            "ItemGrid": "new ClientUserItem[1]",
            "Slot": "0",
            "ShowCountLabel": "true",
            "RuntimeItem": "ClientMarketPlaceInfo.Item; absent",
        }, source=consign_source))
        add_label(generated, row, "NameLabel", "new Point(65, 10)", "new Size(180, 20)",
                  "TextFormatFlags.VerticalCenter | TextFormatFlags.WordEllipsis", consign_source)
        add_label(generated, row, "LevelLabel", "new Point(250, 10)", "new Size(54, 20)",
                  "TextFormatFlags.HorizontalCenter | TextFormatFlags.VerticalCenter", consign_source)
        add_label(generated, row, "PriceLabel", "new Point(307, 10)", "new Size(145, 20)",
                  "TextFormatFlags.HorizontalCenter | TextFormatFlags.VerticalCenter", consign_source)
        add_label(generated, row, "DateLabel", "new Point(460, 10)", "new Size(210, 20)",
                  "TextFormatFlags.HorizontalCenter | TextFormatFlags.VerticalCenter", consign_source)

    if len(generated) != 121:
        raise SystemExit(f"Consignment deterministic composite count internal error: {len(generated)} != 121")
    window["controls"] = generated + controls
    window["deterministicConsignmentComposites"] = {
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
    args.spec.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("Consignment composites expanded: 121 controls (34 ItemType buttons + 6 search + 6 consign rows)")


if __name__ == "__main__":
    main()
