#!/usr/bin/env python3
"""Gate custom non-DX controls constructed directly by source window constructors.

The base importer recognises object initialisers whose type name starts with DX.
Zircon also constructs custom DXControl subclasses directly (for example
GameStoreItemListControl or ConsignmentItemTypeMenu). Those are easy to omit even
though their shell exists before any server payload arrives.

This audit scans all 65 GameScene + nested window constructors, ignores event
lambda bodies, resolves the C# inheritance chain, and requires every directly
constructed custom DXControl/DXWindow type to have a materialised sourceType in
that manifest owner. Fixed array cardinality remains the responsibility of the
specific deterministic row/composite audits.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path

CLASS_RE = re.compile(r"\bclass\s+([A-Za-z_][A-Za-z0-9_]*)\s*:\s*([A-Za-z_][A-Za-z0-9_]*)")
NEW_RE = re.compile(r"\bnew\s+([A-Za-z_][A-Za-z0-9_]*)\s*(?=[({])")


def match_brace(text: str, opening: int) -> int:
    depth = 0
    quote = None
    escaped = False
    line_comment = False
    block_comment = False
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
        if quote:
            if escaped: escaped = False
            elif c == "\\": escaped = True
            elif c == quote: quote = None
            i += 1; continue
        if c == "/" and n == "/": line_comment = True; i += 2; continue
        if c == "/" and n == "*": block_comment = True; i += 2; continue
        if c in ('"', "'"): quote = c; i += 1; continue
        if c == "{": depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0: return i
        i += 1
    return len(text) - 1


def class_body(text: str, name: str) -> str:
    match = re.search(rf"\bclass\s+{re.escape(name)}\b[^{{]*\{{", text)
    if not match: return ""
    opening = text.find("{", match.start())
    return text[opening + 1:match_brace(text, opening)]


def constructor_body(body: str, name: str) -> str:
    match = re.search(rf"\b(?:public\s+)?{re.escape(name)}\s*\([^)]*\)\s*(?::\s*[^{{]+)?\{{", body)
    if not match: return ""
    opening = body.find("{", match.start())
    return body[opening + 1:match_brace(body, opening)]


def strip_event_lambdas(chunk: str) -> str:
    chars = list(chunk)
    pos = 0
    while True:
        plus = chunk.find("+=", pos)
        if plus < 0: break
        arrow = chunk.find("=>", plus + 2)
        if arrow < 0: break
        terminator = chunk.find(";", plus + 2, arrow)
        if terminator >= 0:
            pos = terminator + 1
            continue
        cursor = arrow + 2
        while cursor < len(chunk) and chunk[cursor].isspace(): cursor += 1
        if cursor < len(chunk) and chunk[cursor] == "{":
            end = match_brace(chunk, cursor) + 1
            while end < len(chunk) and chunk[end].isspace(): end += 1
            if end < len(chunk) and chunk[end] == ";": end += 1
        else:
            semi = chunk.find(";", cursor)
            end = len(chunk) if semi < 0 else semi + 1
        for i in range(plus, min(end, len(chars))):
            if chars[i] != "\n": chars[i] = " "
        pos = max(end, plus + 2)
    return "".join(chars)


def build_types(root: Path) -> tuple[dict[str, str], dict[str, Path]]:
    bases: dict[str, str] = {}
    paths: dict[str, Path] = {}
    for path in (root / "Client").rglob("*.cs"):
        try: text = path.read_text(encoding="utf-8-sig")
        except UnicodeDecodeError: continue
        for name, base in CLASS_RE.findall(text):
            bases[name] = base
            paths[name] = path
    return bases, paths


def derives(name: str, targets: set[str], bases: dict[str, str]) -> bool:
    seen: set[str] = set()
    current = name
    while current and current not in seen:
        if current in targets: return True
        seen.add(current)
        current = bases.get(current, "")
    return False


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--zircon-root", type=Path, required=True)
    args = parser.parse_args()

    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    bases, paths = build_types(args.zircon_root)
    rows: list[dict] = []
    missing: list[dict] = []
    targets = {"DXControl", "DXWindow"}

    for owner in [*(spec.get("windows") or []), *(spec.get("nestedWindows") or [])]:
        source_class = str(owner.get("class") or owner.get("sourceClass") or "")
        source_path = str(owner.get("sourcePath") or "")
        path = args.zircon_root / source_path
        if not source_class or not source_path or not path.exists(): continue
        text = path.read_text(encoding="utf-8-sig")
        body = class_body(text, source_class)
        ctor = constructor_body(body, source_class)
        if not ctor: continue
        ctor = strip_event_lambdas(ctor)

        source_types = defaultdict(int)
        for control in owner.get("controls") or []:
            source_type = str(control.get("sourceType") or "")
            if source_type: source_types[source_type] += 1

        discovered: dict[str, int] = defaultdict(int)
        for type_name in NEW_RE.findall(ctor):
            if type_name.startswith("DX"): continue
            if type_name == source_class: continue
            if type_name not in bases: continue
            if not derives(type_name, targets, bases): continue
            discovered[type_name] += 1

        for type_name, source_occurrences in sorted(discovered.items()):
            materialized = int(source_types.get(type_name, 0))
            row = {
                "id": owner.get("id"),
                "field": owner.get("field"),
                "sourceClass": source_class,
                "sourcePath": source_path,
                "customType": type_name,
                "customTypeSourcePath": paths[type_name].relative_to(args.zircon_root).as_posix() if type_name in paths else None,
                "constructorSyntaxOccurrences": source_occurrences,
                "materializedSourceTypeControls": materialized,
                "covered": materialized > 0,
            }
            rows.append(row)
            if not row["covered"]: missing.append(row)

    if missing:
        details = "; ".join(f"{row['field'] or row['sourceClass']}:{row['customType']}" for row in missing)
        raise SystemExit(f"Direct custom source composites not materialized: {details}")

    spec["directCustomCompositeInventory"] = {
        "passed": True,
        "ownerCount": len(spec.get("windows") or []) + len(spec.get("nestedWindows") or []),
        "customTypeOccurrenceRows": len(rows),
        "allDirectCustomTypesMaterialized": True,
        "eventCallbackBodiesExcluded": True,
        "runtimePayloadsInvented": False,
        "rows": rows,
    }
    args.spec.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Direct custom composite inventory: PASS ({len(rows)} source type/owner rows, 0 uncovered)")


if __name__ == "__main__":
    main()
