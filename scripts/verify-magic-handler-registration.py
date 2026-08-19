#!/usr/bin/env python3
"""Verify every runtime-ready Crystal spell resolves to a direct Zircon MagicObject handler.

Zircon's SEnvir.CreateMagic() registers only non-abstract classes whose direct
base type is MagicObject and which carry [MagicType(MagicType.X)]. This check
mirrors that rule so a compiling but unregistered spell cannot enter System.db.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re


def norm(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (value or "").lower())


def load_decisions(path: pathlib.Path) -> list[dict]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if "includes" not in payload:
        return payload.get("decisions", [])

    result: list[dict] = []
    seen: set[str] = set()
    for include in payload["includes"]:
        child_path = path.parent / include
        for decision in load_decisions(child_path):
            key = norm(decision.get("crystalSpell", ""))
            if not key:
                raise RuntimeError(f"Decision without crystalSpell in {child_path}")
            if key in seen:
                raise RuntimeError(f"Duplicate Crystal decision: {decision['crystalSpell']}")
            seen.add(key)
            result.append(decision)
    return result


def scan_handlers(root: pathlib.Path) -> dict[str, list[tuple[str, str]]]:
    pattern = re.compile(
        r"\[MagicType\(MagicType\.(?P<magic>[A-Za-z0-9_]+)\)\]"
        r"\s*(?:public\s+)?(?:sealed\s+)?class\s+[A-Za-z0-9_]+\s*:\s*(?P<base>[A-Za-z0-9_]+)",
        re.MULTILINE,
    )

    handlers: dict[str, list[tuple[str, str]]] = {}
    for path in root.rglob("*.cs"):
        text = path.read_text(encoding="utf-8-sig", errors="ignore")
        for match in pattern.finditer(text):
            handlers.setdefault(match.group("magic"), []).append(
                (match.group("base"), str(path.relative_to(root)))
            )
    return handlers


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("zircon_root", type=pathlib.Path)
    parser.add_argument("decisions", type=pathlib.Path)
    args = parser.parse_args()

    decisions = [d for d in load_decisions(args.decisions) if d.get("runtimeReady")]
    handlers = scan_handlers(args.zircon_root / "ServerLibrary" / "Models" / "Magics")

    errors: list[str] = []
    verified: list[str] = []

    for decision in decisions:
        spell = decision["crystalSpell"]
        magic_type = decision.get("zirconMagicType")
        if not magic_type:
            errors.append(f"{spell}: missing zirconMagicType")
            continue

        matches = handlers.get(magic_type, [])
        direct = [item for item in matches if item[0] == "MagicObject"]

        if len(direct) != 1:
            errors.append(
                f"{spell}: MagicType.{magic_type} must have exactly one direct MagicObject handler; "
                f"found direct={direct}, all={matches}"
            )
            continue

        verified.append(f"{spell} -> MagicType.{magic_type} -> {direct[0][1]}")

    if errors:
        print("Magic handler registration FAILED")
        for error in errors:
            print(f"- {error}")
        return 1

    print(f"Magic handler registration OK: {len(verified)} runtime-ready Crystal spells")
    for item in verified:
        print(f"- {item}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
