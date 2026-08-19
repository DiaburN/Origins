#!/usr/bin/env python3
"""Index concrete Crystal spell references and Zircon MagicObject handlers.

The index is research metadata only. It never changes combat behavior.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
from collections import defaultdict

SPELL_REF = re.compile(r"\bSpell\.([A-Za-z_]\w*)\b")
MAGIC_ATTR = re.compile(r"\[MagicType\(MagicType\.([A-Za-z_]\w*)\)\]")
CLASS_DECL = re.compile(r"\bclass\s+([A-Za-z_]\w*)\b")
METHOD_DECL = re.compile(r"\b(?:public|private|protected|internal)\s+(?:static\s+)?(?:async\s+)?[\w<>,\[\]?\.]+\s+([A-Za-z_]\w*)\s*\(")

CRYSTAL_EXCLUDED = {
    "Shared/Enums.cs",
    "Server/MirEnvir/Envir.cs",
    "Server/MirDatabase/MagicInfo.cs",
}


def nearest_method(lines: list[str], line_index: int) -> str | None:
    for idx in range(line_index, max(-1, line_index - 120), -1):
        match = METHOD_DECL.search(lines[idx])
        if match:
            return match.group(1)
    return None


def crystal_index(root: pathlib.Path) -> dict[str, list[dict]]:
    result: dict[str, list[dict]] = defaultdict(list)
    server_root = root / "Server"
    shared_root = root / "Shared"
    paths = list(server_root.rglob("*.cs")) + list(shared_root.rglob("*.cs"))
    for path in sorted(paths):
        rel = path.relative_to(root).as_posix()
        if rel in CRYSTAL_EXCLUDED:
            continue
        try:
            lines = path.read_text(encoding="utf-8-sig").splitlines()
        except UnicodeDecodeError:
            continue
        for idx, line in enumerate(lines):
            for match in SPELL_REF.finditer(line):
                name = match.group(1)
                result[name].append({
                    "file": rel,
                    "line": idx + 1,
                    "method": nearest_method(lines, idx),
                    "snippet": line.strip()[:300],
                })
    return dict(result)


def zircon_index(root: pathlib.Path) -> dict[str, list[dict]]:
    result: dict[str, list[dict]] = defaultdict(list)
    magic_root = root / "ServerLibrary" / "Models" / "Magics"
    for path in sorted(magic_root.rglob("*.cs")):
        rel = path.relative_to(root).as_posix()
        text = path.read_text(encoding="utf-8-sig")
        lines = text.splitlines()
        for match in MAGIC_ATTR.finditer(text):
            name = match.group(1)
            line_no = text.count("\n", 0, match.start()) + 1
            class_name = None
            after = text[match.end():]
            class_match = CLASS_DECL.search(after)
            if class_match:
                class_name = class_match.group(1)
            methods = []
            for idx, line in enumerate(lines):
                method = METHOD_DECL.search(line)
                if method:
                    methods.append(method.group(1))
            result[name].append({
                "file": rel,
                "attributeLine": line_no,
                "class": class_name,
                "methods": sorted(set(methods)),
            })
    return dict(result)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("crystal_root", type=pathlib.Path)
    parser.add_argument("zircon_root", type=pathlib.Path)
    parser.add_argument("crystal_catalog", type=pathlib.Path)
    parser.add_argument("output", type=pathlib.Path)
    args = parser.parse_args()

    catalog = json.loads(args.crystal_catalog.read_text(encoding="utf-8"))
    cidx = crystal_index(args.crystal_root)
    zidx = zircon_index(args.zircon_root)

    entries = []
    for spell in catalog["spells"]:
        name = spell["name"]
        entries.append({
            "crystal": {
                "name": name,
                "spellId": spell["spellId"],
                "category": spell["category"],
                "kind": spell["kind"],
                "serverCallSites": cidx.get(name, []),
            },
            "zirconExactMagicTypeHandlers": zidx.get(name, []),
        })

    output = {
        "schemaVersion": 1,
        "source": {
            "crystalCommit": catalog["source"]["commit"],
            "zirconCommit": "cbf1aa919083bc13fc3f23f93772a8ab8370632d"
        },
        "policy": {
            "callSiteIndexIsBehaviorVerification": False,
            "purpose": "Locate implementation code before manual/structured behavior comparison"
        },
        "counts": {
            "catalogSpells": len(entries),
            "spellsWithCrystalServerCallSites": sum(1 for e in entries if e["crystal"]["serverCallSites"]),
            "spellsWithExactZirconHandlerName": sum(1 for e in entries if e["zirconExactMagicTypeHandlers"]),
        },
        "entries": entries,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(
        "Magic implementation index: "
        f"{output['counts']['spellsWithCrystalServerCallSites']} Crystal spells with server call sites, "
        f"{output['counts']['spellsWithExactZirconHandlerName']} exact Zircon handlers"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
