#!/usr/bin/env python3
"""Resolve deterministic C# symbols used by Zircon UI geometry and number state.

This is a derived-manifest augmentation step. It never edits Zircon source.
Class constants, static readonly Point/Size values and simple constructor-local
numeric/Point/Size variables are substituted into render-facing geometry while
the original expression is preserved as provenance.

C# also permits a local mutation inside a geometry expression, for example:
`label.Location = new Point(left, y += rowSpacing)`. Those side effects are
executed here in constructor order so successive controls see the new `y`, just
as the original Zircon client does.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from build_ui_source_spec import constructor_body, split_top_level, strip_leading_comments, top_level_statements

CONTROL_INIT_RE = re.compile(
    r"(?:(?:[A-Za-z_][A-Za-z0-9_<>]*\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*)"
    r"new\s+(DX[A-Za-z_][A-Za-z0-9_]*)\s*\{"
)
SCALAR_CONST_RE = re.compile(
    r"(?:public|private|protected|internal)?\s*(?:static\s+)?const\s+"
    r"(?:int|float|double|decimal)\s+([^;]+);", re.M,
)
POINT_SIZE_FIELD_RE = re.compile(
    r"(?:public|private|protected|internal)?\s*(?:static\s+)?readonly\s+"
    r"(Point|Size)\s+([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(new\s+\1\s*\([^;]+\))\s*;", re.M,
)
LOCAL_DECL_RE = re.compile(r"^(?:const\s+)?(int|float|double|decimal|Point|Size)\s+(.+)$", re.S)
LOCAL_ASSIGN_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)\s*(\+=|-=|=)\s*(.+)$", re.S)
PROPERTY_GEOMETRY_ASSIGN_RE = re.compile(
    r"^[A-Za-z_][A-Za-z0-9_]*(?:\[[^\]]+\])?\.(?:Location|Size|GridSize)\s*=\s*(new\s+(?:Point|Size)\s*\(.*\))$",
    re.S,
)
NUMBER_STATE_ASSIGN_RE = re.compile(
    r"^([A-Za-z_][A-Za-z0-9_]*)\.(Value|MinValue|MaxValue|Change)\s*=\s*(.+)$", re.S,
)
NUMBER_TYPES = {"DXNumberBox", "DXNumberTextBox"}
COMMON_SYMBOLS: dict[str, str] = {"ResizeBuffer": "9"}


def normalise(expression: str) -> str:
    return " ".join(expression.strip().split())


def statement_spans(body: str) -> list[tuple[int, str]]:
    parts = split_top_level(body, ';')
    result: list[tuple[int, str]] = []
    cursor = 0
    for raw in parts:
        if not raw.strip():
            cursor += len(raw) + 1
            continue
        result.append((cursor, raw.strip()))
        cursor += len(raw) + 1
    return result


def parse_declarators(text: str) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for part in split_top_level(text, ','):
        match = re.match(r"\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.+?)\s*$", part, re.S)
        if match:
            out.append((match.group(1), normalise(match.group(2))))
    return out


def parse_class_symbols(text: str) -> dict[str, str]:
    symbols = dict(COMMON_SYMBOLS)
    for match in SCALAR_CONST_RE.finditer(text):
        for name, expression in parse_declarators(match.group(1)):
            symbols[name] = expression
    for match in POINT_SIZE_FIELD_RE.finditer(text):
        symbols[match.group(2)] = normalise(match.group(3))
    return symbols


def pair_components(expression: str, kind: str) -> tuple[str, str] | None:
    match = re.match(rf"^new\s+{kind}\s*\((.*)\)$", expression.strip(), re.S)
    if not match:
        return None
    args = split_top_level(match.group(1), ',')
    if len(args) != 2:
        return None
    return normalise(args[0]), normalise(args[1])


def substitute_symbols(expression: str, symbols: dict[str, str]) -> str:
    """Substitute known scalar and Point/Size components without evaluating C#."""
    value = expression
    for _ in range(12):
        before = value
        for name, symbol_expression in list(symbols.items()):
            point = pair_components(symbol_expression, "Point")
            if point:
                value = re.sub(rf"\b{re.escape(name)}\.X\b", f"({point[0]})", value)
                value = re.sub(rf"\b{re.escape(name)}\.Y\b", f"({point[1]})", value)
            size = pair_components(symbol_expression, "Size")
            if size:
                value = re.sub(rf"\b{re.escape(name)}\.Width\b", f"({size[0]})", value)
                value = re.sub(rf"\b{re.escape(name)}\.Height\b", f"({size[1]})", value)
        for name, symbol_expression in list(symbols.items()):
            if pair_components(symbol_expression, "Point") or pair_components(symbol_expression, "Size"):
                continue
            value = re.sub(rf"(?<!\.)\b{re.escape(name)}\b", f"({symbol_expression})", value)
        if value == before:
            break
    return normalise(value)


