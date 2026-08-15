#!/usr/bin/env python3
"""Resolve derived Zircon UI geometry that spans constructor/method statements.

The primary parser intentionally captures declarative object initializers. Some
Zircon geometry is deterministic but expressed through constructor arguments,
post-initializer assignments, Rectangle aliases, library GetSize calls or a
small runtime composite recipe. This pass records those relationships in the
derived manifest without modifying Zircon source and preserves every replaced
source expression for provenance.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from build_ui_source_spec import constructor_body, named_method_body, split_top_level, strip_leading_comments
from augment_ui_symbols import parse_class_symbols, statement_spans, substitute_symbols, update_local_symbols, normalise

GAME_NEW_RE = re.compile(
    r"\b([A-Za-z_][A-Za-z0-9_]*)\s*=\s*new\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(([^;{}]*)\)",
    re.S,
)
CTOR_SIGNATURE_RE = re.compile(r"\bpublic\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(([^)]*)\)")
PROPERTY_ASSIGN_RE = re.compile(
    r"^([A-Za-z_][A-Za-z0-9_]*)\.(Location|Size|GridSize|MinimumTabWidth|Index)\s*=\s*(.+)$",
    re.S,
)
TRY_LIBRARY_RE = re.compile(
    r"TryGetValue\s*\(\s*LibraryFile\.([A-Za-z0-9_]+)\s*,\s*out\s+(?:var|MirLibrary)\s+([A-Za-z_][A-Za-z0-9_]*)\s*\)",
    re.S,
)
GET_SIZE_LOCAL_RE = re.compile(
    r"(?:var|Size)\s+([A-Za-z_][A-Za-z0-9_]*)\s*=\s*([A-Za-z_][A-Za-z0-9_]*)\??\.GetSize\s*\(\s*([A-Za-z_][A-Za-z0-9_]*)\s*\)",
    re.S,
)


def parse_args(text: str) -> list[str]:
    return [normalise(part) for part in split_top_level(text, ',') if part.strip()]


def parse_ctor_params(source: str, class_name: str) -> list[str]:
    for match in CTOR_SIGNATURE_RE.finditer(source):
        if match.group(1) != class_name:
            continue
        params = []
        for raw in parse_args(match.group(2)):
            # Last identifier in the declaration is the parameter name.
            name = re.findall(r"[A-Za-z_][A-Za-z0-9_]*", raw)
            if name:
                params.append(name[-1])
        return params
    return []


def game_constructor_calls(zircon_root: Path) -> dict[str, tuple[str, list[str]]]:
    text = (zircon_root / 'Client' / 'Scenes' / 'GameScene.cs').read_text(encoding='utf-8-sig')
    body = constructor_body(text, 'GameScene')
    result: dict[str, tuple[str, list[str]]] = {}
    for match in GAME_NEW_RE.finditer(body):
        result[match.group(1)] = (match.group(2), parse_args(match.group(3)))
    return result


def collapse_literal_ternaries(expression: str) -> str:
    value = expression
    # Resolve simple literal boolean branches repeatedly. Parenthesized booleans
    # are common after symbol substitution.
    pattern = re.compile(r"\(?\s*(true|false)\s*\)?\s*\?\s*([^,:?()]+)\s*:\s*([^,?()]+)", re.I)
    for _ in range(6):
        changed = False
        def replace(match: re.Match[str]) -> str:
            nonlocal changed
            changed = True
            return normalise(match.group(2) if match.group(1).lower() == 'true' else match.group(3))
        value = pattern.sub(replace, value)
        if not changed:
            break
    return normalise(value)


def apply_bindings(expression: str, bindings: dict[str, str]) -> str:
    value = expression
    for name, bound in bindings.items():
        value = re.sub(rf"(?<!\.)\b{re.escape(name)}\b", f"({bound})", value)
    return collapse_literal_ternaries(value)


def preserve_and_set(control: dict, prop: str, new_value: str, provenance_key: str) -> bool:
    properties = control.get('properties', {})
    old = properties.get(prop)
    if old is None or normalise(str(old)) == normalise(new_value):
        return False
    control.setdefault(provenance_key, old)
    properties[prop] = normalise(new_value)
    return True


def unique_control(window: dict, name: str) -> dict | None:
    matches = [control for control in window.get('controls', []) if control.get('name') == name]
    return matches[0] if len(matches) == 1 else None


def resolve_constructor_bindings(window: dict, source: str, call: tuple[str, list[str]] | None) -> int:
    if not call:
        return 0
    class_name, args = call
    params = parse_ctor_params(source, class_name)
    if not params or len(params) != len(args):
        return 0
    bindings = {name: arg for name, arg in zip(params, args)}
    window['constructorArguments'] = args
    window['constructorBindings'] = bindings
    changed = 0
    root = window.get('root', {})
    for prop in ('Index', 'Size', 'Location', 'ClientSize'):
        if prop in root:
            new = apply_bindings(str(root[prop]), bindings)
            if new != normalise(str(root[prop])):
                window.setdefault('sourceRootExpressions', {})[prop] = root[prop]
                root[prop] = new
                changed += 1
    for control in window.get('controls', []):
        for prop in ('Location', 'Size', 'GridSize', 'MinimumTabWidth', 'Index'):
            if prop not in control.get('properties', {}):
                continue
            old = str(control['properties'][prop])
            new = apply_bindings(old, bindings)
            if new != normalise(old):
                control.setdefault(f'source{prop}Expression', old)
                control['properties'][prop] = new
                changed += 1
    return changed


def resolve_post_assignments(window: dict, source: str) -> int:
    """Apply local symbols at the actual source position of post-init assignments."""
    body = constructor_body(source, window.get('class', ''))
    if not body:
        return 0
    symbols = parse_class_symbols(source)
    changed = 0
    by_name: dict[str, list[dict]] = {}
    for control in window.get('controls', []):
        by_name.setdefault(control.get('name', ''), []).append(control)

    for _, raw in statement_spans(body):
        statement = strip_leading_comments(raw)
        assignment = PROPERTY_ASSIGN_RE.match(statement)
        if assignment:
            name, prop, expression = assignment.groups()
            matches = by_name.get(name, [])
            if len(matches) == 1:
                resolved = collapse_literal_ternaries(substitute_symbols(expression, symbols))
                if preserve_and_set(matches[0], prop, resolved, f'source{prop}Expression'):
                    changed += 1
        update_local_symbols(statement, symbols)
    return changed


def resolve_area_alias(window: dict, source: str) -> int:
    """Resolve the common `Area = ClientArea; Area.Inflate(x,y)` pattern."""
    method = named_method_body(source, 'OnClientAreaChanged')
    if not method or not re.search(r"\bArea\s*=\s*ClientArea\s*;", method):
        return 0
    inflate = re.search(r"\bArea\.Inflate\s*\(\s*(-?\d+)\s*,\s*(-?\d+)\s*\)\s*;", method)
    dx = int(inflate.group(1)) if inflate else 0
    dy = int(inflate.group(2)) if inflate else 0
    location = 'ClientArea.Location' if dx == 0 and dy == 0 else f'new Point(ClientArea.X - {dx}, ClientArea.Y - {dy})'
    size = 'ClientArea.Size' if dx == 0 and dy == 0 else f'new Size(ClientArea.Width + {dx * 2}, ClientArea.Height + {dy * 2})'
    changed = 0
    for control in window.get('controls', []):
        p = control.get('properties', {})
        if p.get('Location') == 'Area.Location':
            if preserve_and_set(control, 'Location', location, 'sourceLocationExpression'):
                changed += 1
        if p.get('Size') == 'Area.Size':
            if preserve_and_set(control, 'Size', size, 'sourceSizeExpression'):
                changed += 1
    if changed:
        window['derivedArea'] = {'source': 'OnClientAreaChanged', 'inflate': [dx, dy]}
    return changed


def library_aliases(source: str) -> dict[str, str]:
    return {alias: library for library, alias in TRY_LIBRARY_RE.findall(source)}


def add_asset_ref(spec: dict, library: str, index: int) -> None:
    refs = spec.setdefault('assetRefs', {}).setdefault(library, [])
    if index not in refs:
        refs.append(index)
        refs.sort()


def resolve_getsize_locals(spec: dict, window: dict, source: str) -> int:
    aliases = library_aliases(source)
    constants = parse_class_symbols(source)
    size_locals: dict[str, tuple[str, int]] = {}
    for match in GET_SIZE_LOCAL_RE.finditer(source):
        local_name, alias, index_expr = match.groups()
        library = aliases.get(alias)
        if not library:
            continue
        resolved_index = substitute_symbols(index_expr, constants)
        numeric = re.fullmatch(r"\(?\s*(\d+)\s*\)?", resolved_index)
        if not numeric:
            continue
        index = int(numeric.group(1))
        size_locals[local_name] = (library, index)
        add_asset_ref(spec, library, index)

    changed = 0
    for control in window.get('controls', []):
        for prop in ('Location', 'Size'):
            old = control.get('properties', {}).get(prop)
            if old is None:
                continue
            new = str(old)
            for local_name, (library, index) in size_locals.items():
                new = re.sub(rf"\b{re.escape(local_name)}\.Width\b", f'AssetSize.{library}.{index}.Width', new)
                new = re.sub(rf"\b{re.escape(local_name)}\.Height\b", f'AssetSize.{library}.{index}.Height', new)
            if new != str(old):
                if preserve_and_set(control, prop, new, f'source{prop}Expression'):
                    changed += 1
    if size_locals:
        window['librarySizeLocals'] = {name: {'library': library, 'index': index} for name, (library, index) in size_locals.items()}
    return changed


def add_horse_tame_recipe(spec: dict, window: dict, source: str) -> int:
    if window.get('class') != 'HorseTameDialog':
        return 0
    constants = parse_class_symbols(source)
    def integer(name: str) -> int | None:
        value = constants.get(name)
        if value is None:
            return None
        # Repeatedly substitute other scalar constants.
        resolved = substitute_symbols(value, constants).replace('(', '').replace(')', '').strip()
        try:
            return int(eval(resolved, {'__builtins__': {}}, {}))
        except Exception:
            return None

    loop = integer('LoopBaseIndex')
    angle = integer('AngleBaseIndex')
    angle_count = integer('AngleCount')
    fill = integer('ProgressFillIndex')
    outline = integer('ProgressOutlineIndex')
    if None in (loop, angle, angle_count, fill, outline):
        return 0
    end = angle + angle_count - 1
    for index in range(loop, end + 1):
        add_asset_ref(spec, 'GameInter', index)
    add_asset_ref(spec, 'GameInter', fill)
    add_asset_ref(spec, 'GameInter', outline)
    add_asset_ref(spec, 'Interface', 80)
    window['derivedGeometry'] = {
        'type': 'HorseTameDialog',
        'animationLibrary': 'GameInter',
        'animationStart': loop,
        'animationEnd': end,
        'progressLibrary': 'GameInter',
        'progressFillIndex': fill,
        'progressOutlineIndex': outline,
        'healthBarLibrary': 'Interface',
        'healthBarIndex': 80,
        'source': 'GetImageBounds + GetSize in HorseTameDialog constructor',
    }
    return 1


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--spec', type=Path, required=True)
    parser.add_argument('--zircon-root', type=Path, required=True)
    args = parser.parse_args()

    spec = json.loads(args.spec.read_text(encoding='utf-8'))
    calls = game_constructor_calls(args.zircon_root)
    metrics = {
        'constructorBindingChanges': 0,
        'postAssignmentChanges': 0,
        'areaAliasChanges': 0,
        'librarySizeChanges': 0,
        'horseRecipes': 0,
    }

    for window in spec.get('windows', []):
        source_path = window.get('sourcePath')
        if not source_path:
            continue
        path = args.zircon_root / source_path
        if not path.exists():
            continue
        source = path.read_text(encoding='utf-8-sig')
        metrics['constructorBindingChanges'] += resolve_constructor_bindings(window, source, calls.get(window.get('field', '')))
        metrics['postAssignmentChanges'] += resolve_post_assignments(window, source)
        metrics['areaAliasChanges'] += resolve_area_alias(window, source)
        metrics['librarySizeChanges'] += resolve_getsize_locals(spec, window, source)
        metrics['horseRecipes'] += add_horse_tame_recipe(spec, window, source)

    spec['derivedGeometryPass'] = {
        'sourceExpressionsPreserved': True,
        **metrics,
    }
    args.spec.write_text(json.dumps(spec, indent=2, ensure_ascii=False), encoding='utf-8')
    for key, value in metrics.items():
        print(f'{key}: {value}')


if __name__ == '__main__':
    main()
