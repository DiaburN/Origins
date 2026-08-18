#!/usr/bin/env python3
"""Inventory constructor-reachable helper methods that create Zircon UI.

The flat constructor parser can miss controls when a window constructor delegates
UI creation into helpers such as BigMapDialog.CreateSidePanel/CreateRows/
CreateScrollBar. This audit walks same-class helper calls from each constructor,
records source-created control types and verifies known deterministic BigMap
helpers are represented by the promoted manifest. It never fabricates controls.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter, deque
from pathlib import Path


def match_brace(text: str, opening: int) -> int:
    depth = 0
    quote = None
    escaped = False
    i = opening
    while i < len(text):
        char = text[i]
        if quote:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
            i += 1
            continue
        if char in ('"', "'"):
            quote = char
            i += 1
            continue
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return i
        i += 1
    return len(text) - 1


def class_body(text: str, name: str) -> str:
    match = re.search(rf"\bclass\s+{re.escape(name)}\b[^{{]*\{{", text)
    if not match:
        return ""
    opening = text.find("{", match.start())
    return text[opening + 1:match_brace(text, opening)]


def constructor_body(body: str, name: str) -> str:
    match = re.search(rf"\b{re.escape(name)}\s*\([^)]*\)\s*\{{", body)
    if not match:
        return ""
    opening = body.find("{", match.start())
    return body[opening + 1:match_brace(body, opening)]


def methods(body: str) -> dict[str, list[str]]:
    # Deliberately source-oriented rather than a C# compiler: only ordinary
    # class methods with access modifiers are relevant to constructor delegation.
    pattern = re.compile(
        r"(?m)^[ \t]*(?:public|private|protected|internal)\s+"
        r"(?:(?:static|virtual|override|sealed|async|unsafe|new)\s+)*"
        r"[A-Za-z_][A-Za-z0-9_<>,.\[\]? ]*\s+"
        r"([A-Za-z_][A-Za-z0-9_]*)\s*\([^;{}]*\)\s*\{"
    )
    result: dict[str, list[str]] = {}
    for match in pattern.finditer(body):
        opening = body.find("{", match.start())
        chunk = body[opening + 1:match_brace(body, opening)]
        result.setdefault(match.group(1), []).append(chunk)
    return result


def calls(chunk: str, known: set[str]) -> set[str]:
    found = set(re.findall(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*\(", chunk))
    return found & known


def created_types(chunk: str) -> list[str]:
    values = re.findall(r"\bnew\s+([A-Za-z_][A-Za-z0-9_]*)\b", chunk)
    return sorted({
        value for value in values
        if value.startswith("DX") or value.endswith(("Row", "Line", "Control", "Dialog", "Panel", "Window", "Tab"))
    })


def named_creations(chunk: str) -> list[str]:
    pattern = re.compile(
        r"\b([A-Za-z_][A-Za-z0-9_]*)\s*=\s*new\s+"
        r"([A-Za-z_][A-Za-z0-9_]*)\b"
    )
    return sorted({name for name, type_name in pattern.findall(chunk)
                   if type_name.startswith("DX") or type_name.endswith(("Row", "Line", "Control", "Dialog", "Panel", "Window", "Tab"))})


def runtime_bound(chunk: str) -> bool:
    runtime_patterns = (
        r"\bGameScene\.Game\b",
        r"\bGlobals\.",
        r"\bMapObject\.",
        r"\.Binding\b",
        r"\bSelectedInfo\b",
        r"\bDataDictionary\b",
        r"\bEnqueue\s*\(",
    )
    return any(re.search(pattern, chunk) for pattern in runtime_patterns)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--zircon-root", type=Path, required=True)
    args = parser.parse_args()

    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    rows = []

    for window in [*(spec.get("windows") or []), *(spec.get("nestedWindows") or [])]:
        source_path = str(window.get("sourcePath") or "")
        source_class = str(window.get("class") or window.get("sourceClass") or "")
        path = args.zircon_root / source_path
        if not source_path or not source_class or not path.exists():
            continue

        body = class_body(path.read_text(encoding="utf-8-sig"), source_class)
        ctor = constructor_body(body, source_class)
        method_map = methods(body)
        if not ctor or not method_map:
            continue

        known = set(method_map)
        queue = deque(sorted(calls(ctor, known)))
        visited: set[str] = set()
        depth: dict[str, int] = {name: 1 for name in queue}

        while queue:
            helper = queue.popleft()
            if helper in visited:
                continue
            visited.add(helper)
            chunks = method_map.get(helper) or []
            combined = "\n".join(chunks)
            for child in sorted(calls(combined, known)):
                if child not in visited:
                    depth[child] = min(depth.get(child, 999), depth.get(helper, 1) + 1)
                    queue.append(child)

            types = created_types(combined)
            if not types:
                continue

            named = named_creations(combined)
            controls = window.get("controls") or []
            control_names = {str(control.get("name") or "") for control in controls}
            named_materialized = [name for name in named if name in control_names]
            provenance_materialized = [
                str(control.get("name") or "")
                for control in controls
                if helper in str(control.get("sourceGenerated") or "")
            ]
            materialized_names = sorted(set(named_materialized + provenance_materialized))
            is_runtime = runtime_bound(combined)
            classification = "runtime-bound" if is_runtime else "deterministic-source"
            status = "materialized" if materialized_names else (
                "runtime-bound" if is_runtime else "audited-source-only"
            )

            rows.append({
                "id": window.get("id"),
                "field": window.get("field"),
                "sourceClass": source_class,
                "sourcePath": source_path,
                "helper": helper,
                "constructorReachDepth": depth.get(helper, 1),
                "createdTypes": types,
                "namedCreations": named,
                "materializedControlNames": materialized_names,
                "classification": classification,
                "status": status,
                "sourceBackedOnly": True,
            })

    # BigMap is the known regression class that motivated this pass. Its helper
    # chain is deterministic at construction time and the rows/scrollbars must
    # be represented without inventing SelectedInfo/NPC/monster payloads.
    bigmap = {row["helper"]: row for row in rows if row["sourceClass"] == "BigMapDialog"}
    required = {"CreateSidePanel", "CreateRows", "CreateScrollBar"}
    missing = sorted(required - set(bigmap))
    if missing:
        raise SystemExit(f"BigMap constructor UI helper inventory incomplete: {missing}")
    for helper in ("CreateRows", "CreateScrollBar"):
        if bigmap[helper]["classification"] != "deterministic-source":
            raise SystemExit(f"BigMap {helper} misclassified: {bigmap[helper]}")
        if bigmap[helper]["status"] != "materialized":
            raise SystemExit(f"BigMap {helper} deterministic UI is not materialized: {bigmap[helper]}")

    counts = Counter(row["classification"] for row in rows)
    statuses = Counter(row["status"] for row in rows)
    report = {
        "passed": True,
        "helperCount": len(rows),
        "classificationCounts": dict(counts),
        "statusCounts": dict(statuses),
        "rows": rows,
        "knownBigMapHelpers": sorted(required),
        "knownBigMapHelpersMaterialized": True,
        "controlsFabricatedByAudit": False,
        "sourceBackedOnly": True,
    }
    spec["uiCreationHelperInventory"] = report
    args.spec.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(
        "Constructor-reachable UI helper inventory: PASS -> "
        f"{len(rows)} helpers; classifications={dict(counts)}; statuses={dict(statuses)}"
    )


if __name__ == "__main__":
    main()
