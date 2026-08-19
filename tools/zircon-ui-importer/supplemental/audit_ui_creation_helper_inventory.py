#!/usr/bin/env python3
"""Audit helper-created Zircon UI without confusing callbacks with constructors.

The flat constructor parser can miss controls when a window delegates creation to
helpers (BigMap.CreateRows/CreateScrollBar), while other helpers intentionally
create UI only later (ChatOptions.AddNewTab) or from server/runtime data
(HelpDialog.Add, MagicDialog.CreateTabs). This pass inventories both classes of
helper, follows only *immediate* constructor/helper calls, and records deferred/
runtime composites without fabricating controls or payloads.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter, deque
from pathlib import Path


CONTROL_SUFFIXES = (
    "Row", "Line", "Control", "Dialog", "Panel", "Window", "Tab",
    "Container", "Item", "Cell",
)


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
    match = re.search(rf"\b{re.escape(name)}\s*\([^)]*\)\s*(?::\s*[^{{]+)?\{{", body)
    if not match:
        return ""
    opening = body.find("{", match.start())
    return body[opening + 1:match_brace(body, opening)]


def methods(body: str) -> dict[str, list[str]]:
    # Source-oriented, intentionally not a C# compiler. Ordinary class methods
    # are sufficient for the UI helper patterns in Client/Scenes/Views.
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


def strip_event_lambdas(chunk: str) -> str:
    """Mask event callback bodies so callback calls are not constructor calls.

    `button.MouseClick += (o,e) => AddNewTab(null);` is deferred UI creation,
    not something the ChatOptionsDialog constructor executes. Only `+=` lambda
    handlers are stripped; LINQ lambdas remain available to runtime-data tests.
    """
    chars = list(chunk)
    pos = 0
    while True:
        plus = chunk.find("+=", pos)
        if plus < 0:
            break
        arrow = chunk.find("=>", plus + 2)
        if arrow < 0:
            break
        # If a statement terminates before the lambda arrow, this += was a
        # method-group subscription and the later arrow belongs elsewhere.
        semicolon = chunk.find(";", plus + 2, arrow)
        if semicolon >= 0:
            pos = semicolon + 1
            continue
        cursor = arrow + 2
        while cursor < len(chunk) and chunk[cursor].isspace():
            cursor += 1
        end = cursor
        if cursor < len(chunk) and chunk[cursor] == "{":
            end = match_brace(chunk, cursor) + 1
            while end < len(chunk) and chunk[end].isspace():
                end += 1
            if end < len(chunk) and chunk[end] == ";":
                end += 1
        else:
            semi = chunk.find(";", cursor)
            end = len(chunk) if semi < 0 else semi + 1
        for i in range(plus, min(end, len(chars))):
            if chars[i] != "\n":
                chars[i] = " "
        pos = max(end, plus + 2)
    return "".join(chars)


def calls(chunk: str, known: set[str], *, immediate_only: bool = False) -> set[str]:
    source = strip_event_lambdas(chunk) if immediate_only else chunk
    found = set(re.findall(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*\(", source))
    return found & known


def is_controlish(type_name: str) -> bool:
    return type_name.startswith("DX") or type_name.endswith(CONTROL_SUFFIXES)


def created_types(chunk: str) -> list[str]:
    values = re.findall(r"\bnew\s+([A-Za-z_][A-Za-z0-9_]*)\b", chunk)
    return sorted({value for value in values if is_controlish(value)})


def named_creations(chunk: str) -> list[str]:
    pattern = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*=\s*new\s+([A-Za-z_][A-Za-z0-9_]*)\b")
    return sorted({name for name, type_name in pattern.findall(chunk) if is_controlish(type_name)})


def external_runtime_bound(chunk: str) -> bool:
    """True only for external/server/data-backed payload dependencies.

    A reference to GameScene.Game merely to parent a locally-created ChatTab is
    not server data. Those deferred controls remain local-state templates.
    """
    runtime_patterns = (
        r"\bGlobals\.",
        r"\.Binding\b",
        r"\bMapObject\.(?:User|Objects|ObjectsByLocation)\b",
        r"\bSelectedInfo\b",
        r"\bDataDictionary\b",
        r"\bRankInfo\b",
        r"\bInstanceInfo\b",
        r"\bHelpInfo\b",
        r"\bHelpItemInfo\b",
        r"\bMagicInfo\b",
        r"\bClientUserMagic\b",
        r"\bMonsterObject\b",
        r"\bNPCInfo\b",
        r"\bClientObjectData\b",
        r"\bEnqueue\s*\(",
    )
    return any(re.search(pattern, chunk) for pattern in runtime_patterns)


def composite_constructor_summary(source_text: str, type_name: str) -> dict | None:
    if type_name.startswith("DX"):
        return None
    body = class_body(source_text, type_name)
    if not body:
        return None
    ctor = constructor_body(body, type_name)
    if not ctor:
        return None
    method_map = methods(body)
    direct = created_types(ctor)
    immediate_helpers = sorted(calls(ctor, set(method_map), immediate_only=True))
    helper_types = sorted({
        created
        for helper in immediate_helpers
        for chunk in method_map.get(helper, [])
        for created in created_types(chunk)
    })
    combined = ctor + "\n" + "\n".join(
        chunk for helper in immediate_helpers for chunk in method_map.get(helper, [])
    )
    return {
        "sourceClass": type_name,
        "directConstructorCreatedTypes": direct,
        "immediateConstructorHelpers": immediate_helpers,
        "immediateHelperCreatedTypes": helper_types,
        "externalRuntimeData": external_runtime_bound(combined),
        "templateOnly": True,
    }


def constructor_reachability(ctor: str, method_map: dict[str, list[str]]) -> dict[str, int]:
    known = set(method_map)
    initial = sorted(calls(ctor, known, immediate_only=True))
    queue = deque(initial)
    depth = {name: 1 for name in initial}
    visited: set[str] = set()
    while queue:
        helper = queue.popleft()
        if helper in visited:
            continue
        visited.add(helper)
        combined = "\n".join(method_map.get(helper) or [])
        for child in sorted(calls(combined, known, immediate_only=True)):
            child_depth = depth.get(helper, 1) + 1
            if child not in depth or child_depth < depth[child]:
                depth[child] = child_depth
            if child not in visited:
                queue.append(child)
    return depth


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--zircon-root", type=Path, required=True)
    args = parser.parse_args()

    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    rows: list[dict] = []
    source_contracts: dict[str, dict] = {}

    for window in [*(spec.get("windows") or []), *(spec.get("nestedWindows") or [])]:
        source_path = str(window.get("sourcePath") or "")
        source_class = str(window.get("class") or window.get("sourceClass") or "")
        path = args.zircon_root / source_path
        if not source_path or not source_class or not path.exists():
            continue

        source_text = path.read_text(encoding="utf-8-sig")
        body = class_body(source_text, source_class)
        ctor = constructor_body(body, source_class)
        method_map = methods(body)
        if not ctor or not method_map:
            continue

        reach_depth = constructor_reachability(ctor, method_map)
        source_contracts[source_class] = {
            "immediateConstructorHelpers": sorted(name for name, depth in reach_depth.items() if depth == 1),
            "constructorReachableHelpers": sorted(reach_depth),
        }

        for helper in sorted(method_map):
            chunks = method_map.get(helper) or []
            combined = "\n".join(chunks)
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
            reachable = helper in reach_depth
            runtime_data = external_runtime_bound(combined)

            if reachable:
                classification = "runtime-bound" if runtime_data else "deterministic-source"
                status = "materialized" if materialized_names else (
                    "runtime-bound" if runtime_data else "audited-source-only"
                )
            else:
                classification = "deferred-runtime" if runtime_data else "deferred-local-state"
                status = "audited-deferred-runtime" if runtime_data else "audited-deferred-local"

            composites = [summary for type_name in types
                          if (summary := composite_constructor_summary(source_text, type_name)) is not None]

            rows.append({
                "id": window.get("id"),
                "field": window.get("field"),
                "sourceClass": source_class,
                "sourcePath": source_path,
                "helper": helper,
                "constructorReachable": reachable,
                "constructorReachDepth": reach_depth.get(helper),
                "deferredUntilCalled": not reachable,
                "createdTypes": types,
                "namedCreations": named,
                "materializedControlNames": materialized_names,
                "externalRuntimeData": runtime_data,
                "classification": classification,
                "status": status,
                "customCompositeConstructors": composites,
                "sourceBackedOnly": True,
            })

    # BigMap: deterministic constructor helper chain must be materialised, while
    # its final list layout/data remains runtime-neutral until SelectedInfo.
    bigmap = {row["helper"]: row for row in rows if row["sourceClass"] == "BigMapDialog"}
    required_bigmap = {"CreateSidePanel", "CreateRows", "CreateScrollBar"}
    missing = sorted(required_bigmap - set(bigmap))
    if missing:
        raise SystemExit(f"BigMap constructor UI helper inventory incomplete: {missing}")
    for helper in required_bigmap:
        if not bigmap[helper]["constructorReachable"]:
            raise SystemExit(f"BigMap {helper} must be constructor-reachable: {bigmap[helper]}")
    for helper in ("CreateRows", "CreateScrollBar"):
        if bigmap[helper]["classification"] != "deterministic-source":
            raise SystemExit(f"BigMap {helper} misclassified: {bigmap[helper]}")
        if bigmap[helper]["status"] != "materialized":
            raise SystemExit(f"BigMap {helper} deterministic UI is not materialized: {bigmap[helper]}")

    # ChatOptions: AddNewTab is referenced by an event callback, not executed by
    # the constructor. It is a source-derived local-state template and must not
    # be pre-created as fake user chat tabs.
    chat = {row["helper"]: row for row in rows if row["sourceClass"] == "ChatOptionsDialog"}
    if "AddNewTab" not in chat:
        raise SystemExit("ChatOptions.AddNewTab UI helper missing from inventory")
    add_tab = chat["AddNewTab"]
    if add_tab["constructorReachable"]:
        raise SystemExit(f"ChatOptions.AddNewTab incorrectly treated as constructor UI: {add_tab}")
    if add_tab["classification"] != "deferred-local-state" or add_tab["status"] != "audited-deferred-local":
        raise SystemExit(f"ChatOptions.AddNewTab must remain deferred local state: {add_tab}")
    if not {"ChatOptionsPanel", "DXListBoxItem", "DXTabControl", "ChatTab"}.issubset(set(add_tab["createdTypes"])):
        raise SystemExit(f"ChatOptions.AddNewTab source template incomplete: {add_tab['createdTypes']}")
    chat_contract = source_contracts.get("ChatOptionsDialog", {})
    if "AddNewTab" in chat_contract.get("constructorReachableHelpers", []):
        raise SystemExit(f"ChatOptions event callback leaked into immediate constructor graph: {chat_contract}")

    # Help: constructor calls Add(), but Add enumerates Globals.HelpInfoList and
    # only then creates HelpContainer pages. Keep structural Menu/chrome but no
    # fabricated pages/articles/items when that runtime list is absent.
    help_rows = {row["helper"]: row for row in rows if row["sourceClass"] == "HelpDialog"}
    if "Add" not in help_rows:
        raise SystemExit("HelpDialog.Add runtime UI helper missing from inventory")
    help_add = help_rows["Add"]
    if not help_add["constructorReachable"] or help_add["classification"] != "runtime-bound":
        raise SystemExit(f"HelpDialog.Add must remain constructor-reachable runtime data: {help_add}")
    if "HelpContainer" not in help_add["createdTypes"]:
        raise SystemExit(f"HelpDialog.Add no longer creates HelpContainer: {help_add}")

    # Magic: CreateTabs is not constructor UI. It is invoked later when real
    # MagicInfo/user-class/learned-magic state exists. Source school variants may
    # be retained as templates, but no school tab or MagicCell is assumed visible.
    magic_rows = {row["helper"]: row for row in rows if row["sourceClass"] == "MagicDialog"}
    if "CreateTabs" not in magic_rows:
        raise SystemExit("MagicDialog.CreateTabs runtime UI helper missing from inventory")
    magic_tabs = magic_rows["CreateTabs"]
    if magic_tabs["constructorReachable"]:
        raise SystemExit(f"MagicDialog.CreateTabs incorrectly treated as constructor UI: {magic_tabs}")
    if magic_tabs["classification"] != "deferred-runtime" or magic_tabs["status"] != "audited-deferred-runtime":
        raise SystemExit(f"MagicDialog.CreateTabs must remain deferred runtime UI: {magic_tabs}")
    if not {"MagicTab", "MagicCell"}.issubset(set(magic_tabs["createdTypes"])):
        raise SystemExit(f"MagicDialog.CreateTabs source-created controls changed: {magic_tabs['createdTypes']}")

    counts = Counter(row["classification"] for row in rows)
    statuses = Counter(row["status"] for row in rows)
    deferred = [row for row in rows if row["deferredUntilCalled"]]
    report = {
        "passed": True,
        "helperCount": len(rows),
        "deferredHelperCount": len(deferred),
        "classificationCounts": dict(counts),
        "statusCounts": dict(statuses),
        "rows": rows,
        "sourceContracts": source_contracts,
        "knownBigMapHelpers": sorted(required_bigmap),
        "knownBigMapHelpersMaterialized": True,
        "chatOptionsAddNewTabDeferredLocal": True,
        "helpPagesRemainRuntimeBound": True,
        "magicTabsRemainRuntimeBound": True,
        "eventCallbacksExcludedFromConstructorReachability": True,
        "controlsFabricatedByAudit": False,
        "runtimePayloadsInvented": False,
        "sourceBackedOnly": True,
    }
    spec["uiCreationHelperInventory"] = report
    args.spec.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(
        "UI creation helper inventory: PASS -> "
        f"{len(rows)} helpers; deferred={len(deferred)}; "
        f"classifications={dict(counts)}; statuses={dict(statuses)}"
    )


if __name__ == "__main__":
    main()
