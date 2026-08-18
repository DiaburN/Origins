#!/usr/bin/env python3
"""Annotate deterministic DXListBoxItem rows already reconstructed in nested Zircon windows.

The nested/composite parser already materializes direct constructor-created
DXListBoxItem controls. This pass must never duplicate them. It only attaches
source-backed label/item metadata and records that their initial visual state is
deferred because DXComboBox starts closed.
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
    annotated: list[dict] = []
    failures: list[str] = []

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

        source_rows: list[dict] = []
        for initializer in list_item_initializers(body):
            parent_match = PARENT_RE.search(initializer)
            if not parent_match or parent_match.group(1) not in combos:
                continue
            label = label_from_initializer(initializer, messages)
            if not label:
                continue
            item_match = ITEM_RE.search(initializer)
            source_rows.append({
                "comboSourceName": parent_match.group(1),
                "label": label[0],
                "labelExpression": label[1],
                "itemExpression": " ".join(item_match.group(1).split()) if item_match else None,
            })

        if not source_rows:
            continue

        existing_rows = [
            control for control in controls
            if control.get("type") == "DXListBoxItem"
            and not control.get("sourceGenerated")
            and not control.get("deterministicNestedComboRow")
            and any(
                str((control.get("properties") or {}).get("Parent") or "").endswith(f"{combo.get('name')}.ListBox")
                for combo in combos.values()
            )
        ]
        existing_rows.sort(key=lambda control: int(control.get("sourceInitializerOffset") or 0))

        if len(existing_rows) != len(source_rows):
            failures.append(
                f"{class_name}: direct source DXListBoxItem rows={len(source_rows)} but reconstructed existing rows={len(existing_rows)}"
            )
            continue

        for control, source_row in zip(existing_rows, source_rows):
            combo = combos[source_row["comboSourceName"]]
            expected_parent = f"{combo.get('name')}.ListBox"
            actual_parent = str((control.get("properties") or {}).get("Parent") or "")
            if actual_parent != expected_parent:
                failures.append(
                    f"{class_name}.{control.get('name')}: parent {actual_parent!r} != {expected_parent!r}"
                )
                continue
            control["deterministicNestedComboRow"] = True
            control["sourceDeferredByClosedCombo"] = True
            control["sourceLabel"] = source_row["label"]
            control["sourceLabelExpression"] = source_row["labelExpression"]
            control["sourceItemExpression"] = source_row["itemExpression"]
            control["runtimePayloadInvented"] = False
            annotated.append({
                "window": owner.get("field"),
                "control": control.get("name"),
                "combo": combo.get("name"),
                "comboSourceName": source_row["comboSourceName"],
                "label": source_row["label"],
                "itemExpression": source_row["itemExpression"],
            })

    lfg = next((owner for owner in spec.get("nestedWindows") or [] if owner.get("sourceClass") == "GroupLFGInputWindow"), None)
    if lfg is None:
        failures.append("GroupLFGInputWindow missing while annotating nested combo rows")
        lfg_rows = []
    else:
        lfg_rows = [
            control for control in lfg.get("controls") or []
            if control.get("type") == "DXListBoxItem" and control.get("deterministicNestedComboRow")
        ]
    labels = [str(control.get("sourceLabel") or "") for control in lfg_rows]
    if labels != ["PvE", "PvP"]:
        failures.append(f"GroupLFG existing DXListBoxItem rows drifted: {labels}")

    report = {
        "passed": not failures,
        "sourceRowsAnnotated": len(annotated),
        "controlsAdded": 0,
        "controlsRemoved": 0,
        "groupLFGSourceRows": len(lfg_rows),
        "groupLFGLabels": labels,
        "initialComboShowing": False,
        "rowsDeferredByClosedCombo": True,
        "runtimePayloadsInvented": False,
        "rows": annotated,
        "failures": failures,
    }
    spec["nestedComboListBoxItemMaterialization"] = report
    args.spec.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if failures:
        raise SystemExit("Nested DXListBoxItem annotation failed:\n- " + "\n- ".join(failures))
    print(f"Nested deterministic DXListBoxItem rows annotated: {len(annotated)}; controls added=0; GroupLFG={labels}")


if __name__ == "__main__":
    main()
