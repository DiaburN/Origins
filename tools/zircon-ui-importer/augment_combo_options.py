#!/usr/bin/env python3
"""Extract deterministic DXComboBox list options from Zircon source.

Only DXListBoxItem entries whose label is a C# string literal or a resolved
CEnvir.Language key are promoted. Runtime/database-derived options are left out.
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


def label_from_initializer(initializer: str, messages: dict[str, str]) -> tuple[str, str] | None:
    literal = re.search(r'\bLabel\s*=\s*\{\s*Text\s*=\s*"((?:\\.|[^"\\])*)"', initializer, re.S)
    if literal: return decode_csharp(literal.group(1)), "literal"
    language = re.search(r"\bLabel\s*=\s*\{\s*Text\s*=\s*CEnvir\.Language\.([A-Za-z_][A-Za-z0-9_]*)", initializer, re.S)
    if language and language.group(1) in messages: return messages[language.group(1)], f"CEnvir.Language.{language.group(1)}"
    return None


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
    combos = 0; with_options = 0; option_count = 0; selected_count = 0

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
            entry = {
                "label": label[0],
                "labelSource": label[1],
                "valueExpression": " ".join(item.group(1).split()) if item else None,
            }
            if not any(existing["label"] == entry["label"] and existing.get("valueExpression") == entry.get("valueExpression") for existing in found[parent.group(1)]):
                found[parent.group(1)].append(entry)
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

    # Regression sentinel: this nested source has two literal options and selects
    # TypeValue="PvE" in its constructor. If this fails, direct option extraction broke.
    lfg = next((w for w in spec.get("nestedWindows", []) if w.get("sourceClass") == "GroupLFGInputWindow"), None)
    if not lfg: raise SystemExit("GroupLFGInputWindow missing from nested source inventory")
    type_combo = next((c for c in lfg.get("controls", []) if c.get("name") == "TypeComboBox"), None)
    labels = [o.get("label") for o in (type_combo or {}).get("comboOptions", [])]
    if labels != ["PvE", "PvP"]:
        raise SystemExit(f"DXComboBox static option extraction drifted for GroupLFG TypeComboBox: {labels}")
    if type_combo.get("comboSelectedOptionIndex") != 0:
        raise SystemExit(f"GroupLFG TypeComboBox initial PvE selection not resolved: {type_combo}")

    spec["comboOptionPass"] = {
        "comboControlCount": combos,
        "combosWithDeterministicOptions": with_options,
        "deterministicOptionCount": option_count,
        "initialSelectionsResolved": selected_count,
        "runtimeOptionsInvented": False,
        "source": "direct DXListBoxItem initializers with literal/resolved-language labels",
    }
    args.spec.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"DXComboBox deterministic options: {option_count} across {with_options}/{combos} combo controls; selected={selected_count}")


if __name__ == "__main__": main()
