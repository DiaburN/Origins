#!/usr/bin/env python3
"""Generate a machine-readable player-spell catalog from pinned Suprcode/Crystal.

This parses source declarations only. It does NOT import Crystal's database engine.
The output distinguishes the five playable Crystal classes, custom spell
candidates, and map-event effects. ORIGINS adds Monk and Crystal-Monk variants
from the separately pinned Crystal-Monk source.
"""
from __future__ import annotations

import argparse
import ast
import json
import operator
import pathlib
import re
from typing import Any

CRYSTAL_COMMIT = "0e315fe327192afe52c3d7357ddd1f5b7e26c5b8"

DEFAULTS: dict[str, Any] = {
    "BaseCost": 0,
    "LevelCost": 0,
    "Icon": 0,
    "Level1": 0,
    "Level2": 0,
    "Level3": 0,
    "Need1": 0,
    "Need2": 0,
    "Need3": 0,
    "DelayBase": 1800,
    "DelayReduction": 0,
    "PowerBase": 0,
    "PowerBonus": 0,
    "MPowerBase": 0,
    "MPowerBonus": 0,
    "MultiplierBase": 1.0,
    "MultiplierBonus": 0.0,
    "Range": 9,
}

PLAYER_CLASSES = {"Warrior", "Wizard", "Taoist", "Assassin", "Archer"}
EXPECTED_PLAYER_COUNTS = {
    "Warrior": 17,
    "Wizard": 25,
    "Taoist": 25,
    "Assassin": 17,
    "Archer": 21,
}


def matching_brace(text: str, open_pos: int) -> int:
    depth = 0
    in_string = False
    escaped = False
    line_comment = False
    block_comment = False
    i = open_pos
    while i < len(text):
        ch = text[i]
        nxt = text[i + 1] if i + 1 < len(text) else ""
        if line_comment:
            if ch == "\n":
                line_comment = False
            i += 1
            continue
        if block_comment:
            if ch == "*" and nxt == "/":
                block_comment = False
                i += 2
                continue
            i += 1
            continue
        if in_string:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_string = False
            i += 1
            continue
        if ch == "/" and nxt == "/":
            line_comment = True
            i += 2
            continue
        if ch == "/" and nxt == "*":
            block_comment = True
            i += 2
            continue
        if ch == '"':
            in_string = True
            i += 1
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return i
        i += 1
    raise ValueError("Unbalanced braces")


def method_body(text: str, signature: str) -> str:
    pos = text.find(signature)
    if pos < 0:
        raise ValueError(f"Method not found: {signature}")
    start = text.find("{", pos)
    end = matching_brace(text, start)
    return text[start + 1 : end]


def enum_body(text: str, signature: str) -> str:
    pos = text.find(signature)
    if pos < 0:
        raise ValueError(f"Enum not found: {signature}")
    start = text.find("{", pos)
    end = matching_brace(text, start)
    return text[start + 1 : end]


_ALLOWED_BINOPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
}
_ALLOWED_UNARY = {ast.UAdd: operator.pos, ast.USub: operator.neg}


def safe_number(expr: str) -> int | float | None:
    cleaned = expr.strip()
    cleaned = re.sub(r"(?<=\d)[fFdDmMuUlL]+\b", "", cleaned)
    if not re.fullmatch(r"[0-9+\-*/().\s]+", cleaned):
        return None
    try:
        node = ast.parse(cleaned, mode="eval")
    except SyntaxError:
        return None

    def visit(n: ast.AST) -> float | int:
        if isinstance(n, ast.Expression):
            return visit(n.body)
        if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)):
            return n.value
        if isinstance(n, ast.BinOp) and type(n.op) in _ALLOWED_BINOPS:
            return _ALLOWED_BINOPS[type(n.op)](visit(n.left), visit(n.right))
        if isinstance(n, ast.UnaryOp) and type(n.op) in _ALLOWED_UNARY:
            return _ALLOWED_UNARY[type(n.op)](visit(n.operand))
        raise ValueError("unsupported expression")

    try:
        value = visit(node)
        if isinstance(value, float) and value.is_integer():
            return int(value)
        return value
    except Exception:
        return None


