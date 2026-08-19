#!/usr/bin/env python3
"""Extract every Crystal-Monk-only playable MagicInfo default from the pinned fork.

The fork contributes 14 secret/variant skills to the five existing classes plus
9 Monk skills: 23 extension spells total. Base Crystal spells remain sourced
from the approved Crystal/Jev pipeline.

Spell IDs are validated only against Common.cs::Spell. Common.cs contains other
enums with repeated member names (for example PoisonType.DelayedExplosion2 =
1024), so searching the whole file by member name can resolve the wrong enum.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re

EXTENSION_COMMIT = "381e589e3d7ee736cdf0583c8315c0d144ab058f"
EXTENSIONS = {
    "Warrior": {18:"CounterAttack1",19:"ProtectionField1",20:"EntrapSwordSecret",21:"ImmortalSkin1"},
    "Wizard": {56:"GreateFireBallSecret",57:"Bisul",58:"StormEscape1"},
    "Taoist": {87:"HealingCircle2",88:"Healing2"},
    "Assassin": {108:"FlashDash2",109:"MoonMist2"},
    "Archer": {142:"ElementalBarrier1",143:"DelayedExplosion2",144:"NapalmShot2"},
    "Monk": {161:"JiBenGunFa",162:"LuoHanGunFa",163:"JinGangGunFa",164:"DaMoGunFa",165:"XiangLongGunFa",166:"Taunt",167:"TianLeiZhen",168:"ShiBuYiSha",169:"LuoHanZhen"},
}
DEFAULTS = {
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


def parse_number(raw: str):
    raw = raw.strip()
    raw = re.sub(r"(?<=\d)[fFdDmMuUlL]+$", "", raw)
    try:
        return float(raw) if "." in raw else int(raw)
    except ValueError:
        return None


def find_matching_brace(text: str, open_pos: int) -> int:
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

    raise RuntimeError("Unbalanced braces while reading Common.cs::Spell")


def extract_spell_enum(common: str) -> str:
    match = re.search(r"\bpublic\s+enum\s+Spell\s*:\s*byte\b", common)
    if not match:
        raise RuntimeError("Common.cs::Spell enum not found")
    start = common.find("{", match.end())
    if start < 0:
        raise RuntimeError("Common.cs::Spell opening brace not found")
    end = find_matching_brace(common, start)
    return common[start + 1:end]


def parse_spell_ids(spell_enum: str) -> dict[str, int]:
    result: dict[str, int] = {}
    for match in re.finditer(
        r"^\s*([A-Za-z_]\w*)\s*=\s*(\d+)\s*,?",
        spell_enum,
        re.MULTILINE,
    ):
        name = match.group(1)
        spell_id = int(match.group(2))
        if name in result:
            raise RuntimeError(f"Duplicate member in Common.cs::Spell: {name}")
        result[name] = spell_id
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("crystal_monk_root", type=pathlib.Path)
    parser.add_argument("output", type=pathlib.Path)
    args = parser.parse_args()

    common = (args.crystal_monk_root / "Common.cs").read_text(encoding="utf-8-sig")
    envir = (args.crystal_monk_root / "Server" / "MirEnvir" / "Envir.cs").read_text(encoding="utf-8-sig")
    spell_ids = parse_spell_ids(extract_spell_enum(common))

    spells = []
    for category, entries in EXTENSIONS.items():
        for expected_id, name in entries.items():
            actual_id = spell_ids.get(name)
            if actual_id is None:
                raise RuntimeError(f"Crystal-Monk extension spell missing from Common.cs::Spell: {name}")
            if actual_id != expected_id:
                raise RuntimeError(f"Extension Spell id mismatch for {name}: expected {expected_id}, got {actual_id}")

            pattern = re.compile(
                rf"if\s*\(\s*!MagicExists\(Spell\.{re.escape(name)}\)\s*\)\s*"
                rf"MagicInfoList\.Add\(new MagicInfo\s*\{{(?P<body>.*?)\}}\s*\);",
                re.DOTALL,
            )
            match = pattern.search(envir)
            if not match:
                raise RuntimeError(f"MagicInfo default missing for Crystal-Monk extension spell: {name}")

            fields = dict(DEFAULTS)
            body = match.group("body")
            explicit = []
            source_display_match = re.search(r'\bName\s*=\s*Tr\(\"([^\"]+)\"\)', body)
            source_display_name = source_display_match.group(1) if source_display_match else name
            for key in DEFAULTS:
                value_match = re.search(rf"\b{key}\s*=\s*([^,}}]+)", body)
                if not value_match:
                    continue
                value = parse_number(value_match.group(1))
                if value is None:
                    raise RuntimeError(f"Unsupported extension numeric expression {name}.{key}: {value_match.group(1).strip()}")
                fields[key] = value
                explicit.append(key)
            fields["Spell"] = name
            fields["Name"] = name

            spells.append({
                "name": name,
                "sourceDisplayName": source_display_name,
                "spellId": expected_id,
                "sourceSpellId": actual_id,
                "category": category,
                "kind": "player",
                "hasDefaultMagicInfo": True,
                "defaultMagicInfo": {
                    "fields": fields,
                    "explicitFields": sorted(explicit),
                    "source": "Server/MirEnvir/Envir.cs::FillMagicInfoList",
                },
            })

    expected_total = sum(len(v) for v in EXTENSIONS.values())
    if expected_total != 23 or len(spells) != 23:
        raise RuntimeError(f"Expected 23 Crystal-Monk extension spells, generated {len(spells)}")

    payload = {
        "schemaVersion": 3,
        "source": {
            "repository": "JevLOMCN/Crystal-Monk",
            "commit": EXTENSION_COMMIT,
            "enum": "Common.cs::Spell",
            "defaults": "Server/MirEnvir/Envir.cs::FillMagicInfoList",
        },
        "counts": {
            "extensionSpells": len(spells),
            "nonMonkSecretOrVariantSpells": 14,
            "monkSpells": 9,
            "recordsWithDefaults": len(spells),
        },
        "spells": spells,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("Crystal-Monk extension catalog: 23/23 defaults extracted from Common.cs::Spell (14 variants + 9 Monk)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
