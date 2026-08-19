#!/usr/bin/env python3
"""Verify every runtime-ready Crystal spell resolves to a registered Zircon MagicObject handler.

ORIGINS extends Zircon registration to accept every non-abstract class assignable
to MagicObject that carries [MagicType(MagicType.X)]. This check mirrors that
rule statically, including handler classes that inherit through shared abstract
bases such as CrystalArcherMagic and CrystalArcherProjectile.
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
        return payload.get("decisions", payload.get("spells", []))

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


CLASS_RE = re.compile(
    r"\b(?:(?:public|internal|private|protected)\s+)?"
    r"(?:(?:abstract|sealed|partial)\s+)*"
    r"class\s+(?P<name>[A-Za-z0-9_]+)\s*:\s*(?P<base>[A-Za-z0-9_]+)",
    re.MULTILINE,
)

HANDLER_RE = re.compile(
    r"\[MagicType\(MagicType\.(?P<magic>[A-Za-z0-9_]+)\)\]"
    r"\s*(?:(?:public|internal|private|protected)\s+)?"
    r"(?:(?:sealed|partial)\s+)*"
    r"class\s+(?P<name>[A-Za-z0-9_]+)\s*:\s*(?P<base>[A-Za-z0-9_]+)",
    re.MULTILINE,
)


def scan_handlers(root: pathlib.Path) -> tuple[dict[str, list[tuple[str, str, str]]], dict[str, str]]:
    handlers: dict[str, list[tuple[str, str, str]]] = {}
    bases: dict[str, str] = {}

    for path in root.rglob("*.cs"):
        text = path.read_text(encoding="utf-8-sig", errors="ignore")
        relative = str(path.relative_to(root))

        for match in CLASS_RE.finditer(text):
            bases.setdefault(match.group("name"), match.group("base"))

        for match in HANDLER_RE.finditer(text):
            handlers.setdefault(match.group("magic"), []).append(
                (match.group("name"), match.group("base"), relative)
            )

    return handlers, bases


def derives_from_magic_object(class_name: str, direct_base: str, bases: dict[str, str]) -> bool:
    if direct_base == "MagicObject":
        return True

    current = direct_base
    seen: set[str] = {class_name}
    while current and current not in seen:
        if current == "MagicObject":
            return True
        seen.add(current)
        current = bases.get(current)

    return False


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("zircon_root", type=pathlib.Path)
    parser.add_argument("decisions", type=pathlib.Path)
    args = parser.parse_args()

    decisions = [d for d in load_decisions(args.decisions) if d.get("runtimeReady")]
    handlers, bases = scan_handlers(args.zircon_root / "ServerLibrary" / "Models" / "Magics")

    errors: list[str] = []
    verified: list[str] = []

    for decision in decisions:
        spell = decision["crystalSpell"]
        magic_type = decision.get("zirconMagicType")
        if not magic_type:
            errors.append(f"{spell}: missing zirconMagicType")
            continue

        matches = handlers.get(magic_type, [])
        registered = [
            item for item in matches
            if derives_from_magic_object(item[0], item[1], bases)
        ]

        if len(registered) != 1:
            errors.append(
                f"{spell}: MagicType.{magic_type} must have exactly one registered MagicObject-derived handler; "
                f"found registered={registered}, all={matches}"
            )
            continue

        verified.append(f"{spell} -> MagicType.{magic_type} -> {registered[0][2]}")

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