def parse_value(raw: str) -> Any:
    raw = raw.strip()
    if raw.startswith('"') and raw.endswith('"'):
        try:
            return ast.literal_eval(raw)
        except Exception:
            return raw.strip('"')
    if raw in {"true", "false"}:
        return raw == "true"
    if raw.startswith("Spell."):
        return raw.split(".", 1)[1]
    number = safe_number(raw)
    if number is not None:
        return number
    return {"raw": raw}


def split_assignments(initializer: str) -> dict[str, Any]:
    result: dict[str, Any] = {}
    parts: list[str] = []
    current: list[str] = []
    depth = 0
    in_string = False
    escaped = False
    for ch in initializer:
        if in_string:
            current.append(ch)
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
            current.append(ch)
        elif ch in "([{":
            depth += 1
            current.append(ch)
        elif ch in ")]}":
            depth -= 1
            current.append(ch)
        elif ch == "," and depth == 0:
            parts.append("".join(current).strip())
            current = []
        else:
            current.append(ch)
    if current:
        parts.append("".join(current).strip())

    for part in parts:
        if not part or "=" not in part:
            continue
        key, raw = part.split("=", 1)
        result[key.strip()] = parse_value(raw.strip())
    return result


def parse_spell_enum(text: str) -> list[dict[str, Any]]:
    body = enum_body(text, "public enum Spell : byte")
    category = "Uncategorized"
    result: list[dict[str, Any]] = []
    for original in body.splitlines():
        line = original.strip()
        if not line:
            continue
        if line.startswith("//"):
            comment = line[2:].strip()
            normalized = comment.lower().replace(" ", "")
            if "warrior" in normalized:
                category = "Warrior"
            elif "wizard" in normalized or normalized == "wiz":
                category = "Wizard"
            elif "taoist" in normalized or normalized == "tao":
                category = "Taoist"
            elif "assassin" in normalized or normalized in {"sin", "ass"}:
                category = "Assassin"
            elif "archer" in normalized:
                category = "Archer"
            elif "custom" in normalized:
                category = "Custom"
            elif "map" in normalized and ("event" in normalized or "spell" in normalized):
                category = "MapEvent"
            continue
        line = line.split("//", 1)[0].strip().rstrip(",")
        match = re.match(r"^([A-Za-z_]\w*)\s*=\s*(\d+)\s*$", line)
        if not match:
            continue
        name, value = match.group(1), int(match.group(2))
        if name == "None":
            kind = "none"
        elif category in PLAYER_CLASSES:
            kind = "player"
        elif category == "Custom":
            kind = "custom_player_candidate"
        elif category == "MapEvent":
            kind = "map_event"
        else:
            kind = "unclassified"
        result.append({"name": name, "spellId": value, "category": category, "kind": kind})
    return result


def extract_magic_initializers(fill_body: str) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    pattern = re.compile(r"if\s*\(\s*!MagicExists\(Spell\.(\w+)\)\s*\)")
    for match in pattern.finditer(fill_body):
        spell = match.group(1)
        add_pos = fill_body.find("MagicInfoList.Add", match.end())
        if add_pos < 0:
            continue
        next_if = fill_body.find("if (!MagicExists", match.end())
        if next_if >= 0 and add_pos > next_if:
            continue
        new_pos = fill_body.find("new MagicInfo", add_pos)
        if new_pos < 0:
            continue
        brace = fill_body.find("{", new_pos)
        if brace < 0:
            continue
        end = matching_brace(fill_body, brace)
        initializer = fill_body[brace + 1 : end]
        fields = dict(DEFAULTS)
        explicit = split_assignments(initializer)
        fields.update(explicit)
        fields["Spell"] = spell
        result[spell] = {
            "fields": fields,
            "explicitFields": sorted(explicit.keys()),
            "source": "Server/MirEnvir/Envir.cs::FillMagicInfoList"
        }
    return result


