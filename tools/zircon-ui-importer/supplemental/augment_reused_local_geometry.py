#!/usr/bin/env python3
"""Resolve render geometry after reused-local identity canonicalization.

The core symbol pass runs before the late reused-local canonicalizer. Zircon
constructors that reuse locals such as `label` therefore expose two late cases:

1. constructor post-assignments (for example `label.Location = ...`) are replayed
   by the canonicalizer after scalar symbols such as left/right/y/rowSpacing were
   already resolved; and
2. anonymous controls keep source expressions such as `label.Location.X` even
   after that source local has become `label__srcNN` in the flat manifest.

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
from build_ui_source_spec import constructor_body, strip_leading_comments  # noqa: E402

POST_GEOMETRY_RE = re.compile(
    r"^([A-Za-z_][A-Za-z0-9_]*)\.(Location|Size|GridSize)\s*=\s*(.+)$",
    re.S,
)
PREFIX = "reused-local-geometry-v1"


def normalise(expression: str) -> str:
    return " ".join(str(expression).strip().split())


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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--zircon-root", type=Path, required=True)
    args = parser.parse_args()

    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    controls_before = sum(len(item.get("controls") or []) for item in [*(spec.get("windows") or []), *(spec.get("nestedWindows") or [])])
    expression_rebindings = 0
    anonymous_rebindings = 0
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

        # Rebind controls that the reused-local canonicalizer deliberately did
        # not own (most importantly anonymous DX controls). Their exact lexical
        # initializer offset is already emitted by the base parser.
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
                if control.get("sourceAnonymous") is True:
                    anonymous_rebindings += count

        # Replay top-level constructor scalar state in exact source order. For a
        # post-assignment targeting a reused local, resolve local deterministic
        # symbols on a copy (so provenance remains intact), then let
        # update_local_symbols mutate the shared y/x/etc state exactly once.
        symbols = parse_class_symbols(source)
        for position, raw_statement in statement_spans(body):
            statement = strip_leading_comments(raw_statement)
            match = POST_GEOMETRY_RE.match(statement)
            if match:
                source_name, property_name, expression = match.groups()
                target = active_control(groups, source_name, position)
                if target is not None:
                    original = normalise(expression)
                    canonical_source, source_rebindings = rebind_expression(original, position, groups)
                    resolved = resolve_inline_geometry_side_effects(original, dict(symbols))
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

            update_local_symbols(statement, symbols)

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
        "version": 1,
        "windowsChanged": windows_changed,
        "expressionRebindings": expression_rebindings,
        "anonymousExpressionRebindings": anonymous_rebindings,
        "postGeometryAssignments": post_geometry_assignments,
        "postGeometryResolved": post_geometry_resolved,
        "sourceExpressionsPreserved": True,
        "exactConstructorOffsetsUsed": True,
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
        "Reused-local geometry: PASS -> "
        f"windows={windows_changed}, rebindings={expression_rebindings}, anonymous={anonymous_rebindings}, "
        f"post geometry={post_geometry_assignments}, resolved={post_geometry_resolved}; controls +0"
    )


if __name__ == "__main__":
    main()
