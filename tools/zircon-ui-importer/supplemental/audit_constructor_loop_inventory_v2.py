#!/usr/bin/env python3
"""Strict coverage layer for the constructor loop inventory.

Only source loops whose iteration count is mechanically provable are gated:
`for (int i = 0; i < N; i++)` / `<= N`, with no conditional/break/continue/
return in the loop body. Runtime collections and more complex loops remain
explicit review rows rather than guessed materialisations.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import audit_constructor_loop_inventory as base  # noqa: E402

SIMPLE_FOR_RE = re.compile(
    r"^(?:int\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*0\s*;\s*\1\s*(<|<=)\s*(\d+)\s*;\s*\1\s*\+\+$"
)
LOOP_RE = re.compile(r"\b(for|foreach)\s*\(([^)]*)\)\s*\{")
CONDITIONAL_RE = re.compile(r"\b(if|switch|continue|break|return)\b")


def normalise(value: str) -> str:
    return " ".join(str(value).split())


def type_count(window: dict, type_name: str) -> int:
    return sum(
        1 for control in window.get("controls", [])
        if control.get("type") == type_name or control.get("sourceType") == type_name
    )


def loop_chunks(source: str, class_name: str) -> list[dict]:
    body = base.class_body(source, class_name)
    ctor = base.constructor_body(body, class_name)
    rows = []
    for match in LOOP_RE.finditer(ctor):
        opening = ctor.find("{", match.start())
        closing = base.match_brace(ctor, opening)
        rows.append({
            "loopType": match.group(1),
            "header": normalise(match.group(2)),
            "body": ctor[opening + 1:closing],
        })
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--zircon-root", type=Path, required=True)
    args = parser.parse_args()

    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    inventory = spec.get("constructorLoopInventory") or {}
    failures: list[str] = []
    if inventory.get("sourceBackedOnly") is not True:
        failures.append(f"constructor loop inventory missing/not source-backed: {inventory}")

    items = [*(spec.get("windows") or []), *(spec.get("nestedWindows") or [])]
    by_key = {
        (str(item.get("field") or ""), str(item.get("id") or ""), str(item.get("class") or item.get("sourceClass") or "")): item
        for item in items
    }
    source_cache: dict[str, str] = {}
    chunks_cache: dict[tuple[str, str], list[dict]] = {}
    chunk_use: dict[tuple[str, str, str], int] = {}

    strict_rows = []
    review_rows = []
    runtime_rows = []

    for row in inventory.get("rows") or []:
        key = (str(row.get("field") or ""), str(row.get("id") or ""), str(row.get("sourceClass") or ""))
        item = by_key.get(key)
        if item is None:
            # Some nested rows have no field; fall back by id/sourceClass.
            item = next((candidate for candidate in items if str(candidate.get("id") or "") == key[1] and str(candidate.get("class") or candidate.get("sourceClass") or "") == key[2]), None)
        if item is None:
            failures.append(f"loop inventory window unresolved: {row}")
            continue

        if row.get("runtimeCollectionLikely") is True:
            runtime_rows.append({**row, "coverage": "runtime-bound"})
            continue

        simple = SIMPLE_FOR_RE.match(str(row.get("header") or "")) if row.get("loopType") == "for" else None
        if simple is None:
            review_rows.append({**row, "coverage": "non-literal-or-complex-review"})
            continue

        source_path = str(item.get("sourcePath") or "")
        if not source_path:
            failures.append(f"simple loop missing sourcePath: {row}")
            continue
        if source_path not in source_cache:
            source_cache[source_path] = (args.zircon_root / source_path).read_text(encoding="utf-8-sig")
        class_name = str(row.get("sourceClass") or "")
        cache_key = (source_path, class_name)
        if cache_key not in chunks_cache:
            chunks_cache[cache_key] = loop_chunks(source_cache[source_path], class_name)

        candidates = [chunk for chunk in chunks_cache[cache_key] if chunk["loopType"] == row.get("loopType") and chunk["header"] == row.get("header")]
        use_key = (source_path, class_name, str(row.get("header") or ""))
        ordinal = chunk_use.get(use_key, 0)
        chunk_use[use_key] = ordinal + 1
        chunk = candidates[ordinal] if ordinal < len(candidates) else None
        if chunk is None:
            failures.append(f"simple loop source body unresolved: {row}")
            continue
        if CONDITIONAL_RE.search(chunk["body"]):
            review_rows.append({**row, "coverage": "conditional-body-review"})
            continue

        limit = int(simple.group(3))
        expected = limit if simple.group(2) == "<" else limit + 1
        created_types = list(row.get("createdTypes") or [])
        coverage = {type_name: type_count(item, type_name) for type_name in created_types}
        missing = {type_name: count for type_name, count in coverage.items() if count < expected}
        if missing:
            failures.append(
                f"{row.get('field') or row.get('id')} simple loop {row.get('header')} expects >= {expected} "
                f"instances for {created_types}; manifest coverage={coverage}"
            )
        strict_rows.append({
            **row,
            "coverage": "strict-simple-literal",
            "expectedIterations": expected,
            "manifestTypeCoverage": coverage,
            "covered": not missing,
        })

    report = {
        "passed": not failures,
        "version": 2,
        "inventoryLoops": int(inventory.get("loopCount") or 0),
        "strictSimpleLiteralLoops": len(strict_rows),
        "reviewLoops": len(review_rows),
        "runtimeLoops": len(runtime_rows),
        "uncoveredSimpleLiteralLoops": sum(1 for row in strict_rows if not row.get("covered")),
        "strictRows": strict_rows,
        "reviewRows": review_rows,
        "runtimeRows": runtime_rows,
        "sourceBackedOnly": True,
        "controlsFabricatedByAudit": False,
        "runtimePayloadsInvented": False,
        "failures": failures,
    }
    spec["constructorLoopCoverageAudit"] = report
    args.spec.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if failures:
        raise SystemExit("Constructor loop coverage audit failed:\n- " + "\n- ".join(failures))
    print(
        "Constructor loop coverage: PASS -> "
        f"strict={len(strict_rows)}, review={len(review_rows)}, runtime={len(runtime_rows)}, uncoveredSimple=0"
    )


if __name__ == "__main__":
    main()
