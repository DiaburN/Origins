#!/usr/bin/env python3
"""Hardened compatibility runner for the derived Zircon geometry pass.

Adds three source-safe fixes over the base pass:
- numeric GetSize(...) indices,
- constructor parameters with default values,
- direct OnClientAreaChanged assignments such as Panel.Location = ClientArea.Location.
"""
import re

import augment_ui_derived_geometry as derived

# Zircon uses both named constants and direct numeric indices in GetSize calls.
derived.GET_SIZE_LOCAL_RE = re.compile(
    r"(?:var|Size)\s+([A-Za-z_][A-Za-z0-9_]*)\s*=\s*([A-Za-z_][A-Za-z0-9_]*)\??\.GetSize\s*\(\s*([A-Za-z_][A-Za-z0-9_]*|\d+)\s*\)",
    re.S,
)


def parse_ctor_params_v2(source: str, class_name: str) -> list[str]:
    """Read parameter names without mistaking default values for the name."""
    for match in derived.CTOR_SIGNATURE_RE.finditer(source):
        if match.group(1) != class_name:
            continue
        params: list[str] = []
        for raw in derived.parse_args(match.group(2)):
            declaration = raw.split("=", 1)[0].strip()
            names = re.findall(r"[A-Za-z_][A-Za-z0-9_]*", declaration)
            if names:
                params.append(names[-1])
        return params
    return []


derived.parse_ctor_params = parse_ctor_params_v2

_base_resolve_area_alias = derived.resolve_area_alias


def resolve_area_alias_v2(window: dict, source: str) -> int:
    """Resolve both Area aliases and direct deterministic ClientArea re-layouts."""
    changed = _base_resolve_area_alias(window, source)
    method = derived.named_method_body(source, "OnClientAreaChanged")
    if not method:
        return changed

    # A direct OnClientAreaChanged assignment is the runtime source of truth for
    # the named control. Only exact ClientArea Location/Size aliases are applied
    # here; dynamic expressions remain untouched.
    assignments = re.findall(
        r"\b([A-Za-z_][A-Za-z0-9_]*)\.(Location|Size)\s*=\s*(ClientArea\.(?:Location|Size))\s*;",
        method,
    )
    for name, prop, expression in assignments:
        control = derived.unique_control(window, name)
        if not control:
            continue
        if derived.preserve_and_set(control, prop, expression, f"source{prop}Expression"):
            changed += 1
            window.setdefault("derivedClientAreaAssignments", []).append(
                {"control": name, "property": prop, "expression": expression}
            )
    return changed


derived.resolve_area_alias = resolve_area_alias_v2

derived.main()
