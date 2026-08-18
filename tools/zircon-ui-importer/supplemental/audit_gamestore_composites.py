#!/usr/bin/env python3
"""Strict gate for deterministic GameStore custom composite expansion."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


ASSET_IDS = {4830, 4835, 4840, 4845, 4855, 4872}


def props(control: dict | None) -> dict:
    return (control or {}).get("properties") or {}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--zircon-root", type=Path, required=True)
    args = parser.parse_args()

    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    store = next((w for w in spec.get("windows", []) if w.get("field") == "GameStoreBox"), None)
    if store is None:
        raise SystemExit("GameStoreBox missing")
    contract = store.get("deterministicGameStoreComposites") or {}
    expected = {
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
    }
    for key, value in expected.items():
        if contract.get(key) != value:
            raise SystemExit(f"GameStore composite contract drifted: {key}={contract.get(key)!r}, expected {value!r}")

    by = {str(control.get("name") or ""): control for control in store.get("controls", [])}
    item_list = by.get("GameStoreItemListSource")
    if item_list is None or item_list.get("sourceType") != "GameStoreItemListControl":
        raise SystemExit("GameStore item-list composite root missing")
    if props(item_list).get("Location") != "new Point(199, 67)" or props(item_list).get("Size") != "new Size(409, 432)":
        raise SystemExit(f"GameStore item-list geometry drifted: {props(item_list)}")

    for i in range(10):
        row_name = f"GameStoreItemSource{i + 1:02d}"
        row = by.get(row_name)
        if row is None or row.get("sourceType") != "GameStoreItem":
            raise SystemExit(f"GameStore item row missing: {row_name}")
        x = (i % 2) * 202
        y = (i // 2) * 80
        if props(row).get("Location") != f"new Point({x}, {y})" or props(row).get("Size") != "new Size(200, 78)":
            raise SystemExit(f"GameStore item row geometry drifted: {row_name} -> {props(row)}")
        if props(row).get("Visible") != "false":
            raise SystemExit(f"GameStore neutral StoreInfo row must remain hidden: {row_name}")
        quantity = by.get(f"{row_name}QuantityBox")
        options = (quantity or {}).get("comboOptions") or []
        if [option.get("label") for option in options] != [str(value) for value in range(1, 11)]:
            raise SystemExit(f"GameStore quantity options drifted: {row_name} -> {options}")
        if quantity.get("comboSelectedOptionIndex") != 0:
            raise SystemExit(f"GameStore quantity initial selection drifted: {row_name}")
        option_controls = [by.get(f"{row_name}QuantityOption{value:02d}") for value in range(1, 11)]
        if any(control is None for control in option_controls):
            raise SystemExit(f"GameStore quantity DXListBoxItem controls incomplete: {row_name}")
        for suffix in ("HoverImage", "ItemCell", "PriceLabel", "NameLabel", "BuyButton", "GiftButton", "FavouriteButton"):
            if by.get(f"{row_name}{suffix}") is None:
                raise SystemExit(f"GameStore row constructor child missing: {row_name}{suffix}")
        for suffix in ("PriceLabel", "NameLabel"):
            if by[f"{row_name}{suffix}"].get("resolvedText") not in ("", None):
                raise SystemExit(f"Fabricated GameStore row data leaked: {row_name}{suffix}")

    previous = by.get("GameStorePreviousButtonSource")
    page = by.get("GameStorePageLabelSource")
    nxt = by.get("GameStoreNextButtonSource")
    if props(previous).get("Enabled") != "false" or props(nxt).get("Enabled") != "false":
        raise SystemExit("GameStore neutral pager buttons must be disabled on empty results")
    if page.get("resolvedText") != "1 / 1":
        raise SystemExit(f"GameStore neutral pager text drifted: {page}")

    top = by.get("GameStoreTopItemsSource")
    if top is None or top.get("sourceType") != "GameStoreTopItemsControl":
        raise SystemExit("GameStore top-items composite root missing")
    if props(top).get("Location") != "new Point(614, 65)" or props(top).get("Size") != "new Size(174, 425)":
        raise SystemExit(f"GameStore top-items geometry drifted: {props(top)}")
    for i in range(5):
        row_name = f"GameStoreTopItemSource{i + 1:02d}"
        row = by.get(row_name)
        if row is None or row.get("sourceType") != "GameStoreTopItemControl":
            raise SystemExit(f"GameStore top row missing: {row_name}")
        expected_height = 73 if i == 4 else 78
        if props(row).get("Location") != f"new Point(0, {5 + i * 87})" or props(row).get("Size") != f"new Size(174, {expected_height})":
            raise SystemExit(f"GameStore top-row geometry drifted: {row_name}")
        rank = by.get(f"{row_name}RankLabel")
        name = by.get(f"{row_name}NameLabel")
        cell = by.get(f"{row_name}ItemCell")
        if rank is None or name is None or cell is None:
            raise SystemExit(f"GameStore top-row constructor children incomplete: {row_name}")
        if not str(rank.get("resolvedText") or "").strip():
            raise SystemExit(f"GameStore top rank source text unresolved: {row_name}")
        if name.get("resolvedText") not in ("", None):
            raise SystemExit(f"Fabricated GameStore top item name leaked: {row_name}")

    generated = [
        control for control in store.get("controls", [])
        if str(control.get("sourceGenerated") or "").startswith("deterministic-gamestore:")
    ]
    if len(generated) != 215:
        raise SystemExit(f"GameStore generated control count drifted: {len(generated)}")
    if any(control.get("runtimePayloadInvented") is not False for control in generated):
        raise SystemExit("GameStore supplemental introduced runtime payloads")

    game_inter = {int(value) for value in spec.get("assetRefs", {}).get("GameInter", [])}
    missing_assets = ASSET_IDS - game_inter
    if missing_assets:
        raise SystemExit(f"GameStore source artwork refs were not promoted: {sorted(missing_assets)}")

    spec["gameStoreCompositeAudit"] = {
        "passed": True,
        "deterministicControls": 215,
        "itemRows": 10,
        "topRows": 5,
        "sourceAssets": sorted(ASSET_IDS),
        "runtimeStoreInfoInvented": False,
        "runtimeItemsInvented": False,
    }
    args.spec.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("GameStore composite audit: PASS (215 deterministic controls, no StoreInfo/items)")


if __name__ == "__main__":
    main()
