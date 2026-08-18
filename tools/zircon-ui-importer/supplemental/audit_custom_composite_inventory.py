#!/usr/bin/env python3
"""Inventory non-DX Zircon view composites that the flat DX parser cannot see.

`build_ui_source_spec.object_initializers()` intentionally parses `new DX*`.
Zircon view files also use custom controls derived from DXControl, frequently in
fixed arrays. This audit walks constructor-reachable custom composite types,
records their source/materialisation state, and strictly protects all families
already expanded by supplemental source passes. It never creates UI itself.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict, deque
from pathlib import Path

from audit_ui_creation_helper_inventory import class_body, constructor_body, strip_event_lambdas


CLASS_RE = re.compile(
    r"\b(?:public|private|protected|internal)?\s*(?:sealed\s+|abstract\s+|partial\s+)*"
    r"class\s+([A-Za-z_][A-Za-z0-9_]*)\s*:\s*([A-Za-z_][A-Za-z0-9_]*)"
)
NEW_RE = re.compile(r"\bnew\s+([A-Za-z_][A-Za-z0-9_]*)\b")
ARRAY_RE = re.compile(r"\bnew\s+([A-Za-z_][A-Za-z0-9_]*)\s*\[([^\]]+)\]")

# These are source-fixed families already proven/materialised in this branch.
# `minimumEvidence` is deliberately evidence-count based: older row augmenters
# did not stamp sourceType on row roots, but their sourceGenerated provenance is
# still strict and audited separately.
KNOWN = {
    ("RankingBox", "RankingLine"): 12,
    ("DungeonFinderBox", "DungeonRow"): 9,
    ("FortuneCheckerBox", "FortuneCheckerRow"): 9,
    ("BigMapBox", "BigMapListRow"): 48,
    ("GuildBox", "GuildMemberRow"): 18,
    ("GameStoreBox", "GameStoreItemListControl"): 1,
    ("GameStoreBox", "GameStoreItem"): 10,
    ("GameStoreBox", "GameStoreTopItemsControl"): 1,
    ("GameStoreBox", "GameStoreTopItemControl"): 5,
    ("CommunicationBox", "CommunicationReceivedRow"): 5,
    ("ConsignmentBox", "ConsignmentItemTypeMenu"): 1,
    ("ConsignmentBox", "ConsignmentSearchRow"): 6,
    ("ConsignmentBox", "ConsignmentListRow"): 6,
    ("GroupBox", "GroupLFGRow"): 5,
}


def class_bases(text: str) -> dict[str, str]:
    return {match.group(1): match.group(2) for match in CLASS_RE.finditer(text)}


def derives_dx(name: str, bases: dict[str, str]) -> bool:
    seen: set[str] = set()
    current = name
    while current and current not in seen:
        seen.add(current)
        base = bases.get(current, "")
        if base.startswith("DX"):
            return True
        current = base
    return False


def runtime_markers(chunk: str) -> list[str]:
    patterns = {
        "Binding": r"\.Binding\b",
        "SelectedInfo": r"\bSelectedInfo\b",
        "ClientMarketPlaceInfo": r"\bClientMarketPlaceInfo\b",
        "StoreInfo": r"\bStoreInfo\b",
        "ClientMailInfo": r"\bClientMailInfo\b",
        "ClientLookingForGroup": r"\bClientLookingForGroup\b",
        "ClientGuildMemberInfo": r"\bClientGuildMemberInfo\b",
        "RankInfo": r"\bRankInfo\b",
        "InstanceInfo": r"\bInstanceInfo\b",
        "HelpInfo": r"\bHelpInfo\b",
        "MagicInfo": r"\bMagicInfo\b",
    }
    return [label for label, pattern in patterns.items() if re.search(pattern, chunk)]


def materialisation(window: dict, type_name: str) -> dict:
    controls = window.get("controls") or []
    typed = [str(control.get("name") or "") for control in controls if control.get("sourceType") == type_name]
    provenance = [
        str(control.get("name") or "") for control in controls
        if type_name in str(control.get("sourceGenerated") or "")
    ]
    return {
        "sourceTypeInstances": len(typed),
        "sourceTypeNames": typed,
        "provenanceControls": len(provenance),
        "provenanceSample": provenance[:20],
        "hasEvidence": bool(typed or provenance),
    }


def reachable_custom_types(source_text: str, root_class: str) -> tuple[list[dict], dict[str, str]]:
    bases = class_bases(source_text)
    dx_custom = {name for name in bases if not name.startswith("DX") and derives_dx(name, bases)}
    root_body = class_body(source_text, root_class)
    root_ctor = constructor_body(root_body, root_class)
    if not root_ctor:
        return [], bases

    rows: list[dict] = []
    queue = deque([(root_class, strip_event_lambdas(root_ctor), 0, None)])
    visited: set[tuple[str, int | str | None]] = set()

    while queue:
        owner, ctor, depth, parent_type = queue.popleft()
        key = (owner, depth if depth == 0 else parent_type)
        if key in visited:
            continue
        visited.add(key)
        arrays = defaultdict(list)
        for match in ARRAY_RE.finditer(ctor):
            arrays[match.group(1)].append(" ".join(match.group(2).split()))
        created = [name for name in NEW_RE.findall(ctor) if name in dx_custom]
        for type_name in sorted(set(created)):
            body = class_body(source_text, type_name)
            child_ctor = constructor_body(body, type_name)
            structural = strip_event_lambdas(child_ctor) if child_ctor else ""
            row = {
                "owner": owner,
                "type": type_name,
                "constructorDepth": depth + 1,
                "parentComposite": parent_type,
                "arrayExpressions": arrays.get(type_name, []),
                "newOccurrences": created.count(type_name),
                "constructorRuntimeMarkers": runtime_markers(structural),
                "customComposite": True,
                "sourceBackedOnly": True,
            }
            rows.append(row)
            if child_ctor:
                queue.append((type_name, structural, depth + 1, type_name))
    return rows, bases


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--zircon-root", type=Path, required=True)
    args = parser.parse_args()

    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    report_rows: list[dict] = []
    by_field = {window.get("field"): window for window in spec.get("windows", [])}

    for window in spec.get("windows", []):
        source_path = str(window.get("sourcePath") or "")
        source_class = str(window.get("class") or "")
        path = args.zircon_root / source_path
        if not source_path or not source_class or not path.exists():
            continue
        source_text = path.read_text(encoding="utf-8-sig")
        entries, _ = reachable_custom_types(source_text, source_class)
        for entry in entries:
            evidence = materialisation(window, entry["type"])
            entry.update({
                "id": window.get("id"),
                "field": window.get("field"),
                "sourceClass": source_class,
                "sourcePath": source_path,
                "materialisation": evidence,
                "knownProtectedFamily": (window.get("field"), entry["type"]) in KNOWN,
            })
            report_rows.append(entry)

    failures: list[str] = []
    protected = []
    for (field, type_name), minimum in KNOWN.items():
        window = by_field.get(field)
        if window is None:
            failures.append(f"{field} missing for protected custom composite {type_name}")
            continue
        evidence = materialisation(window, type_name)
        source_entries = [row for row in report_rows if row["field"] == field and row["type"] == type_name]
        if not source_entries:
            failures.append(f"{field}.{type_name} no longer constructor-reachable from current Zircon source")
            continue
        # Exact root-instance counts are available where sourceType is stamped.
        # Older deterministic-row passes use provenance; those have their own
        # exact row-count auditors and only need positive evidence here.
        typed_count = evidence["sourceTypeInstances"]
        provenance_count = evidence["provenanceControls"]
        if typed_count:
            if typed_count < minimum:
                failures.append(f"{field}.{type_name}: {typed_count} sourceType instances < {minimum}")
        elif provenance_count < minimum:
            failures.append(f"{field}.{type_name}: provenance evidence {provenance_count} < {minimum}")
        protected.append({
            "field": field,
            "type": type_name,
            "minimumEvidence": minimum,
            **evidence,
        })

    # Surface every constructor-reachable non-DX composite not yet in the strict
    # matrix. This is an explicit review queue, not permission to invent UI.
    review = [
        {
            "field": row["field"],
            "type": row["type"],
            "owner": row["owner"],
            "constructorDepth": row["constructorDepth"],
            "arrayExpressions": row["arrayExpressions"],
            "runtimeMarkers": row["constructorRuntimeMarkers"],
            "hasMaterialisationEvidence": row["materialisation"]["hasEvidence"],
        }
        for row in report_rows
        if not row["knownProtectedFamily"]
    ]

    report = {
        "passed": not failures,
        "parserBoundary": "base object_initializers parses new DX*; custom DX-derived composites require explicit expansion/audit",
        "constructorReachableCompositeOccurrences": len(report_rows),
        "protectedFamilyCount": len(KNOWN),
        "protectedFamilies": protected,
        "reviewQueue": review,
        "reviewQueueCount": len(review),
        "runtimePayloadsInvented": False,
        "controlsFabricatedByAudit": False,
        "failures": failures,
        "rows": report_rows,
    }
    spec["customCompositeInventory"] = report
    args.spec.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if failures:
        raise SystemExit("Custom composite inventory failed:\n- " + "\n- ".join(failures))
    print(
        "Custom composite inventory: PASS -> "
        f"protected={len(KNOWN)} source-occurrences={len(report_rows)} review={len(review)}"
    )


if __name__ == "__main__":
    main()