def extract_update_overrides(update_body: str) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    case_pattern = re.compile(r"case\s+Spell\.(\w+)\s*:")
    matches = list(case_pattern.finditer(update_body))
    for idx, match in enumerate(matches):
        spell = match.group(1)
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(update_body)
        block = update_body[match.end():end]
        block = block.split("break;", 1)[0]
        overrides: dict[str, Any] = {}
        for assignment in re.finditer(r"MagicInfoList\[i\]\.(\w+)\s*=\s*([^;]+);", block):
            overrides[assignment.group(1)] = parse_value(assignment.group(2))
        if overrides:
            result[spell] = {
                "fields": overrides,
                "source": "Server/MirEnvir/Envir.cs::UpdateMagicInfo"
            }
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("crystal_root", type=pathlib.Path)
    parser.add_argument("output", type=pathlib.Path)
    args = parser.parse_args()

    enum_path = args.crystal_root / "Shared" / "Enums.cs"
    envir_path = args.crystal_root / "Server" / "MirEnvir" / "Envir.cs"
    if not enum_path.is_file() or not envir_path.is_file():
        raise SystemExit("Pinned Crystal source layout not found")

    enums = parse_spell_enum(enum_path.read_text(encoding="utf-8-sig"))
    envir = envir_path.read_text(encoding="utf-8-sig")
    fill = extract_magic_initializers(method_body(envir, "private void FillMagicInfoList()"))
    updates = extract_update_overrides(method_body(envir, "private void UpdateMagicInfo()"))

    spells: list[dict[str, Any]] = []
    for entry in enums:
        spell = dict(entry)
        default_record = fill.get(entry["name"])
        update_record = updates.get(entry["name"])
        if default_record:
            spell["defaultMagicInfo"] = default_record
        if update_record:
            spell["updateOverrides"] = update_record
        spell["hasDefaultMagicInfo"] = default_record is not None
        spells.append(spell)

    player_spells = [s for s in spells if s["kind"] == "player"]
    player_counts = {
        class_name: sum(1 for s in player_spells if s["category"] == class_name)
        for class_name in sorted(PLAYER_CLASSES)
    }
    if player_counts != EXPECTED_PLAYER_COUNTS:
        raise RuntimeError(f"Pinned Crystal playable-class counts changed: {player_counts}")

    missing_defaults = [s["name"] for s in player_spells if not s["hasDefaultMagicInfo"]]
    if missing_defaults != ["FastMove"]:
        raise RuntimeError(
            "Pinned Crystal playable spells without MagicInfo defaults changed; "
            f"expected only FastMove, got {missing_defaults}"
        )

    output = {
        "schemaVersion": 2,
        "source": {
            "repository": "Suprcode/Crystal",
            "commit": CRYSTAL_COMMIT,
            "enum": "Shared/Enums.cs::Spell",
            "defaults": "Server/MirEnvir/Envir.cs::FillMagicInfoList",
            "overrides": "Server/MirEnvir/Envir.cs::UpdateMagicInfo"
        },
        "policy": {
            "databaseEngineImported": False,
            "playableClasses": sorted(PLAYER_CLASSES),
            "archerRequired": True,
            "mapEventsInMagicDialog": False,
            "missingDefaultPolicy": "Preserve source identity; never invent MagicInfo numerics"
        },
        "counts": {
            "enumEntries": len(spells),
            "supportedPlayerSpells": len(player_spells),
            "playerSpellsByClass": player_counts,
            "customPlayerCandidates": sum(1 for s in spells if s["kind"] == "custom_player_candidate"),
            "mapEventSpells": sum(1 for s in spells if s["kind"] == "map_event"),
            "recordsWithDefaults": sum(1 for s in spells if s["hasDefaultMagicInfo"])
        },
        "missingDefaultMagicInfo": missing_defaults,
        "spells": spells
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(
        f"Crystal spell catalog: {len(spells)} enum entries, {len(player_spells)} playable spells, "
        f"{len(fill)} defaults, {len(updates)} update overrides"
    )
    print("Playable classes: " + ", ".join(f"{k}={v}" for k, v in player_counts.items()))
    print("Source stubs without MagicInfo: FastMove")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
