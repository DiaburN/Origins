#!/usr/bin/env python3
"""Expand deterministic GameStore custom controls omitted by the DX-only parser.

GameStoreDialog constructs two custom DXControl composites directly:
- GameStoreItemListControl: 10 fixed hidden GameStoreItem rows + pager chrome.
- GameStoreTopItemsControl: 5 fixed ranked placeholder rows.
The rows exist before StoreInfo arrives. This pass materialises only source
structure/options/rank labels and keeps all StoreInfo/ClientUserItem data absent.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


PREFIX = "deterministic-gamestore:"
RANK_KEYS = (
    "GameStoreDialogFirstPlaceLabel",
    "GameStoreDialogSecondPlaceLabel",
    "GameStoreDialogThirdPlaceLabel",
    "GameStoreDialogFourthPlaceLabel",
    "GameStoreDialogFifthPlaceLabel",
)


def english(spec: dict, key: str, fallback: str = "") -> str:
    return str(((spec.get("language") or {}).get("English") or {}).get(key) or fallback)


def make(name: str, type_name: str, properties: dict[str, str], *, source_type: str | None = None,
         source: str, resolved_text: str | None = None) -> dict:
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
    path = root / "Client/Scenes/Views/GameStoreDialog.cs"
    text = path.read_text(encoding="utf-8-sig")
    needles = (
        "ItemList = new GameStoreItemListControl",
        "Location = new Point(199, 67)",
        "Size = new Size(409, 432)",
        "public const int ItemsPerPage = 10;",
        "Rows = new GameStoreItem[ItemsPerPage];",
        "Location = new Point((i % 2) * 202, (i / 2) * 80)",
        "PreviousButton = new DXButton",
        "Index = 4840",
        "Location = new Point(122, 410)",
        "PageLabel = new DXLabel",
        "Location = new Point(150, 406)",
        "Size = new Size(106, 20)",
        "NextButton = new DXButton",
        "Index = 4845",
        "Location = new Point(265, 410)",
        "public GameStoreItem()",
        "Size = new Size(200, 78);",
        "Visible = false;",
        "HoverImage = new DXImageControl",
        "Index = 4872",
        "ItemCell = new DXItemCell",
        "Location = new Point(19, 18)",
        "PriceLabel = new DXLabel",
        "Location = new Point(7, 59)",
        "NameLabel = new DXLabel",
        "Location = new Point(65, 8)",
        "QuantityBox = new DXComboBox",
        "Location = new Point(72, 30)",
        "Size = new Size(117, DXComboBox.DefaultNormalHeight)",
        "for (int i = 1; i <= 10; i++)",
        "BuyButton = CreateActionButton(4835, new Point(83, 51)",
        "GiftButton = CreateActionButton(4830, new Point(116, 51)",
        "FavouriteButton = CreateActionButton(4855, new Point(151, 51)",
        "TopItems = new GameStoreTopItemsControl",
        "Location = new Point(614, 65)",
        "Size = new Size(174, 425)",
        "Rows = new GameStoreTopItemControl[5];",
        "Location = new Point(0, 5 + i * 87)",
        "Size = new Size(174, i == Rows.Length - 1 ? 73 : 78)",
        "public GameStoreTopItemControl()",
        "RankLabel = new DXLabel",
        "Location = new Point(0, 1)",
        "ItemCell = new DXItemCell",
        "Location = new Point(19, 26)",
        "NameLabel = new DXLabel",
        "Location = new Point(65, 30)",
    )
    for needle in needles:
        if needle not in text:
            raise SystemExit(f"GameStore composite source changed: missing {needle!r}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--zircon-root", type=Path, required=True)
    args = parser.parse_args()

    assert_source(args.zircon_root)
    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    store = next((w for w in spec.get("windows", []) if w.get("field") == "GameStoreBox"), None)
    if store is None:
        raise SystemExit("GameStoreBox missing from manifest")

    controls = [
        control for control in store.get("controls", [])
        if not str(control.get("sourceGenerated") or "").startswith(PREFIX)
    ]
    existing = {str(control.get("name") or "") for control in controls}
    collision_names = {"GameStoreItemListSource", "GameStoreTopItemsSource"} & existing
    if collision_names:
        raise SystemExit(f"GameStore supplemental identity collision: {sorted(collision_names)}")

    generated: list[dict] = []

    list_source = PREFIX + "GameStoreItemListControl constructor"
    item_list = "GameStoreItemListSource"
    generated.append(make(item_list, "DXControl", {
        "Parent": "this",
        "Location": "new Point(199, 67)",
        "Size": "new Size(409, 432)",
        "RuntimeStoreInfo": "Globals.StoreInfoList.Binding; absent in neutral reference",
    }, source_type="GameStoreItemListControl", source=list_source))

    item_source = PREFIX + "GameStoreItemListControl fixed 10 rows + GameStoreItem constructor"
    for i in range(10):
        row = f"GameStoreItemSource{i + 1:02d}"
        x = (i % 2) * 202
        y = (i // 2) * 80
        generated.append(make(row, "DXControl", {
            "Parent": item_list,
            "Location": f"new Point({x}, {y})",
            "Size": "new Size(200, 78)",
            "Visible": "false",
            "RuntimeStoreInfo": "StoreInfo; null in neutral reference",
        }, source_type="GameStoreItem", source=item_source))
        generated.append(make(f"{row}HoverImage", "DXImageControl", {
            "Parent": row,
            "LibraryFile": "LibraryFile.GameInter",
            "Index": "4872",
            "IsControl": "false",
            "Visible": "false",
        }, source=item_source))
        generated.append(make(f"{row}ItemCell", "DXItemCell", {
            "Parent": row,
            "Location": "new Point(19, 18)",
            "Border": "false",
            "ReadOnly": "true",
            "ItemGrid": "new ClientUserItem[1]",
            "Slot": "0",
            "FixedBorder": "true",
            "FixedBorderColour": "true",
            "BorderColour": "Color.Empty",
            "ShowCountLabel": "false",
            "RuntimeItem": "StoreInfo.Item -> ClientUserItem; absent",
        }, source=item_source))
        generated.append(make(f"{row}PriceLabel", "DXLabel", {
            "Parent": row,
            "AutoSize": "false",
            "DrawFormat": "TextFormatFlags.HorizontalCenter",
            "ForeColour": "Color.FromArgb(255, 140, 0)",
            "Location": "new Point(7, 59)",
            "Size": "new Size(58, 16)",
            "IsControl": "false",
            "Text": '""',
        }, source=item_source, resolved_text=""))
        generated.append(make(f"{row}NameLabel", "DXLabel", {
            "Parent": row,
            "AutoSize": "false",
            "DrawFormat": "TextFormatFlags.HorizontalCenter | TextFormatFlags.WordEllipsis",
            "Location": "new Point(65, 8)",
            "Size": "new Size(128, 17)",
            "ForeColour": "Color.White",
            "IsControl": "false",
            "Text": '""',
        }, source=item_source, resolved_text=""))
        quantity = f"{row}QuantityBox"
        quantity_control = make(quantity, "DXComboBox", {
            "Parent": row,
            "Location": "new Point(72, 30)",
            "Size": "new Size(117, DXComboBox.DefaultNormalHeight)",
            "DropDownHeight": "120",
            "Border": "false",
        }, source=item_source)
        quantity_control["comboOptions"] = [
            {
                "label": str(value),
                "labelSource": "GameStoreItem constructor integer loop",
                "valueExpression": str(value),
                "sourceBuilder": "for (int i = 1; i <= 10; i++)",
            }
            for value in range(1, 11)
        ]
        quantity_control["comboSelectedExpression"] = "1"
        quantity_control["comboSelectedOptionIndex"] = 0
        generated.append(quantity_control)
        for value in range(1, 11):
            generated.append(make(f"{row}QuantityOption{value:02d}", "DXListBoxItem", {
                "Parent": f"{quantity}.ListBox",
                "Label.Text": f'"{value}"',
                "Item": str(value),
            }, source=item_source, resolved_text=str(value)))
        for suffix, index, x, hint_key in (
            ("BuyButton", 4835, 83, "GameStoreDialogPurchaseHint"),
            ("GiftButton", 4830, 116, "GameStoreDialogGiftHint"),
            ("FavouriteButton", 4855, 151, "GameStoreDialogFavouriteHint"),
        ):
            generated.append(make(f"{row}{suffix}", "DXButton", {
                "Parent": row,
                "LibraryFile": "LibraryFile.GameInter",
                "Index": str(index),
                "Location": f"new Point({x}, 51)",
                "Hint": f"CEnvir.Language.{hint_key}",
                "HintPosition": "HintPosition.TopLeft",
            }, source=item_source))

    # The neutral data boundary produces one empty page if RefreshItems/Search is
    # evaluated without StoreInfo. No product row is made visible.
    generated.append(make("GameStorePreviousButtonSource", "DXButton", {
        "Parent": item_list,
        "LibraryFile": "LibraryFile.GameInter",
        "Index": "4840",
        "Location": "new Point(122, 410)",
        "Enabled": "false",
        "NeutralStateReason": "PageCount=Math.Max(1, empty results); _Page=0",
    }, source=list_source))
    generated.append(make("GameStorePageLabelSource", "DXLabel", {
        "Parent": item_list,
        "AutoSize": "false",
        "DrawFormat": "TextFormatFlags.HorizontalCenter | TextFormatFlags.VerticalCenter",
        "Location": "new Point(150, 406)",
        "Size": "new Size(106, 20)",
        "Text": '"1 / 1"',
    }, source=list_source, resolved_text="1 / 1"))
    generated.append(make("GameStoreNextButtonSource", "DXButton", {
        "Parent": item_list,
        "LibraryFile": "LibraryFile.GameInter",
        "Index": "4845",
        "Location": "new Point(265, 410)",
        "Enabled": "false",
        "NeutralStateReason": "PageCount=Math.Max(1, empty results); _Page=0",
    }, source=list_source))

    top_source = PREFIX + "GameStoreTopItemsControl fixed 5 rows + GameStoreTopItemControl constructor"
    top = "GameStoreTopItemsSource"
    generated.append(make(top, "DXControl", {
        "Parent": "this",
        "Location": "new Point(614, 65)",
        "Size": "new Size(174, 425)",
        "RuntimeStoreInfo": "SetItems indexes -> StoreInfo; absent in neutral reference",
    }, source_type="GameStoreTopItemsControl", source=top_source))
    for i, language_key in enumerate(RANK_KEYS):
        row = f"GameStoreTopItemSource{i + 1:02d}"
        height = 73 if i == 4 else 78
        generated.append(make(row, "DXControl", {
            "Parent": top,
            "Location": f"new Point(0, {5 + i * 87})",
            "Size": f"new Size(174, {height})",
            "RuntimeStoreInfo": "StoreInfo; null until SetItems",
        }, source_type="GameStoreTopItemControl", source=top_source))
        generated.append(make(f"{row}RankLabel", "DXLabel", {
            "Parent": row,
            "Location": "new Point(0, 1)",
            "Size": "new Size(174, 20)",
            "AutoSize": "false",
            "DrawFormat": "TextFormatFlags.HorizontalCenter | TextFormatFlags.VerticalCenter",
            "LabelStyle": "DXLabelStyle.GameStoreTopRank",
            "IsControl": "false",
            "Text": f"CEnvir.Language.{language_key}",
        }, source=top_source, resolved_text=english(spec, language_key)))
        generated.append(make(f"{row}ItemCell", "DXItemCell", {
            "Parent": row,
            "Location": "new Point(19, 26)",
            "FixedBorder": "true",
            "BorderColour": "Color.Empty",
            "Border": "false",
            "ReadOnly": "true",
            "ItemGrid": "new ClientUserItem[1]",
            "Slot": "0",
            "FixedBorderColour": "true",
            "ShowCountLabel": "false",
            "RuntimeItem": "StoreInfo.Item -> ClientUserItem; absent",
        }, source=top_source))
        generated.append(make(f"{row}NameLabel", "DXLabel", {
            "Parent": row,
            "AutoSize": "false",
            "DrawFormat": "TextFormatFlags.VerticalCenter | TextFormatFlags.WordEllipsis",
            "Location": "new Point(65, 30)",
            "Size": "new Size(100, 20)",
            "ForeColour": "Color.White",
            "IsControl": "false",
            "Text": '""',
        }, source=top_source, resolved_text=""))

    if len(generated) != 215:
        raise SystemExit(f"GameStore deterministic composite count internal error: {len(generated)} != 215")
    unresolved_ranks = [
        control["name"] for control in generated
        if control["name"].endswith("RankLabel") and not str(control.get("resolvedText") or "").strip()
    ]
    if unresolved_ranks:
        raise SystemExit(f"GameStore source rank labels unresolved: {unresolved_ranks}")

    store["controls"] = generated + controls
    store["deterministicGameStoreComposites"] = {
        "passed": True,
        "controlsAdded": 215,
        "itemListControls": 194,
        "itemRows": 10,
        "itemRowsVisible": False,
        "quantityOptionsPerRow": 10,
        "topItemsControls": 21,
        "topRows": 5,
        "runtimeStoreInfoInvented": False,
        "runtimeItemsInvented": False,
        "runtimePricesInvented": False,
        "runtimeFavouritesInvented": False,
        "source": "GameStoreItemListControl/GameStoreItem/GameStoreTopItemsControl/GameStoreTopItemControl constructors",
    }
    args.spec.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("GameStore deterministic composites expanded: 215 controls (10 item rows + 5 top rows)")


if __name__ == "__main__":
    main()
