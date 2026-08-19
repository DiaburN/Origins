#!/usr/bin/env python3
"""Resolve render geometry after reused-local identity canonicalization.

The core symbol pass runs before the late reused-local canonicalizer. Zircon
constructors that reuse locals such as `label` therefore expose three late cases:

1. the flat parser can carry a later assignment back onto an earlier occurrence
   of the same local name, so an occurrence must recover geometry from its own
   exact lexical object initializer;
2. constructor post-assignments (for example `label.Location = ...`) must be
   replayed after scalar symbols such as left/right/y/rowSpacing are resolved;
3. scalar locals can depend on the currently-active reused control, for example
   `x += button.Size.Width + 5` before `button` is assigned again.

This pass runs immediately after augment_reused_local_control_identity.py. It
uses exact constructor offsets plus the existing deterministic scalar resolver
to rebind those references and resolve only constructor-local geometry. It adds
or removes no controls and never materialises runtime/server/player data.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from augment_ui_symbols import (  # noqa: E402
    parse_class_symbols,
    resolve_inline_geometry_side_effects,
    statement_spans,
    update_local_symbols,
)
from build_ui_source_spec import (  # noqa: E402
    constructor_body,
    match_brace,
    split_top_level,
    strip_leading_comments,
)

NAMED_DX_RE = re.compile(
    r"(?:(?:[A-Za-z_][A-Za-z0-9_<>]*\s+)?(?P<name>[A-Za-z_][A-Za-z0-9_]*)\s*=\s*)"
    r"new\s+(?P<type>DX[A-Za-z_][A-Za-z0-9_]*)\s*\{"
)
INITIALIZER_GEOMETRY_RE = re.compile(
    r"^\s*(Location|Size|GridSize)\s*=\s*(.+?)\s*$",
    re.S,
)
POST_GEOMETRY_RE = re.compile(
    r"^([A-Za-z_][A-Za-z0-9_]*)\.(Location|Size|GridSize)\s*=\s*(.+)$",
    re.S,
)
PREPROCESSOR_RE = re.compile(r"(?m)^\s*#(?:region|endregion)\b[^\n]*\n?")
PREFIX = "reused-local-geometry-v3"


def normalise(expression: str) -> str:
    return " ".join(str(expression).strip().split())


def clean_statement(statement: str) -> str:
    # `split_top_level` correctly preserves constructor ordering, but a region
    # directive can share the same segment as the following local declaration.
    # Region directives are not executable C# and must not block deterministic
    # local parsing (e.g. CharacterDialog's `int xOffset = 40`).
    return strip_leading_comments(PREPROCESSOR_RE.sub("", statement)).strip()


def repeated_groups(item: dict) -> dict[str, list[dict]]:
    groups: dict[str, list[dict]] = defaultdict(list)
    for control in item.get("controls") or []:
        if control.get("sourceRepeatedLocal") is not True:
            continue
        source_name = str(control.get("sourceName") or "")
        if not source_name:
            continue
        groups[source_name].append(control)
    for rows in groups.values():
        rows.sort(key=lambda row: int(row.get("sourceInitializerOffset") or -1))
    return dict(groups)


def active_control(groups: dict[str, list[dict]], source_name: str, position: int) -> dict | None:
    active = None
    for control in groups.get(source_name) or []:
        offset = int(control.get("sourceInitializerOffset") or -1)
        if offset >= position:
            break
        active = control
    return active


def rebind_expression(expression: str, position: int, groups: dict[str, list[dict]]) -> tuple[str, int]:
    value = str(expression)
    changes = 0
    for source_name in sorted(groups, key=len, reverse=True):
        active = active_control(groups, source_name, position)
        if active is None:
            continue
        canonical = str(active.get("name") or "")
        if not canonical or canonical == source_name:
            continue
        pattern = rf"(?<![A-Za-z0-9_]){re.escape(source_name)}(?![A-Za-z0-9_])"
        value, count = re.subn(pattern, canonical, value)
        changes += count
    return normalise(value), changes


def initializer_geometry(body: str) -> dict[int, dict[str, str]]:
    """Return exact Location/Size/GridSize expressions keyed by lexical offset."""
    result: dict[int, dict[str, str]] = {}
    for match in NAMED_DX_RE.finditer(body):
        opening = body.find("{", match.start())
        try:
            closing = match_brace(body, opening)
        except ValueError:
            continue
        chunk = body[opening + 1:closing]
        properties: dict[str, str] = {}
        for entry in split_top_level(chunk, ','):
            property_match = INITIALIZER_GEOMETRY_RE.match(entry)
            if not property_match:
                continue
            property_name, expression = property_match.groups()
            properties[property_name] = normalise(expression)
        if properties:
            result[match.start()] = properties
    return result


def symbol_snapshots_for_offsets(
    source: str,
    body: str,
    offsets: list[int],
    groups: dict[str, list[dict]],
) -> tuple[dict[int, dict[str, str]], int]:
    """Replay constructor scalar state up to each exact initializer offset."""
    statements = statement_spans(body)
    statement_index = 0
    symbols = parse_class_symbols(source)
    snapshots: dict[int, dict[str, str]] = {}
    rebindings = 0
    for offset in sorted(set(offsets)):
        while statement_index < len(statements) and statements[statement_index][0] < offset:
            position, raw_statement = statements[statement_index]
            statement_index += 1
            statement = clean_statement(raw_statement)
            if not statement:
                continue
            canonical_statement, count = rebind_expression(statement, position, groups)
            rebindings += count
            update_local_symbols(canonical_statement, symbols)
        snapshots[offset] = dict(symbols)
    return snapshots, rebindings


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--zircon-root", type=Path, required=True)
    args = parser.parse_args()

    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    controls_before = sum(len(item.get("controls") or []) for item in [*(spec.get("windows") or []), *(spec.get("nestedWindows") or [])])
    expression_rebindings = 0
    scalar_statement_rebindings = 0
    initializer_geometry_restored = 0
    initializer_locations_restored = 0
    post_geometry_assignments = 0
    post_geometry_resolved = 0
    windows_changed = 0
    failures: list[str] = []

    for item in [*(spec.get("windows") or []), *(spec.get("nestedWindows") or [])]:
        groups = repeated_groups(item)
        if not groups:
            continue
        source_path = item.get("sourcePath")
        class_name = item.get("sourceClass") or item.get("class")
        if not source_path or not class_name:
            failures.append(f"{item.get('field') or item.get('id')}: reused locals without source identity")
            continue
        path = args.zircon_root / str(source_path)
        if not path.exists():
            failures.append(f"{item.get('field') or item.get('id')}: source path missing: {source_path}")
            continue
        source = path.read_text(encoding="utf-8-sig")
        body = constructor_body(source, str(class_name))
        if not body:
            failures.append(f"{item.get('field') or item.get('id')}: constructor body missing for {class_name}")
            continue

        changed_here = 0
        exact_initializers = initializer_geometry(body)
        repeated_controls = [control for rows in groups.values() for control in rows]
        offsets = [
            int(control.get("sourceInitializerOffset"))
            for control in repeated_controls
            if isinstance(control.get("sourceInitializerOffset"), int)
        ]
        snapshots, snapshot_rebindings = symbol_snapshots_for_offsets(source, body, offsets, groups)
        scalar_statement_rebindings += snapshot_rebindings
        expression_rebindings += snapshot_rebindings

        # First restore geometry from each repeated local's *own* lexical object
        # initializer. This prevents a later assignment to the same C# variable
        # from contaminating an earlier flattened occurrence. A later explicit
        # post-assignment is replayed below and still wins, exactly as in C#.
        for control in repeated_controls:
            offset = control.get("sourceInitializerOffset")
            if not isinstance(offset, int):
                continue
            exact = exact_initializers.get(offset) or {}
            symbols = snapshots.get(offset) or parse_class_symbols(source)
            properties = control.setdefault("properties", {})
            for property_name in ("Location", "Size", "GridSize"):
                original = exact.get(property_name)
                if original is None:
                    continue
                canonical_source, source_rebindings = rebind_expression(original, offset, groups)
                resolved = resolve_inline_geometry_side_effects(canonical_source, dict(symbols))
                resolved, resolved_rebindings = rebind_expression(resolved, offset, groups)
                expression_rebindings += source_rebindings + resolved_rebindings
                final_value = resolved if resolved else canonical_source
                properties[property_name] = final_value
                control[f"sourceInitializer{property_name}Expression"] = original
                control.setdefault("resolvedInitializerGeometry", {})[property_name] = {
                    "source": original,
                    "canonicalSource": canonical_source,
                    "resolved": final_value,
                    "sourcePosition": offset,
                    "pass": PREFIX,
                }
                if property_name == "Location":
                    # This is the exact provenance expected by the geometry QA
                    # report when a control had previously inherited a later
                    # assignment from the reused local variable.
                    control["sourceLocationExpression"] = original
                    initializer_locations_restored += 1
                initializer_geometry_restored += 1
                changed_here += 1

        # Rebind all remaining render-facing expressions at their exact lexical
        # initializer position. The exact initializer restoration above owns its
        # geometry keys; this loop mainly fixes Parent/Tag/other references.
        for control in item.get("controls") or []:
            offset = control.get("sourceInitializerOffset")
            if not isinstance(offset, int):
                continue
            properties = control.get("properties") or {}
            for property_name, expression in list(properties.items()):
                rebound, count = rebind_expression(str(expression), offset, groups)
                if not count:
                    continue
                properties[property_name] = rebound
                expression_rebindings += count
                changed_here += count

        # Replay deterministic constructor scalar state in exact source order.
        # Rebind the statement before adding it to the symbol table so an update
        # such as `x += button.Size.Width + 5` records the active canonical button.
        symbols = parse_class_symbols(source)
        for position, raw_statement in statement_spans(body):
            statement = clean_statement(raw_statement)
            if not statement:
                continue
            canonical_statement, statement_rebindings = rebind_expression(statement, position, groups)
            scalar_statement_rebindings += statement_rebindings
            expression_rebindings += statement_rebindings

            match = POST_GEOMETRY_RE.match(statement)
            if match:
                source_name, property_name, expression = match.groups()
                target = active_control(groups, source_name, position)
                if target is not None:
                    original = normalise(expression)
                    canonical_source, source_rebindings = rebind_expression(original, position, groups)
                    resolved = resolve_inline_geometry_side_effects(canonical_source, dict(symbols))
                    resolved, resolved_rebindings = rebind_expression(resolved, position, groups)
                    post_geometry_assignments += 1
                    expression_rebindings += source_rebindings + resolved_rebindings

                    properties = target.setdefault("properties", {})
                    final_value = resolved if resolved else canonical_source
                    if final_value != canonical_source:
                        provenance_key = f"source{property_name}Expression"
                        target[provenance_key] = original
                        target.setdefault("resolvedPostGeometry", {})[property_name] = {
                            "source": original,
                            "canonicalSource": canonical_source,
                            "resolved": final_value,
                            "sourcePosition": position,
                            "pass": PREFIX,
                        }
                        post_geometry_resolved += 1
                    properties[property_name] = final_value
                    changed_here += 1

            update_local_symbols(canonical_statement, symbols)

        # Hard boundary: once a source local has an active canonical occurrence,
        # no render-facing property at a known lexical position may still point
        # at the obsolete plain local identifier.
        stale: list[str] = []
        for control in item.get("controls") or []:
            offset = control.get("sourceInitializerOffset")
            if not isinstance(offset, int):
                continue
            for source_name in groups:
                active = active_control(groups, source_name, offset)
                if active is None:
                    continue
                pattern = rf"(?<![A-Za-z0-9_]){re.escape(source_name)}(?![A-Za-z0-9_])"
                for property_name, expression in (control.get("properties") or {}).items():
                    if re.search(pattern, str(expression)):
                        stale.append(f"{control.get('name')}.{property_name} -> {expression}")
        if stale:
            failures.append(
                f"{item.get('field') or item.get('id')}: stale reused-local render references remain: {stale[:12]}"
            )

        if changed_here:
            windows_changed += 1

    controls_after = sum(len(item.get("controls") or []) for item in [*(spec.get("windows") or []), *(spec.get("nestedWindows") or [])])
    if controls_after != controls_before:
        failures.append(f"control count changed: {controls_before} -> {controls_after}")

    report = {
        "passed": not failures,
        "version": 3,
        "windowsChanged": windows_changed,
        "expressionRebindings": expression_rebindings,
        "scalarStatementRebindings": scalar_statement_rebindings,
        "initializerGeometryRestored": initializer_geometry_restored,
        "initializerLocationsRestored": initializer_locations_restored,
        "postGeometryAssignments": post_geometry_assignments,
        "postGeometryResolved": post_geometry_resolved,
        "sourceExpressionsPreserved": True,
        "exactConstructorOffsetsUsed": True,
        "exactInitializerGeometryReplayed": True,
        "preprocessorRegionDirectivesIgnored": True,
        "controlsAdded": 0,
        "controlsRemoved": 0,
        "runtimePayloadsInvented": False,
        "sourceBackedOnly": True,
        "failures": failures,
    }
    spec["reusedLocalGeometryPass"] = report
    args.spec.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    if failures:
        raise SystemExit("Reused-local geometry pass failed:\n- " + "\n- ".join(failures))
    print(
        "Reused-local geometry v3: PASS -> "
        f"windows={windows_changed}, initializer geometry={initializer_geometry_restored}, "
        f"initializer locations={initializer_locations_restored}, rebindings={expression_rebindings}, "
        f"post geometry={post_geometry_assignments}, resolved={post_geometry_resolved}; controls +0"
    )


if __name__ == "__main__":
    main()
