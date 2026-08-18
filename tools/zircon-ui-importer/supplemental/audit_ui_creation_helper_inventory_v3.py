#!/usr/bin/env python3
"""Exact provenance refinement for the remaining constructor helper boundaries.

V2 intentionally classifies helpers from their own structural body. Three
current-Zircon cases need stricter caller/source provenance:
- GameStore AddCategoryNode receives StoreInfo collections built from Binding,
  so its StoreTreeNode rows are runtime store data and must stay absent.
- Communication RefreshBlockList iterates the live local block list, so its
  panels/names must stay absent.
- GameStore AddSortOption is deterministic, but its four DXListBoxItem controls
  are already emitted by the source parser under SortBox.ListBox; link those
  exact controls instead of duplicating them.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path


def require_source(source: str, needles: tuple[str, ...], label: str) -> None:
    missing = [needle for needle in needles if needle not in source]
    if missing:
        raise SystemExit(f"{label} source contract changed:\n- " + "\n- ".join(missing))


def find_row(rows: list[dict], source_class: str, helper: str) -> dict:
    matches = [row for row in rows if row.get("sourceClass") == source_class and row.get("helper") == helper]
    if len(matches) != 1:
        raise SystemExit(f"Expected one helper row for {source_class}.{helper}, found {len(matches)}")
    return matches[0]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--zircon-root", type=Path, required=True)
    args = parser.parse_args()

    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    inventory = spec.get("uiCreationHelperInventory") or {}
    if inventory.get("passed") is not True or inventory.get("version") != 2:
        raise SystemExit(f"UI helper v2 inventory missing/not green: {inventory.get('version')!r}")
    rows = inventory.get("rows") or []

    store_source = (args.zircon_root / "Client/Scenes/Views/GameStoreDialog.cs").read_text(encoding="utf-8-sig")
    require_source(
        store_source,
        (
            "List<StoreInfo> itemList = Globals.StoreInfoList.Binding.ToList();",
            "AddCategoryNode(",
            "List<StoreInfo>",
            "AddSortOption(StoreSort.Recent, CEnvir.Language.GameStoreDialogSortBoxRecent);",
            "AddSortOption(StoreSort.Name, CEnvir.Language.GameStoreDialogSortBoxName);",
            "AddSortOption(StoreSort.PriceHigh, CEnvir.Language.GameStoreDialogSortBoxPriceHigh);",
            "AddSortOption(StoreSort.PriceLow, CEnvir.Language.GameStoreDialogSortBoxPriceLow);",
            "Parent = SortBox.ListBox",
        ),
        "GameStoreDialog helper",
    )

    communication_source = (args.zircon_root / "Client/Scenes/Views/CommunicationDialog.cs").read_text(encoding="utf-8-sig")
    require_source(
        communication_source,
        (
            "foreach (long index in CEnvir.BlockList)",
            "ClientBlockInfo blockInfo = CEnvir.BlockInfoList[index];",
            "Text = blockInfo.Name,",
            "Tag = blockInfo",
        ),
        "CommunicationDialog.RefreshBlockList",
    )

    # Runtime-bound StoreInfo category nodes: caller provenance is live Binding.
    category = find_row(rows, "GameStoreDialog", "AddCategoryNode")
    if not category.get("constructorReachable") or "StoreTreeNode" not in (category.get("createdTypes") or []):
        raise SystemExit(f"GameStore AddCategoryNode structural contract drifted: {category}")
    category.update({
        "externalRuntimeData": True,
        "classification": "runtime-bound",
        "status": "runtime-bound",
        "materializedControlNames": [],
        "runtimeProvenance": "BuildFolderTree -> Globals.StoreInfoList.Binding -> List<StoreInfo>",
        "runtimePayloadInvented": False,
        "v3Refined": True,
    })

    # Runtime-bound blocked-player panels/names: never fabricate a neutral list.
    block = find_row(rows, "CommunicationDialog", "RefreshBlockList")
    if not block.get("constructorReachable") or not {"DXControl", "DXLabel"}.issubset(set(block.get("createdTypes") or [])):
        raise SystemExit(f"Communication RefreshBlockList structural contract drifted: {block}")
    block.update({
        "externalRuntimeData": True,
        "classification": "runtime-bound",
        "status": "runtime-bound",
        "materializedControlNames": [],
        "runtimeProvenance": "CEnvir.BlockList + CEnvir.BlockInfoList[index]",
        "runtimePayloadInvented": False,
        "v3Refined": True,
    })

    # Deterministic GameStore sort options are already real DXListBoxItem controls.
    listbox_audit = spec.get("listBoxItemSourceBoundaryAudit") or {}
    if listbox_audit.get("passed") is not True:
        raise SystemExit(f"DXListBoxItem source-boundary audit missing/not green: {listbox_audit}")
    store_window = next((window for window in spec.get("windows", []) if window.get("field") == "GameStoreBox"), None)
    if store_window is None:
        raise SystemExit("GameStoreBox missing")
    sort_items = [
        control for control in store_window.get("controls", [])
        if control.get("type") == "DXListBoxItem"
        and str((control.get("properties") or {}).get("Parent") or "") == "SortBox.ListBox"
    ]
    if len(sort_items) != 4:
        raise SystemExit(f"GameStore SortBox source item count drifted: {len(sort_items)} != 4")
    sort_names = [str(control.get("name") or "") for control in sort_items]
    if any(not name for name in sort_names) or len(set(sort_names)) != 4:
        raise SystemExit(f"GameStore SortBox source item names invalid: {sort_names}")
    sort_row = find_row(rows, "GameStoreDialog", "AddSortOption")
    if not sort_row.get("constructorReachable") or sort_row.get("classification") != "deterministic-source":
        raise SystemExit(f"GameStore AddSortOption deterministic contract drifted: {sort_row}")
    sort_row.update({
        "status": "materialized",
        "materializedControlNames": sorted(sort_names),
        "existingSourceControlsLinked": True,
        "duplicateControlsAdded": 0,
        "v3Refined": True,
    })

    # Companion's three enum-backed helpers must now resolve to the exact
    # source-generated controls from augment_companion_filter_rows.py.
    companion = next((window for window in spec.get("windows", []) if window.get("field") == "CompanionBox"), None)
    if companion is None:
        raise SystemExit("CompanionBox missing")
    companion_contract = companion.get("deterministicCompanionFilters") or {}
    if companion_contract.get("passed") is not True:
        raise SystemExit(f"Companion deterministic filter contract missing: {companion_contract}")
    if companion_contract.get("runtimeCheckedStateInvented") is not False or companion_contract.get("runtimePayloadsInvented") is not False:
        raise SystemExit(f"Companion deterministic filters leaked runtime state: {companion_contract}")
    for helper in ("DrawClassFilter", "DrawRarityFilter", "DrawItemTypeFilter"):
        row = find_row(rows, "CompanionDialog", helper)
        if not row.get("constructorReachable") or row.get("classification") != "deterministic-source" or row.get("status") != "materialized":
            raise SystemExit(f"Companion {helper} not source-materialized: {row}")
        if not row.get("materializedControlNames"):
            raise SystemExit(f"Companion {helper} has no linked controls: {row}")

    inventory["classificationCounts"] = dict(Counter(row.get("classification") for row in rows))
    inventory["statusCounts"] = dict(Counter(row.get("status") for row in rows))
    inventory["version"] = 3
    inventory["storeCategoryNodesRemainRuntimeBound"] = True
    inventory["communicationBlockRowsRemainRuntimeBound"] = True
    inventory["gameStoreSortItemsLinkedWithoutDuplication"] = True
    inventory["companionEnumFiltersMaterialized"] = True
    inventory["runtimePayloadsInvented"] = False
    inventory["sourceBackedOnly"] = True
    spec["uiCreationHelperInventory"] = inventory
    spec["uiCreationHelperInventoryV3Audit"] = {
        "passed": True,
        "runtimeHelpersRefined": ["GameStoreDialog.AddCategoryNode", "CommunicationDialog.RefreshBlockList"],
        "existingSortItemsLinked": 4,
        "sortItemsDuplicated": 0,
        "companionFilterControls": companion_contract.get("controlsAdded"),
        "runtimePayloadsInvented": False,
        "sourceBackedOnly": True,
    }
    args.spec.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(
        "UI creation helper inventory v3: PASS -> Store categories/runtime, block rows/runtime, "
        f"4 existing sort items linked, Companion filters={companion_contract.get('controlsAdded')} controls"
    )


if __name__ == "__main__":
    main()
