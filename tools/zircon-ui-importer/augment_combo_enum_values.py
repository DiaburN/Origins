#!/usr/bin/env python3
"""Promote deterministic DXComboBox options built via Enum.GetValues(...)."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from augment_combo_options import (
    class_body,
    list_item_initializers,
    matching_brace,
    merge_entries,
    parse_enum,
    resolve_selected_index,
    selected_expression,
)


def enum_value_options(body: str, combo_names: set[str], zircon_root: Path) -> dict[str, list[dict]]:
    found: dict[str, list[dict]] = {name: [] for name in combo_names}
    loop_re = re.compile(
        r"foreach\s*\(\s*(?:object|var|[A-Za-z_][A-Za-z0-9_]*)\s+([A-Za-z_][A-Za-z0-9_]*)\s+in\s+Enum\.GetValues\(typeof\(([A-Za-z_][A-Za-z0-9_]*)\)\)\s*\)\s*\{"
    )
    for loop in loop_re.finditer(body):
        variable, enum_name = loop.groups()
        opening = body.find("{", loop.start())
        try: closing = matching_brace(body, opening)
        except ValueError: continue
        loop_body = body[opening + 1:closing]
        members = parse_enum(zircon_root, enum_name)
        if not members: continue
        for initializer in list_item_initializers(loop_body):
            parent = re.search(r"\bParent\s*=\s*([A-Za-z_][A-Za-z0-9_]*)\.ListBox\b", initializer)
            if not parent or parent.group(1) not in combo_names: continue
            if not re.search(rf"\bLabel\s*=\s*\{{\s*Text\s*=\s*{re.escape(variable)}\.ToString\(\)\s*\}}", initializer, re.S): continue
            if not re.search(rf"\bItem\s*=\s*{re.escape(variable)}\b", initializer): continue
            entries = [{
                "label": member["name"],
                "labelSource": f"{enum_name}.{member['name']}.ToString()",
                "valueExpression": f"{enum_name}.{member['name']}",
                "sourceBuilder": f"Enum.GetValues(typeof({enum_name}))",
            } for member in members]
            merge_entries(found[parent.group(1)], entries)
    return found


def all_combo_controls(spec: dict):
    for owner in [*(spec.get("windows") or []), *(spec.get("nestedWindows") or [])]:
        for control in owner.get("controls", []):
            if control.get("type") == "DXComboBox":
                yield owner, control


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--zircon-root", type=Path, required=True)
    args = parser.parse_args()
    spec = json.loads(args.spec.read_text(encoding="utf-8"))

    added = 0
    combos_changed = 0
    for owner in [*(spec.get("windows") or []), *(spec.get("nestedWindows") or [])]:
        combo_controls = {c.get("name"): c for c in owner.get("controls", []) if c.get("type") == "DXComboBox"}
        if not combo_controls: continue
        source_path = owner.get("sourcePath")
        class_name = owner.get("class") or owner.get("sourceClass")
        if not source_path or not class_name: continue
        path = args.zircon_root / source_path
        if not path.exists(): continue
        body = class_body(path.read_text(encoding="utf-8-sig"), str(class_name))
        if not body: continue
        found = enum_value_options(body, set(combo_controls), args.zircon_root)
        for name, entries in found.items():
            if not entries: continue
            control = combo_controls[name]
            options = list(control.get("comboOptions") or [])
            before = len(options)
            merge_entries(options, entries)
            if len(options) == before: continue
            control["comboOptions"] = options
            expression = selected_expression(body, name)
            if expression:
                control["comboSelectedExpression"] = expression
                selected = resolve_selected_index(body, expression, options)
                if selected is not None: control["comboSelectedOptionIndex"] = selected
            added += len(options) - before
            combos_changed += 1

    # Communication is a stable sentinel for Enum.GetValues source construction.
    communication = next((w for w in spec.get("windows", []) if w.get("field") == "CommunicationBox"), None)
    if not communication: raise SystemExit("CommunicationBox missing from GameScene source inventory")
    by_name = {c.get("name"): c for c in communication.get("controls", []) if c.get("type") == "DXComboBox"}
    members = parse_enum(args.zircon_root, "OnlineState")
    enum_labels = [member["name"] for member in members]
    online = by_name.get("FriendOnlineStateBox") or {}
    view = by_name.get("FriendViewStatusBox") or {}
    if [o.get("label") for o in online.get("comboOptions", [])] != enum_labels:
        raise SystemExit(f"Communication OnlineState combo drifted: {online.get('comboOptions')}")
    if [o.get("label") for o in view.get("comboOptions", [])] != ["All", *enum_labels]:
        raise SystemExit(f"Communication View Status combo drifted: {view.get('comboOptions')}")
    if view.get("comboSelectedOptionIndex") != 0:
        raise SystemExit(f"Communication View Status initial All selection drifted: {view}")

    controls = [control for _, control in all_combo_controls(spec)]
    pass_info = spec.setdefault("comboOptionPass", {})
    pass_info["enumGetValuesOptionCount"] = added
    pass_info["enumGetValuesCombosChanged"] = combos_changed
    pass_info["deterministicOptionCount"] = sum(len(c.get("comboOptions") or []) for c in controls)
    pass_info["combosWithDeterministicOptions"] = sum(bool(c.get("comboOptions")) for c in controls)
    pass_info["initialSelectionsResolved"] = sum("comboSelectedOptionIndex" in c for c in controls)
    pass_info["runtimeOptionsInvented"] = False
    pass_info["source"] = str(pass_info.get("source", "")) + "; Enum.GetValues loops resolved from LibraryCore/Enum.cs"

    args.spec.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"DXComboBox Enum.GetValues options added: {added} across {combos_changed} controls")


if __name__ == "__main__": main()
