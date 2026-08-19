#!/usr/bin/env python3
"""Project pinned Crystal source MagicInfo defaults into Zircon MagicInfo numerics."""
from __future__ import annotations

import argparse
import json
import pathlib


def dotnet_round(value: float) -> int:
    return int(round(value))


def power_ranges(fields: dict) -> tuple[list[int], list[int]]:
    def bounds(base_key: str, bonus_key: str) -> tuple[int, int]:
        base = int(fields[base_key])
        bonus = int(fields[bonus_key])
        return base, base + (bonus - 1 if bonus > 0 else 0)

    def_min, def_max = bounds("PowerBase", "PowerBonus")
    mp_min, mp_max = bounds("MPowerBase", "MPowerBonus")
    mins, maxs = [], []
    for level in range(4):
        factor = level + 1
        mins.append(dotnet_round((mp_min / 4.0) * factor + def_min))
        maxs.append(dotnet_round((mp_max / 4.0) * factor + def_max))
    return mins, maxs


def zircon_sequence(base: int, level_power: int) -> list[int]:
    return [base + (level * level_power // 3) for level in range(4)]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source_catalog", type=pathlib.Path)
    parser.add_argument("output", type=pathlib.Path)
    args = parser.parse_args()

    catalog = json.loads(args.source_catalog.read_text(encoding="utf-8"))
    rows = []
    for spell in catalog["spells"]:
        fields = spell["defaultMagicInfo"]["fields"]
        mins, maxs = power_ranges(fields)
        min_base, max_base = mins[0], maxs[0]
        min_level_power = mins[3] - mins[0]
        max_level_power = maxs[3] - maxs[0]
        projected_mins = zircon_sequence(min_base, min_level_power)
        projected_maxs = zircon_sequence(max_base, max_level_power)
        power_exact = mins == projected_mins and maxs == projected_maxs
        requirements = []
        if not power_exact:
            requirements.append("handler_power_formula")
        if fields["DelayReduction"] != 0:
            requirements.append("level_scaled_cooldown")
        if fields["MultiplierBase"] != 1.0 or fields["MultiplierBonus"] != 0.0:
            requirements.append("handler_multiplier")
        if fields["Range"] != 9:
            requirements.append("handler_or_targeting_range")

        rows.append({
            "crystalName": spell["name"],
            "sourceSpellId": spell["spellId"],
            "category": spell["category"],
            "kind": spell["kind"],
            "status": "projected_from_pinned_source",
            "directFieldProjection": {
                "Name": spell["name"],
                "Icon": int(fields["Icon"]),
                "BaseCost": int(fields["BaseCost"]),
                "LevelCost": int(fields["LevelCost"]) * 3,
                "NeedLevel1": int(fields["Level1"]),
                "NeedLevel2": int(fields["Level2"]),
                "NeedLevel3": int(fields["Level3"]),
                "Experience1": int(fields["Need1"]),
                "Experience2": int(fields["Need2"]),
                "Experience3": int(fields["Need3"]),
                "Delay": int(fields["DelayBase"]),
                "MinBasePower": min_base,
                "MaxBasePower": max_base,
                "MinLevelPower": min_level_power,
                "MaxLevelPower": max_level_power,
            },
            "proof": {
                "source": catalog["source"],
                "crystalDelayReduction": int(fields["DelayReduction"]),
                "crystalMultiplierBase": fields["MultiplierBase"],
                "crystalMultiplierBonus": fields["MultiplierBonus"],
                "crystalRange": int(fields["Range"]),
                "crystalPowerMinByLevel": mins,
                "crystalPowerMaxByLevel": maxs,
                "zirconProjectedMinByLevel": projected_mins,
                "zirconProjectedMaxByLevel": projected_maxs,
                "powerProjectionExact": power_exact,
            },
            "runtimeRequirements": requirements,
        })

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps({"schemaVersion": 1, "projections": rows}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Pinned-source numeric projection: {len(rows)} spells")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