def resolve_inline_geometry_side_effects(expression: str, symbols: dict[str, str]) -> str:
    """Resolve Point/Size components and execute inline `local +=/-= expr`.

    The mutation is intentionally limited to a top-level Point/Size component.
    This covers Zircon's constructor geometry idiom while avoiding event/lambda
    bodies or arbitrary C# evaluation.
    """
    text=normalise(expression)
    for kind in ("Point", "Size"):
        components=pair_components(text,kind)
        if not components:
            continue
        resolved=[]
        for component in components:
            mutation=LOCAL_ASSIGN_RE.match(component)
            if mutation and mutation.group(2) in {"+=","-="} and mutation.group(1) in symbols:
                name,operator,rhs=mutation.groups()
                prior=substitute_symbols(symbols[name],symbols)
                resolved_rhs=substitute_symbols(rhs,symbols)
                op="+" if operator=="+=" else "-"
                updated=f"({prior}) {op} ({resolved_rhs})"
                symbols[name]=updated
                resolved.append(f"({updated})")
            else:
                resolved.append(substitute_symbols(component,symbols))
        return normalise(f"new {kind}({resolved[0]}, {resolved[1]})")
    return substitute_symbols(text,symbols)


def update_local_symbols(statement: str, symbols: dict[str, str]) -> None:
    statement = strip_leading_comments(statement)
    declaration = LOCAL_DECL_RE.match(statement)
    if declaration:
        for name, expression in parse_declarators(declaration.group(2)):
            symbols[name] = substitute_symbols(expression, symbols)
        return

    assignment = LOCAL_ASSIGN_RE.match(statement)
    if assignment:
        name, operator, expression = assignment.groups()
        if name in symbols:
            resolved = substitute_symbols(expression, symbols)
            if operator == "=": symbols[name] = resolved
            elif operator == "+=": symbols[name] = f"({symbols[name]}) + ({resolved})"
            elif operator == "-=": symbols[name] = f"({symbols[name]}) - ({resolved})"
        return

    # Constructor statements such as `label.Location = new Point(left, y += rowSpacing)`
    # mutate the local `y`. Event subscriptions/lambdas are deliberately excluded.
    if "=>" in statement:
        return
    geometry=PROPERTY_GEOMETRY_ASSIGN_RE.match(statement)
    if geometry:
        resolve_inline_geometry_side_effects(geometry.group(1),symbols)


def control_offsets(body: str) -> list[int]:
    return [match.start() for match in CONTROL_INIT_RE.finditer(body)]


def symbol_snapshots(body: str, class_symbols: dict[str, str], control_count: int) -> list[dict[str, str]]:
    offsets = control_offsets(body)
    if len(offsets) < control_count:
        offsets += [len(body)] * (control_count - len(offsets))
    offsets = offsets[:control_count]
    statements = statement_spans(body)
    symbols = dict(class_symbols)
    snapshots: list[dict[str, str]] = []
    statement_index = 0
    for offset in offsets:
        while statement_index < len(statements) and statements[statement_index][0] < offset:
            _, statement = statements[statement_index]
            update_local_symbols(statement, symbols)
            statement_index += 1
        snapshots.append(dict(symbols))
    return snapshots


