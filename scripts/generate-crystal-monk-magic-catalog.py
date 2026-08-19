#!/usr/bin/env python3
"""Extract every Crystal-Monk-only playable MagicInfo default from the pinned fork.

The fork contributes 14 secret/variant skills to the five existing classes plus
9 Monk skills: 23 extension spells total. Base Crystal spells remain sourced
from the approved Crystal/Jev pipeline.
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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("crystal_monk_root", type=pathlib.Path)
    parser.add_argument("output", type=pathlib.Path)
    args = parser.parse_args()

    common = (args.crystal_monk_root / "Common.cs").read_text(encoding="utf-8-sig")
    envir = (args.crystal_monk_root / "Server" / "MirEnvir" / "Envir.cs").read_text(encoding="utf-8-sig")

    spells = []
    for category, entries in EXTENSIONS.items():
        for expected_id, name in entries.items():
            enum_match = re.search(rf"^\s*{re.escape(name)}\s*=\s*(\d+)\s*,?", common, re.MULTILINE)
            if not enum_match:
                raise RuntimeError(f"Crystal-Monk extension spell missing from Common.cs: {name}")
            actual_id = int(enum_match.group(1))
            if actual_id != expected_id:
                raise RuntimeError(f"Extension spell id mismatch for {name}: expected {expected_id}, got {actual_id}")

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
        "schemaVersion": 2,
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
    print("Crystal-Monk extension catalog: 23/23 defaults extracted (14 variants + 9 Monk)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
