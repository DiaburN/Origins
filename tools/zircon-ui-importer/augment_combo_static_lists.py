#!/usr/bin/env python3
"""Promote DXComboBox options built from deterministic Globals List<string> data."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from augment_combo_options import class_body, list_item_initializers, matching_brace, merge_entries


def decode(raw: str) -> str:
    try: return json.loads('"' + raw + '"')
    except json.JSONDecodeError: return raw


def globals_string_lists(root: Path) -> dict[str, list[str]]:
    path = root / "LibraryCore" / "Globals.cs"
    if not path.exists(): return {}
    text = path.read_text(encoding="utf-8-sig")
    out: dict[str, list[str]] = {}
    pattern = re.compile(r"public\s+static\s+List<string>\s+([A-Za-z_][A-Za-z0-9_]*)\s*=\s*new\s+List<string>\s*\{")
    for match in pattern.finditer(text):
        opening = text.find("{", match.start())
        try: closing = matching_brace(text, opening)
        except ValueError: continue
        values = [decode(raw) for raw in re.findall(r'"((?:\\.|[^"\\])*)"', text[opening + 1:closing])]
        if values: out[match.group(1)] = values
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--zircon-root", type=Path, required=True)
    args = parser.parse_args()
    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    global_lists = globals_string_lists(args.zircon_root)
    added = 0; changed = 0

    loop_re = re.compile(r"foreach\s*\(\s*string\s+([A-Za-z_][A-Za-z0-9_]*)\s+in\s+Globals\.([A-Za-z_][A-Za-z0-9_]*)\s*\)\s*(?:\{|(?=new\s+DXListBoxItem))")
    for owner in [*(spec.get("windows") or []), *(spec.get("nestedWindows") or [])]:
        combos = {c.get("name"): c for c in owner.get("controls", []) if c.get("type") == "DXComboBox"}
        if not combos: continue
        path = args.zircon_root / str(owner.get("sourcePath") or "")
        class_name = owner.get("class") or owner.get("sourceClass")
        if not path.exists() or not class_name: continue
        body = class_body(path.read_text(encoding="utf-8-sig"), str(class_name))
        if not body: continue
        for loop in loop_re.finditer(body):
            variable, list_name = loop.groups(); values = global_lists.get(list_name)
            if not values: continue
            # Handle both braced foreach bodies and a single following initializer.
            if body.find("{", loop.start(), loop.end()+1) >= 0:
                opening = body.find("{", loop.start())
                try: chunk = body[opening + 1:matching_brace(body, opening)]
                except ValueError: continue
            else:
                next_item = body.find("new DXListBoxItem", loop.end())
                if next_item < 0: continue
                opening = body.find("{", next_item)
                try: chunk = body[next_item:matching_brace(body, opening)+1]
                except ValueError: continue
            for initializer in list_item_initializers(chunk):
                parent = re.search(r"\bParent\s*=\s*([A-Za-z_][A-Za-z0-9_]*)\.ListBox\b", initializer)
                if not parent or parent.group(1) not in combos: continue
                if not re.search(rf"\bLabel\s*=\s*\{{\s*Text\s*=\s*{re.escape(variable)}\b", initializer, re.S): continue
                if not re.search(rf"\bItem\s*=\s*{re.escape(variable)}\b", initializer): continue
                control = combos[parent.group(1)]
                options = list(control.get("comboOptions") or [])
                before = len(options)
                merge_entries(options, [{
                    "label": value,
                    "labelSource": f"Globals.{list_name}",
                    "valueExpression": json.dumps(value, ensure_ascii=False),
                    "sourceBuilder": f"Globals.{list_name}",
                } for value in values])
                if len(options) > before:
                    control["comboOptions"] = options; added += len(options)-before; changed += 1

    config = next((w for w in spec.get("windows", []) if w.get("field") == "ConfigBox"), None)
    language = next((c for c in (config or {}).get("controls", []) if c.get("name") == "LanguageComboBox"), None)
    if [o.get("label") for o in (language or {}).get("comboOptions", [])] != ["English", "Chinese"]:
        raise SystemExit(f"Config LanguageComboBox Globals.Languages extraction drifted: {(language or {}).get('comboOptions')}")

    pass_info = spec.setdefault("comboOptionPass", {})
    pass_info["staticGlobalListOptionCount"] = added
    pass_info["staticGlobalListCombosChanged"] = changed
    controls = [c for w in [*(spec.get('windows') or []),*(spec.get('nestedWindows') or [])] for c in w.get('controls',[]) if c.get('type')=='DXComboBox']
    pass_info["deterministicOptionCount"] = sum(len(c.get("comboOptions") or []) for c in controls)
    pass_info["combosWithDeterministicOptions"] = sum(bool(c.get("comboOptions")) for c in controls)
    pass_info["runtimeOptionsInvented"] = False
    args.spec.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"DXComboBox static Globals options added: {added} across {changed} controls")


if __name__ == "__main__": main()
