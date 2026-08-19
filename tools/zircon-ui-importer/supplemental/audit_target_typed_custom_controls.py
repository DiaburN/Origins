#!/usr/bin/env python3
"""Gate target-typed custom controls created as `identifier = new() { ... }`.

C# target-typed new omits the concrete class name at the creation site. The
base `new DXType` parser and explicit custom-type inventory cannot discover it.
This audit resolves explicit field/local variable declarations to the Client
class inheritance graph, scans constructor bodies with event lambdas removed,
and requires enough manifest controls with matching sourceType to cover every
custom DXControl/DXWindow target-typed creation.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path

CLASS_RE = re.compile(r"\bclass\s+([A-Za-z_][A-Za-z0-9_]*)\s*:\s*([A-Za-z_][A-Za-z0-9_]*)")
TARGET_NEW_RE = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*=\s*new\s*\(\s*\)\s*\{")
DECL_RE = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)\s+([A-Za-z_][A-Za-z0-9_]*)\s*(?=;|=|,)")


def match_brace(text: str, opening: int) -> int:
    depth = 0; quote = None; escaped = False; line = False; block = False; i = opening
    while i < len(text):
        c = text[i]; n = text[i + 1] if i + 1 < len(text) else ""
        if line:
            if c == "\n": line = False
            i += 1; continue
        if block:
            if c == "*" and n == "/": block = False; i += 2; continue
            i += 1; continue
        if quote:
            if escaped: escaped = False
            elif c == "\\": escaped = True
            elif c == quote: quote = None
            i += 1; continue
        if c == "/" and n == "/": line = True; i += 2; continue
        if c == "/" and n == "*": block = True; i += 2; continue
        if c in ('"', "'"): quote = c; i += 1; continue
        if c == "{": depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0: return i
        i += 1
    return len(text) - 1


def class_body(text: str, name: str) -> str:
    m = re.search(rf"\bclass\s+{re.escape(name)}\b[^{{]*\{{", text)
    if not m: return ""
    opening = text.find("{", m.start())
    return text[opening + 1:match_brace(text, opening)]


def constructor_body(body: str, name: str) -> str:
    m = re.search(rf"\b(?:public\s+)?{re.escape(name)}\s*\([^)]*\)\s*(?::\s*[^{{]+)?\{{", body)
    if not m: return ""
    opening = body.find("{", m.start())
    return body[opening + 1:match_brace(body, opening)]


def strip_event_lambdas(chunk: str) -> str:
    chars = list(chunk); pos = 0
    while True:
        plus = chunk.find("+=", pos)
        if plus < 0: break
        arrow = chunk.find("=>", plus + 2)
        if arrow < 0: break
        semi_before = chunk.find(";", plus + 2, arrow)
        if semi_before >= 0:
            pos = semi_before + 1; continue
        cursor = arrow + 2
        while cursor < len(chunk) and chunk[cursor].isspace(): cursor += 1
        if cursor < len(chunk) and chunk[cursor] == "{":
            end = match_brace(chunk, cursor) + 1
            while end < len(chunk) and chunk[end].isspace(): end += 1
            if end < len(chunk) and chunk[end] == ";": end += 1
        else:
            semi = chunk.find(";", cursor); end = len(chunk) if semi < 0 else semi + 1
        for index in range(plus, min(end, len(chars))):
            if chars[index] != "\n": chars[index] = " "
        pos = max(end, plus + 2)
    return "".join(chars)


def build_types(root: Path) -> dict[str, str]:
    bases: dict[str, str] = {}
    for path in (root / "Client").rglob("*.cs"):
        try: text = path.read_text(encoding="utf-8-sig")
        except UnicodeDecodeError: continue
        for name, base in CLASS_RE.findall(text): bases[name] = base
    return bases


def derives(name: str, bases: dict[str, str]) -> bool:
    seen: set[str] = set(); current = name
    while current and current not in seen:
        if current in {"DXControl", "DXWindow"}: return True
        seen.add(current); current = bases.get(current, "")
    return False


def declaration_types(class_chunk: str, ctor: str, bases: dict[str, str]) -> dict[str, str]:
    result: dict[str, str] = {}
    # Explicit class fields and constructor locals are enough to type target-new
    # patterns such as `CompanionBonusStat bonusStat; bonusStat = new() {...}`.
    for text in (class_chunk, ctor):
        for type_name, variable in DECL_RE.findall(text):
            if type_name in bases and derives(type_name, bases):
                result[variable] = type_name
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--zircon-root", type=Path, required=True)
    args = parser.parse_args()

    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    bases = build_types(args.zircon_root)
    rows: list[dict] = []; failures: list[str] = []

    for owner in [*(spec.get("windows") or []), *(spec.get("nestedWindows") or [])]:
        source_path = str(owner.get("sourcePath") or "")
        source_class = str(owner.get("class") or owner.get("sourceClass") or "")
        path = args.zircon_root / source_path
        if not source_path or not source_class or not path.exists(): continue
        source = path.read_text(encoding="utf-8-sig")
        chunk = class_body(source, source_class)
        ctor = constructor_body(chunk, source_class)
        if not ctor: continue
        immediate = strip_event_lambdas(ctor)
        types = declaration_types(chunk, immediate, bases)
        found = Counter()
        unresolved: list[str] = []
        for match in TARGET_NEW_RE.finditer(immediate):
            variable = match.group(1)
            type_name = types.get(variable)
            if type_name:
                found[type_name] += 1
            else:
                # Unresolved target-typed new may be a non-control data object;
                # record for inspection but do not fabricate/control-fail it.
                unresolved.append(variable)
        if not found and not unresolved: continue

        manifest = Counter(
            str(control.get("sourceType") or "")
            for control in owner.get("controls") or []
            if control.get("sourceType")
        )
        for type_name, required in found.items():
            if manifest[type_name] < required:
                failures.append(
                    f"{owner.get('field') or source_class}: target-typed {type_name} requires {required}, "
                    f"manifest sourceType count={manifest[type_name]}"
                )
        rows.append({
            "id": owner.get("id"),
            "field": owner.get("field"),
            "sourceClass": source_class,
            "sourcePath": source_path,
            "resolvedCustomTargetTyped": dict(found),
            "unresolvedTargetTypedVariables": sorted(set(unresolved)),
            "materializedSourceTypeCounts": {name: manifest[name] for name in found},
        })

    if failures:
        raise SystemExit("Target-typed custom control coverage failed:\n- " + "\n- ".join(failures))

    spec["targetTypedCustomControlAudit"] = {
        "passed": True,
        "ownersWithTargetTypedNew": len(rows),
        "resolvedCustomCreations": sum(sum(row["resolvedCustomTargetTyped"].values()) for row in rows),
        "allResolvedCustomControlsMaterialized": True,
        "eventCallbackBodiesExcluded": True,
        "controlsFabricatedByAudit": False,
        "runtimePayloadsInvented": False,
        "rows": rows,
    }
    args.spec.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(
        "Target-typed custom control audit: PASS -> "
        f"{spec['targetTypedCustomControlAudit']['resolvedCustomCreations']} custom constructor creations covered"
    )


if __name__ == "__main__":
    main()
