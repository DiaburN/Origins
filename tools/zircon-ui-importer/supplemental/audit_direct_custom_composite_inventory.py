#!/usr/bin/env python3
"""Gate custom non-DX controls constructed directly by source window constructors.

Most direct custom DXControl/DXWindow subclasses remain materialised with their
sourceType. A small, explicitly source-backed set is intentionally flattened to
base DX controls by deterministic expanders so the full child tree can be
rendered without inventing runtime payloads. Those flattened cases are accepted
only when their exact owner/type/count contracts are already proven in the
manifest. Any new direct custom type remains a hard failure.
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


def generated_count(owner: dict, prefix: str) -> int:
    return sum(1 for c in owner.get("controls", []) if str(c.get("sourceGenerated") or "").startswith(prefix))


def named_roots(owner: dict, pattern: str) -> int:
    regex = re.compile(pattern)
    return sum(1 for c in owner.get("controls", []) if regex.fullmatch(str(c.get("name") or "")))


def flattened_contract(spec: dict, owner: dict, type_name: str, source_occurrences: int) -> dict | None:
    """Return exact evidence for the only approved flattened custom composites."""
    field = str(owner.get("field") or "")

    if (field, type_name) == ("AutoPotionBox", "AutoPotionRow"):
        contract = owner.get("autoPotionSourceLoop") or {}
        ok = (
            source_occurrences == 1
            and contract.get("rowCount") == 8
            and contract.get("runtimeItemLinksInvented") is False
            and named_roots(owner, r"AutoPotionRow\d{2}") == 8
            and generated_count(owner, "AutoPotionDialog Rows loop + AutoPotionRow constructor") == 80
        )
        if ok:
            return {"kind":"flattened-deterministic-tree","rows":8,"controls":80,"runtimePayloadsInvented":False}
        return None

    source_audit = spec.get("deterministicSourceRowAudit") or {}
    if source_audit.get("passed") is not True or source_audit.get("runtimePayloadsInvented") is not False:
        return None

    if (field, type_name) == ("RankingBox", "RankingLine"):
        contract = owner.get("deterministicRankingRows") or {}
        roots = named_roots(owner, r"Ranking(?:SearchLineSource|LineSource\d{2})")
        ok = (
            source_occurrences == 2
            and source_audit.get("rankingRows") == 12
            and contract.get("searchRows") == 1
            and contract.get("rankingRows") == 11
            and contract.get("runtimeRankInfoInvented") is False
            and roots == 12
            and generated_count(owner, "deterministic-rows:Ranking") == 72
        )
        if ok:
            return {"kind":"flattened-deterministic-tree","rows":12,"controls":72,"runtimePayloadsInvented":False}
        return None

    if (field, type_name) == ("DungeonFinderBox", "DungeonRow"):
        contract = owner.get("deterministicDungeonRows") or {}
        ok = (
            source_occurrences == 1
            and source_audit.get("dungeonRows") == 9
            and contract.get("rowCount") == 9
            and contract.get("runtimeInstanceInfoInvented") is False
            and named_roots(owner, r"DungeonRowSource\d{2}") == 9
            and generated_count(owner, "deterministic-rows:Dungeon") == 54
        )
        if ok:
            return {"kind":"flattened-deterministic-tree","rows":9,"controls":54,"runtimePayloadsInvented":False}
        return None

    if (field, type_name) == ("FortuneCheckerBox", "FortuneCheckerRow"):
        contract = owner.get("deterministicFortuneRows") or {}
        ok = (
            source_occurrences == 1
            and source_audit.get("fortuneRows") == 9
            and contract.get("rowCount") == 9
            and contract.get("runtimeItemInfoInvented") is False
            and contract.get("runtimeFortuneInvented") is False
            and named_roots(owner, r"FortuneRowSource\d{2}") == 9
            and generated_count(owner, "deterministic-rows:Fortune") == 90
        )
        if ok:
            return {"kind":"flattened-deterministic-tree","rows":9,"controls":90,"runtimePayloadsInvented":False}
        return None

    return None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--zircon-root", type=Path, required=True)
    args = parser.parse_args()

    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    bases, paths = build_types(args.zircon_root)
    rows: list[dict] = []
    missing: list[dict] = []
    flattened = 0
    targets = {"DXControl", "DXWindow"}

    for owner in [*(spec.get("windows") or []), *(spec.get("nestedWindows") or [])]:
        source_class = str(owner.get("sourceClass") or owner.get("class") or "")
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
            evidence = flattened_contract(spec, owner, type_name, source_occurrences) if materialized == 0 else None
            covered = materialized > 0 or evidence is not None
            if evidence is not None: flattened += 1
            row = {
                "id": owner.get("id"),
                "field": owner.get("field"),
                "sourceClass": source_class,
                "sourcePath": source_path,
                "customType": type_name,
                "customTypeSourcePath": paths[type_name].relative_to(args.zircon_root).as_posix() if type_name in paths else None,
                "constructorSyntaxOccurrences": source_occurrences,
                "materializedSourceTypeControls": materialized,
                "flattenedTreeEvidence": evidence,
                "covered": covered,
            }
            rows.append(row)
            if not covered: missing.append(row)

    if missing:
        details = "; ".join(f"{row['field'] or row['sourceClass']}:{row['customType']}" for row in missing)
        raise SystemExit(f"Direct custom source composites not materialized: {details}")

    spec["directCustomCompositeInventory"] = {
        "passed": True,
        "ownerCount": len(spec.get("windows") or []) + len(spec.get("nestedWindows") or []),
        "customTypeOccurrenceRows": len(rows),
        "allDirectCustomTypesMaterialized": True,
        "flattenedDeterministicContracts": flattened,
        "approvedFlattenedOwnerTypes": [
            "AutoPotionBox:AutoPotionRow",
            "RankingBox:RankingLine",
            "DungeonFinderBox:DungeonRow",
            "FortuneCheckerBox:FortuneCheckerRow",
        ],
        "exactFlattenedCountsRequired": True,
        "eventCallbackBodiesExcluded": True,
        "runtimePayloadsInvented": False,
        "rows": rows,
    }
    args.spec.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Direct custom composite inventory: PASS ({len(rows)} source type/owner rows, {flattened} exact flattened trees, 0 uncovered)")


if __name__ == "__main__":
    main()
