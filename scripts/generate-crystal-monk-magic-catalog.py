#!/usr/bin/env python3
"""Extract the nine Monk MagicInfo defaults from the pinned Crystal-Monk source."""
from __future__ import annotations

import argparse
import json
import pathlib
import re

MONK_COMMIT = "381e589e3d7ee736cdf0583c8315c0d144ab058f"
MONK_IDS = {
    "JiBenGunFa": 161,
    "LuoHanGunFa": 162,
    "JinGangGunFa": 163,
    "DaMoGunFa": 164,
    "XiangLongGunFa": 165,
    "Taunt": 166,
    "TianLeiZhen": 167,
    "ShiBuYiSha": 168,
    "LuoHanZhen": 169,
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
    for name, expected_id in MONK_IDS.items():
        enum_match = re.search(rf"^\s*{re.escape(name)}\s*=\s*(\d+)\s*,?", common, re.MULTILINE)
        if not enum_match:
            raise RuntimeError(f"Monk spell missing from Common.cs: {name}")
        actual_id = int(enum_match.group(1))
        if actual_id != expected_id:
            raise RuntimeError(f"Monk spell id mismatch for {name}: expected {expected_id}, got {actual_id}")

        pattern = re.compile(
            rf"if\s*\(\s*!MagicExists\(Spell\.{re.escape(name)}\)\s*\)\s*"
            rf"MagicInfoList\.Add\(new MagicInfo\s*\{{(?P<body>.*?)\}}\s*\);",
            re.DOTALL,
        )
        match = pattern.search(envir)
        if not match:
            raise RuntimeError(f"MagicInfo default missing for Monk spell: {name}")

        fields = dict(DEFAULTS)
        body = match.group("body")
        explicit = []
        for key in DEFAULTS:
            value_match = re.search(rf"\b{key}\s*=\s*([^,}}]+)", body)
            if not value_match:
                continue
            value = parse_number(value_match.group(1))
            if value is None:
                raise RuntimeError(f"Unsupported Monk numeric expression {name}.{key}: {value_match.group(1).strip()}")
            fields[key] = value
            explicit.append(key)
        fields["Spell"] = name
        fields["Name"] = name

        spells.append({
            "name": name,
            "spellId": expected_id,
            "category": "Monk",
            "kind": "player",
            "hasDefaultMagicInfo": True,
            "defaultMagicInfo": {
                "fields": fields,
                "explicitFields": sorted(explicit),
                "source": "Server/MirEnvir/Envir.cs::FillMagicInfoList",
            },
        })

    payload = {
        "schemaVersion": 1,
        "source": {
            "repository": "JevLOMCN/Crystal-Monk",
            "commit": MONK_COMMIT,
            "enum": "Common.cs::Spell",
            "defaults": "Server/MirEnvir/Envir.cs::FillMagicInfoList",
        },
        "counts": {"playerSpells": len(spells), "recordsWithDefaults": len(spells)},
        "spells": spells,
    }
    if len(spells) != 9:
        raise RuntimeError(f"Expected 9 Monk spells, generated {len(spells)}")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("Crystal-Monk spell catalog: 9/9 defaults extracted from pinned source")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
