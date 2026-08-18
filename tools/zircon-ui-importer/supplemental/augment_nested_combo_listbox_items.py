#!/usr/bin/env python3
"""Materialize deterministic DXListBoxItem rows declared in nested Zircon windows.

Nested/transient controls are namespaced during reconstruction. Historically the
DXListBoxItem rows owned by a nested DXComboBox were represented only as
comboOptions metadata, which omitted real constructor-created controls from the
nested source floor. This pass restores those source rows without inventing any
runtime data. They remain visually deferred because DXComboBox starts closed.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from build_ui_source_spec import constructor_body
from augment_combo_options import label_from_initializer, list_item_initializers

PARENT_RE = re.compile(r"\bParent\s*=\s*([A-Za-z_][A-Za-z0-9_]*)\.ListBox\b")
ITEM_RE = re.compile(r"\bItem\s*=\s*([^,\n}]+)")


def source_name(control: dict) -> str:
    return str(control.get("sourceName") or control.get("name") or "")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--zircon-root", type=Path, required=True)
    args = parser.parse_args()

    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    messages = (spec.get("language") or {}).get("English") or {}
    materialized: list[dict] = []

    for owner in spec.get("nestedWindows") or []:
        source_path = owner.get("sourcePath")
        class_name = owner.get("sourceClass") or owner.get("class")
        if not source_path or not class_name:
            continue
        path = args.zircon_root / str(source_path)
        if not path.exists():
            continue
        body = constructor_body(path.read_text(encoding="utf-8-sig"), str(class_name))
        if not body:
            continue

        controls = owner.get("controls") or []
        combos = {
            source_name(control): control
            for control in controls
            if control.get("type") == "DXComboBox" and source_name(control)
        }
        if not combos:
            continue

        # If the core parser gains native DXListBoxItem support later, never
        # duplicate it here. The audit below will still verify the same source rows.
        existing = {
            (str((control.get("properties") or {}).get("Parent") or ""), str(control.get("sourceLabel") or ""))
            for control in controls
            if control.get("type") == "DXListBoxItem"
        }
        ordinals: dict[str, int] = {}
        additions: list[dict] = []

        for initializer in list_item_initializers(body):
            parent_match = PARENT_RE.search(initializer)
            if not parent_match:
                continue
            combo_source = parent_match.group(1)
            combo = combos.get(combo_source)
            if combo is None:
                continue
            label = label_from_initializer(initializer, messages)
            if not label:
                continue
            label_text, label_source = label
            item_match = ITEM_RE.search(initializer)
            item_expression = " ".join(item_match.group(1).split()) if item_match else None
            parent_expression = f"{combo.get('name')}.ListBox"
            if (parent_expression, label_text) in existing:
                continue

            ordinal = ordinals.get(combo_source, 0) + 1
            ordinals[combo_source] = ordinal
            name = f"{class_name}__{combo_source}__ListItem{ordinal:02d}"
            row = {
                "name": name,
                "sourceName": "_",
                "sourceType": "DXListBoxItem",
                "type": "DXListBoxItem",
                "properties": {
                    "Parent": parent_expression,
                    "DrawTexture": "true",
                },
                "compositeChild": True,
                "compositeOwner": str(class_name),
                "deterministicNestedComboRow": True,
                "sourceDeferredByClosedCombo": True,
                "sourceLabel": label_text,
                "sourceLabelExpression": label_source,
                "sourceItemExpression": item_expression,
                "runtimePayloadInvented": False,
            }
            additions.append(row)
            existing.add((parent_expression, label_text))
            materialized.append({
                "window": owner.get("field"),
                "control": name,
                "combo": combo.get("name"),
                "comboSourceName": combo_source,
                "label": label_text,
                "itemExpression": item_expression,
            })

        controls.extend(additions)
        owner["controls"] = controls

        for inventory in (spec.get("nestedWindowInventory") or {}).get("windows") or []:
            if inventory.get("sourceClass") == class_name:
                inventory["controlCount"] = len(controls)
                break

    lfg = next((owner for owner in spec.get("nestedWindows") or [] if owner.get("sourceClass") == "GroupLFGInputWindow"), None)
    if lfg is None:
        raise SystemExit("GroupLFGInputWindow missing while materializing nested combo rows")
    lfg_rows = [
        control for control in lfg.get("controls") or []
        if control.get("type") == "DXListBoxItem" and control.get("deterministicNestedComboRow")
    ]
    labels = [str(control.get("sourceLabel") or "") for control in lfg_rows]
    if labels != ["PvE", "PvP"]:
        raise SystemExit(f"GroupLFG deterministic DXListBoxItem rows drifted: {labels}")
    if any(not str((control.get("properties") or {}).get("Parent") or "").endswith("TypeComboBox.ListBox") for control in lfg_rows):
        raise SystemExit(f"GroupLFG DXListBoxItem parent contract drifted: {lfg_rows}")

    report = {
        "passed": True,
        "sourceRowsMaterialized": len(materialized),
        "groupLFGSourceRows": len(lfg_rows),
        "groupLFGLabels": labels,
        "initialComboShowing": False,
        "rowsDeferredByClosedCombo": True,
        "runtimePayloadsInvented": False,
        "rows": materialized,
    }
    spec["nestedComboListBoxItemMaterialization"] = report
    args.spec.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Nested deterministic DXListBoxItem rows materialized: {len(materialized)}; GroupLFG={labels}")


if __name__ == "__main__":
    main()