def simplify_geometry(control: dict, symbols: dict[str, str]) -> int:
    changed = 0
    properties = control.get("properties", {})
    for property_name in ("Location", "Size", "GridSize", "MinimumTabWidth"):
        original = properties.get(property_name)
        if original is None:
            continue
        # This operates on a snapshot; execute any inline mutation only on a copy
        # so the shared snapshot is not modified a second time.
        local_symbols=dict(symbols)
        resolved = resolve_inline_geometry_side_effects(str(original), local_symbols) if property_name in {"Location","Size","GridSize"} else substitute_symbols(str(original),symbols)
        if resolved == normalise(str(original)):
            continue
        provenance_key = f"source{property_name}Expression"
        control.setdefault(provenance_key, original)
        properties[property_name] = resolved
        control.setdefault("resolvedGeometrySymbols", {})[property_name] = {
            name: expression for name, expression in symbols.items() if re.search(rf"\b{re.escape(name)}\b", str(original))
        }
        changed += 1
    return changed


def apply_number_state_assignments(body: str, controls: list[dict], class_symbols: dict[str, str]) -> int:
    candidates: dict[str, list[dict]] = {}
    for control in controls:
        if control.get("type") not in NUMBER_TYPES:
            continue
        name = control.get("name")
        if not name or "__" in name:
            continue
        candidates.setdefault(name, []).append(control)
    unique = {name: rows[0] for name, rows in candidates.items() if len(rows) == 1}
    if not unique:
        return 0
    symbols = dict(class_symbols)
    changed = 0
    for raw in top_level_statements(body):
        statement = strip_leading_comments(raw)
        update_local_symbols(statement, symbols)
        match = NUMBER_STATE_ASSIGN_RE.match(statement)
        if not match:
            continue
        name, property_name, expression = match.groups()
        control = unique.get(name)
        if not control:
            continue
        expression = normalise(expression)
        resolved = substitute_symbols(expression, symbols)
        properties = control.setdefault("properties", {})
        previous = properties.get(property_name)
        if previous is not None and normalise(str(previous)) != resolved:
            control.setdefault("sourceInitializerNumberState", {})[property_name] = previous
        control.setdefault("sourceNumberStateAssignments", {})[property_name] = expression
        properties[property_name] = resolved
        changed += 1
    return changed


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--zircon-root", type=Path, required=True)
    args = parser.parse_args()
    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    resolved_properties = 0
    windows_with_symbols = 0
    number_state_assignments = 0
    windows_with_number_state = 0
    for window in spec.get("windows", []):
        source_path = window.get("sourcePath")
        if not source_path: continue
        path = args.zircon_root / source_path
        if not path.exists(): continue
        text = path.read_text(encoding="utf-8-sig")
        body = constructor_body(text, window.get("class", ""))
        if not body: continue
        class_symbols = parse_class_symbols(text)
        controls = window.get("controls", [])
        snapshots = symbol_snapshots(body, class_symbols, len(controls))
        window_changed = 0
        for control, symbols in zip(controls, snapshots):
            window_changed += simplify_geometry(control, symbols)
        state_changed = apply_number_state_assignments(body, controls, class_symbols)
        if state_changed:
            windows_with_number_state += 1; number_state_assignments += state_changed
        if window_changed:
            windows_with_symbols += 1; resolved_properties += window_changed
    spec["geometrySymbols"] = {
        "source": "Zircon class constants/static readonly Point/Size and constructor-local deterministic variables including inline compound geometry assignments",
        "windowsChanged": windows_with_symbols,
        "propertiesSimplified": resolved_properties,
        "sourceExpressionsPreserved": True,
        "inlineCompoundAssignmentsSupported": True,
        "commonInheritedSymbols": COMMON_SYMBOLS,
    }
    spec["numberControlState"] = {
        "source": "constructor-level DXNumberBox/DXNumberTextBox Value/MinValue/MaxValue/Change assignments",
        "windowsChanged": windows_with_number_state,
        "assignmentsApplied": number_state_assignments,
        "sourceExpressionsPreserved": True,
    }
    args.spec.write_text(json.dumps(spec, indent=2, ensure_ascii=False), encoding="utf-8")
    print("Windows with deterministic symbol substitutions:", windows_with_symbols)
    print("Geometry properties simplified:", resolved_properties)
    print("Windows with number-control state assignments:", windows_with_number_state)
    print("Number-control state assignments applied:", number_state_assignments)

if __name__ == "__main__":
    main()
