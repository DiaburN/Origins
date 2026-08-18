#!/usr/bin/env python3
"""Extract deterministic DXComboBox list options from Zircon source.

Promotes only source-backed options whose visible labels can be resolved without
runtime data. Supported patterns:
- direct DXListBoxItem initializers,
- simple helper builders such as GameStoreDialog.AddSortOption(...),
- deterministic enum-range loops using enum names / [Description] labels.
Runtime/database-built rows remain intentionally absent.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def matching_brace(text: str, opening: int) -> int:
    depth = 0
    in_string = in_char = escaped = line_comment = block_comment = False
    i = opening
    while i < len(text):
        c = text[i]
        n = text[i + 1] if i + 1 < len(text) else ""
        if line_comment:
            if c == "\n": line_comment = False
            i += 1; continue
        if block_comment:
            if c == "*" and n == "/": block_comment = False; i += 2; continue
            i += 1; continue
        if in_char:
            if escaped: escaped = False
            elif c == "\\": escaped = True
            elif c == "'": in_char = False
            i += 1; continue
        if in_string:
            if escaped: escaped = False
            elif c == "\\": escaped = True
            elif c == '"': in_string = False
            i += 1; continue
        if c == "/" and n == "/": line_comment = True; i += 2; continue
        if c == "/" and n == "*": block_comment = True; i += 2; continue
        if c == '"': in_string = True; i += 1; continue
        if c == "'": in_char = True; i += 1; continue
        if c == "{": depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0: return i
        i += 1
    raise ValueError("unbalanced braces")


def class_body(text: str, class_name: str) -> str:
    match = re.search(rf"\bclass\s+{re.escape(class_name)}\b[^{{]*\{{", text)
    if not match: return ""
    opening = text.find("{", match.start())
    return text[opening + 1:matching_brace(text, opening)]


def decode_csharp(raw: str) -> str:
    try: return json.loads('"' + raw + '"')
    except json.JSONDecodeError: return raw.replace(r'\"','"').replace(r'\\','\\')


def list_item_initializers(body: str):
    for match in re.finditer(r"\bnew\s+DXListBoxItem\b", body):
        opening = body.find("{", match.end())
        if opening < 0: continue
        try: closing = matching_brace(body, opening)
        except ValueError: continue
        yield body[opening + 1:closing]


def literal_label(raw: str) -> tuple[str, str] | None:
    match = re.fullmatch(r'\$?"((?:\\.|[^"\\])*)"', raw.strip())
    if not match: return None
    value = decode_csharp(match.group(1))
    if "{" in value or "}" in value: return None
    return value, "literal"


def label_from_expression(expression: str, messages: dict[str, str]) -> tuple[str, str] | None:
    literal = literal_label(expression)
    if literal: return literal
    language = re.fullmatch(r"CEnvir\.Language\.([A-Za-z_][A-Za-z0-9_]*)", expression.strip())
    if language and language.group(1) in messages:
        return messages[language.group(1)], f"CEnvir.Language.{language.group(1)}"
    return None


def label_from_initializer(initializer: str, messages: dict[str, str]) -> tuple[str, str] | None:
    literal = re.search(r'\bLabel\s*=\s*\{\s*Text\s*=\s*(\$?"(?:\\.|[^"\\])*")', initializer, re.S)
    if literal:
        result = literal_label(literal.group(1))
        if result: return result
    language = re.search(r"\bLabel\s*=\s*\{\s*Text\s*=\s*CEnvir\.Language\.([A-Za-z_][A-Za-z0-9_]*)", initializer, re.S)
    if language and language.group(1) in messages:
        return messages[language.group(1)], f"CEnvir.Language.{language.group(1)}"
    return None


def split_args(raw: str) -> list[str]:
    out: list[str] = []
    start = 0; depth = 0; in_string = False; escaped = False
    for i, c in enumerate(raw):
        if in_string:
            if escaped: escaped = False
            elif c == "\\": escaped = True
            elif c == '"': in_string = False
            continue
        if c == '"': in_string = True; continue
        if c in "([{": depth += 1
        elif c in ")]}": depth = max(0, depth - 1)
        elif c == ',' and depth == 0:
            out.append(raw[start:i].strip()); start = i + 1
    out.append(raw[start:].strip())
    return out


def merge_entries(target: list[dict], incoming: list[dict]) -> None:
    for entry in incoming:
        if not any(existing["label"] == entry["label"] and existing.get("valueExpression") == entry.get("valueExpression") for existing in target):
            target.append(entry)


def helper_options(body: str, combo_names: set[str], messages: dict[str, str]) -> dict[str, list[dict]]:
    found: dict[str, list[dict]] = {name: [] for name in combo_names}
    method_re = re.compile(r"\b(?:public|private|protected|internal)\s+(?:static\s+)?(?:void|[A-Za-z_][A-Za-z0-9_<>,.? ]*)\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(([^)]*)\)\s*\{")
    for method in method_re.finditer(body):
        opening = body.find("{", method.start())
        try: closing = matching_brace(body, opening)
        except ValueError: continue
        method_body = body[opening + 1:closing]
        params = []
        for raw_param in split_args(method.group(2)):
            name_match = re.search(r"([A-Za-z_][A-Za-z0-9_]*)\s*$", raw_param)
            params.append(name_match.group(1) if name_match else "")
        for initializer in list_item_initializers(method_body):
            parent = re.search(r"\bParent\s*=\s*([A-Za-z_][A-Za-z0-9_]*)\.ListBox\b", initializer)
            if not parent or parent.group(1) not in combo_names: continue
            label_param = re.search(r"\bLabel\s*=\s*\{\s*Text\s*=\s*([A-Za-z_][A-Za-z0-9_]*)\b", initializer, re.S)
            item_param = re.search(r"\bItem\s*=\s*([A-Za-z_][A-Za-z0-9_]*)\b", initializer)
            if not label_param or label_param.group(1) not in params: continue
            for call in re.finditer(rf"\b{re.escape(method.group(1))}\s*\((.*?)\)\s*;", body, re.S):
                args = split_args(call.group(1))
                if len(args) != len(params): continue
                values = dict(zip(params, args))
                label = label_from_expression(values.get(label_param.group(1), ""), messages)
                if not label: continue
                value_expression = values.get(item_param.group(1)) if item_param and item_param.group(1) in values else None
                merge_entries(found[parent.group(1)], [{
                    "label": label[0],
                    "labelSource": label[1],
                    "valueExpression": " ".join(value_expression.split()) if value_expression else None,
                    "sourceBuilder": method.group(1),
                }])
    return found


def parse_enum(root: Path, enum_name: str) -> list[dict]:
    enum_path = root / "LibraryCore" / "Enum.cs"
    if not enum_path.exists(): return []
    text = enum_path.read_text(encoding="utf-8-sig")
    match = re.search(rf"\b(?:public\s+)?enum\s+{re.escape(enum_name)}\b[^{{]*\{{", text)
    if not match: return []
    opening = text.find("{", match.start())
    body = text[opening + 1:matching_brace(text, opening)]
    out: list[dict] = []
    description: str | None = None
    current_value = -1
    for raw_line in body.splitlines():
        line = raw_line.split("//", 1)[0].strip()
        if not line: continue
        desc = re.fullmatch(r'\[Description\("((?:\\.|[^"\\])*)"\)\]', line)
        if desc:
            description = decode_csharp(desc.group(1)); continue
        member = re.fullmatch(r"([A-Za-z_][A-Za-z0-9_]*)\s*(?:=\s*(-?\d+))?\s*,?", line)
        if not member: continue
        current_value = int(member.group(2)) if member.group(2) is not None else current_value + 1
        out.append({"name": member.group(1), "value": current_value, "label": description or member.group(1)})
        description = None
    return out


def enum_range_options(body: str, combo_names: set[str], zircon_root: Path) -> dict[str, list[dict]]:
    found: dict[str, list[dict]] = {name: [] for name in combo_names}
    loop_re = re.compile(
        r"for\s*\(\s*([A-Za-z_][A-Za-z0-9_]*)\s+([A-Za-z_][A-Za-z0-9_]*)\s*=\s*\1\.([A-Za-z_][A-Za-z0-9_]*)\s*;\s*\2\s*<=\s*\1\.([A-Za-z_][A-Za-z0-9_]*)\s*;\s*\2\+\+\s*\)\s*\{"
    )
    for loop in loop_re.finditer(body):
        enum_name, variable, start_name, end_name = loop.groups()
        opening = body.find("{", loop.start())
        try: closing = matching_brace(body, opening)
        except ValueError: continue
        loop_body = body[opening + 1:closing]
        for initializer in list_item_initializers(loop_body):
            parent = re.search(r"\bParent\s*=\s*([A-Za-z_][A-Za-z0-9_]*)\.ListBox\b", initializer)
            if not parent or parent.group(1) not in combo_names: continue
            if not re.search(rf"\bItem\s*=\s*{re.escape(variable)}\b", initializer): continue
            label_pattern = rf"(?:description\?\.Description\s*\?\?\s*)?{re.escape(variable)}\.ToString\(\)"
            if not re.search(rf"\bLabel\s*=\s*\{{\s*Text\s*=\s*{label_pattern}", initializer, re.S): continue
            members = parse_enum(zircon_root, enum_name)
            positions = {member["name"]: i for i, member in enumerate(members)}
            if start_name not in positions or end_name not in positions or positions[start_name] > positions[end_name]: continue
            entries = [{
                "label": member["label"],
                "labelSource": f"{enum_name}.{member['name']}" + (" [Description]" if member["label"] != member["name"] else ""),
                "valueExpression": f"{enum_name}.{member['name']}",
                "sourceBuilder": f"enum-range:{enum_name}.{start_name}..{end_name}",
            } for member in members[positions[start_name]:positions[end_name] + 1]]
            merge_entries(found[parent.group(1)], entries)
    return found


def selected_expression(body: str, combo_name: str) -> str | None:
    matches = list(re.finditer(rf"\b{re.escape(combo_name)}\.ListBox\.SelectItem\(\s*([^\)]+?)\s*\)\s*;", body))
    return " ".join(matches[-1].group(1).split()) if matches else None


def resolve_selected_index(body: str, expression: str | None, options: list[dict]) -> int | None:
    if not expression: return None
    target = expression
    quoted = re.fullmatch(r'"((?:\\.|[^"\\])*)"', expression)
    if quoted: target = json.dumps(decode_csharp(quoted.group(1)), ensure_ascii=False)
    elif re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", expression):
        field = re.search(rf"\b(?:public|private|protected|internal)?\s*(?:readonly\s+)?string\s+{re.escape(expression)}\s*=\s*\"((?:\\.|[^\"\\])*)\"\s*;", body)
        if field: target = json.dumps(decode_csharp(field.group(1)), ensure_ascii=False)
    normalized = target.replace(" ", "")
    for index, option in enumerate(options):
        value = str(option.get("valueExpression") or "").replace(" ", "")
        if value == normalized: return index
        if quoted and option.get("label") == decode_csharp(quoted.group(1)): return index
    return None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--zircon-root", type=Path, required=True)
    args = parser.parse_args()

    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    messages = (spec.get("language") or {}).get("English") or {}
    combos = 0; with_options = 0; option_count = 0; selected_count = 0; helper_option_count = 0; enum_option_count = 0

    for owner in [*(spec.get("windows") or []), *(spec.get("nestedWindows") or [])]:
        source_path = owner.get("sourcePath")
        class_name = owner.get("class") or owner.get("sourceClass")
        if not source_path or not class_name: continue
        path = args.zircon_root / source_path
        if not path.exists(): continue
        body = class_body(path.read_text(encoding="utf-8-sig"), str(class_name))
        if not body: continue
        combo_controls = {c.get("name"): c for c in owner.get("controls", []) if c.get("type") == "DXComboBox"}
        combos += len(combo_controls)
        if not combo_controls: continue
        found: dict[str, list[dict]] = {name: [] for name in combo_controls}
        for initializer in list_item_initializers(body):
            parent = re.search(r"\bParent\s*=\s*([A-Za-z_][A-Za-z0-9_]*)\.ListBox\b", initializer)
            if not parent or parent.group(1) not in found: continue
            label = label_from_initializer(initializer, messages)
            if not label: continue
            item = re.search(r"\bItem\s*=\s*([^,\n}]+)", initializer)
            merge_entries(found[parent.group(1)], [{
                "label": label[0],
                "labelSource": label[1],
                "valueExpression": " ".join(item.group(1).split()) if item else None,
            }])
        helper_found = helper_options(body, set(combo_controls), messages)
        for name, entries in helper_found.items():
            before = len(found[name]); merge_entries(found[name], entries); helper_option_count += len(found[name]) - before
        enum_found = enum_range_options(body, set(combo_controls), args.zircon_root)
        for name, entries in enum_found.items():
            before = len(found[name]); merge_entries(found[name], entries); enum_option_count += len(found[name]) - before
        for name, control in combo_controls.items():
            options = found[name]
            if not options: continue
            control["comboOptions"] = options
            expression = selected_expression(body, name)
            selected = resolve_selected_index(body, expression, options)
            if expression: control["comboSelectedExpression"] = expression
            if selected is not None:
                control["comboSelectedOptionIndex"] = selected
                selected_count += 1
            with_options += 1; option_count += len(options)

    lfg = next((w for w in spec.get("nestedWindows", []) if w.get("sourceClass") == "GroupLFGInputWindow"), None)
    if not lfg: raise SystemExit("GroupLFGInputWindow missing from nested source inventory")
    type_combo = next((c for c in lfg.get("controls", []) if c.get("name") == "TypeComboBox"), None)
    labels = [o.get("label") for o in (type_combo or {}).get("comboOptions", [])]
    if labels != ["PvE", "PvP"]: raise SystemExit(f"DXComboBox static option extraction drifted for GroupLFG TypeComboBox: {labels}")
    if type_combo.get("comboSelectedOptionIndex") != 0: raise SystemExit(f"GroupLFG TypeComboBox initial PvE selection not resolved: {type_combo}")

    store = next((w for w in spec.get("windows", []) if w.get("field") == "GameStoreBox"), None)
    sort_combo = next((c for c in (store or {}).get("controls", []) if c.get("name") == "SortBox"), None)
    expected_values = ["MarketPlaceStoreSort.Alphabetical", "MarketPlaceStoreSort.HighestPrice", "MarketPlaceStoreSort.LowestPrice", "MarketPlaceStoreSort.Favourite"]
    actual_values = [o.get("valueExpression") for o in (sort_combo or {}).get("comboOptions", [])]
    if actual_values != expected_values: raise SystemExit(f"GameStore AddSortOption helper extraction drifted: {actual_values}")
    if sort_combo.get("comboSelectedOptionIndex") != 0: raise SystemExit(f"GameStore initial Alphabetical combo selection not resolved: {sort_combo}")

    storage = next((w for w in spec.get("windows", []) if w.get("field") == "StorageBox"), None)
    storage_combo = next((c for c in (storage or {}).get("controls", []) if c.get("name") == "ItemTypeComboBox"), None)
    storage_options = (storage_combo or {}).get("comboOptions", [])
    if len(storage_options) != 35: raise SystemExit(f"Storage ItemTypeComboBox expected All + ItemType Nothing..Reel (35), got {len(storage_options)}")
    if storage_options[0].get("label") != "All" or storage_options[0].get("valueExpression") != "null":
        raise SystemExit(f"Storage ItemTypeComboBox All option drifted: {storage_options[:1]}")
    if storage_options[-1].get("valueExpression") != "ItemType.Reel":
        raise SystemExit(f"Storage ItemTypeComboBox enum range did not end at Reel: {storage_options[-1:]}")
    dark_stone = next((o for o in storage_options if o.get("valueExpression") == "ItemType.DarkStone"), None)
    if not dark_stone or dark_stone.get("label") != "Dark Stone":
        raise SystemExit(f"Storage ItemType [Description] resolution drifted: {dark_stone}")
    if storage_combo.get("comboSelectedOptionIndex") != 0:
        raise SystemExit(f"Storage initial SelectItem(null) did not resolve to All: {storage_combo}")

    spec["comboOptionPass"] = {
        "comboControlCount": combos,
        "combosWithDeterministicOptions": with_options,
        "deterministicOptionCount": option_count,
        "helperBuiltOptionCount": helper_option_count,
        "enumBuiltOptionCount": enum_option_count,
        "initialSelectionsResolved": selected_count,
        "runtimeOptionsInvented": False,
        "source": "direct/helper/enum-built DXListBoxItem options with literal/language/Description labels",
    }
    args.spec.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"DXComboBox deterministic options: {option_count} across {with_options}/{combos}; helper={helper_option_count}; enum={enum_option_count}; selected={selected_count}")


if __name__ == "__main__": main()
