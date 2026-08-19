#!/usr/bin/env python3
"""Project Crystal Jev spell numerics into the Zircon MagicInfo schema.

This is a candidate generator, never an automatic overlay writer. It answers
which Crystal values can be represented exactly by existing Zircon fields and
which require handler-specific math.
"""
from __future__ import annotations

import argparse
import json
import pathlib


def dotnet_round(value: float) -> int:
    # Python round() and .NET Math.Round(double) both use midpoint-to-even.
    return int(round(value))


def crystal_power_ranges(row: dict) -> tuple[list[int], list[int]]:
    def bounds(base_key: str, bonus_key: str) -> tuple[int, int]:
        base = int(row[base_key])
        bonus = int(row[bonus_key])
        return base, base + (bonus - 1 if bonus > 0 else 0)

    def_min, def_max = bounds("PowerBase", "PowerBonus")
    mp_min, mp_max = bounds("MPowerBase", "MPowerBonus")

    mins: list[int] = []
    maxs: list[int] = []
    for level in range(4):
        factor = level + 1
        mins.append(dotnet_round((mp_min / 4.0) * factor + def_min))
        maxs.append(dotnet_round((mp_max / 4.0) * factor + def_max))
    return mins, maxs


def zircon_sequence(base: int, level_power: int) -> list[int]:
    return [base + (level * level_power // 3) for level in range(4)]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("crystal_catalog", type=pathlib.Path)
    parser.add_argument("jev_effective", type=pathlib.Path)
    parser.add_argument("output", type=pathlib.Path)
    args = parser.parse_args()

    catalog = json.loads(args.crystal_catalog.read_text(encoding="utf-8"))
    jev = json.loads(args.jev_effective.read_text(encoding="utf-8"))
    source_by_id = {s["spellId"]: s for s in catalog["spells"]}

    rows = []
    exact_power = 0
    special_power = 0
    delay_reduction = 0
    multiplier_override = 0
    non_default_range = 0

    for magic in jev["magics"]:
        spell_id = magic["SpellId"]
        source = source_by_id.get(spell_id)
        if source is None:
            rows.append({
                "spellId": spell_id,
                "spell": magic["Spell"],
                "status": "legacy_unknown_not_in_current_enum",
                "automaticOverlayAllowed": False,
            })
            continue

        mins, maxs = crystal_power_ranges(magic)
        min_base = mins[0]
        max_base = maxs[0]
        min_level_power = mins[3] - mins[0]
        max_level_power = maxs[3] - maxs[0]
        projected_mins = zircon_sequence(min_base, min_level_power)
        projected_maxs = zircon_sequence(max_base, max_level_power)
        power_exact = mins == projected_mins and maxs == projected_maxs

        if power_exact:
            exact_power += 1
        else:
            special_power += 1
        if magic["DelayReduction"] != 0:
            delay_reduction += 1
        if magic["MultiplierBase"] != 1.0 or magic["MultiplierBonus"] != 0.0:
            multiplier_override += 1
        if magic["Range"] != 9:
            non_default_range += 1

        requirements = []
        if not power_exact:
            requirements.append("handler_power_formula")
        if magic["DelayReduction"] != 0:
            requirements.append("level_scaled_cooldown")
        if magic["MultiplierBase"] != 1.0 or magic["MultiplierBonus"] != 0.0:
            requirements.append("handler_multiplier")
        if magic["Range"] != 9:
            requirements.append("handler_or_targeting_range")

        rows.append({
            "spellId": spell_id,
            "spell": magic["Spell"],
            "category": source["category"],
            "kind": source["kind"],
            "automaticOverlayAllowed": False,
            "directFieldProjection": {
                "Name": magic["Name"],
                "Icon": magic["Icon"],
                "BaseCost": magic["BaseCost"],
                "LevelCost": magic["LevelCost"] * 3,
                "NeedLevel1": magic["Level1"],
                "NeedLevel2": magic["Level2"],
                "NeedLevel3": magic["Level3"],
                "Experience1": magic["Need1"],
                "Experience2": magic["Need2"],
                "Experience3": magic["Need3"],
                "Delay": magic["DelayBase"],
                "MinBasePower": min_base,
                "MaxBasePower": max_base,
                "MinLevelPower": min_level_power,
                "MaxLevelPower": max_level_power,
            },
            "proof": {
                "crystalCostFormula": "BaseCost + Level * LevelCost",
                "zirconCostFormula": "BaseCost + Level * LevelCost / 3",
                "levelCostTimesThreePreservesLevels0To3": True,
                "crystalPowerMinByLevel": mins,
                "crystalPowerMaxByLevel": maxs,
                "zirconProjectedMinByLevel": projected_mins,
                "zirconProjectedMaxByLevel": projected_maxs,
                "powerProjectionExact": power_exact,
                "crystalDelayBase": magic["DelayBase"],
                "crystalDelayReduction": magic["DelayReduction"],
                "crystalMultiplierBase": magic["MultiplierBase"],
                "crystalMultiplierBonus": magic["MultiplierBonus"],
                "crystalRange": magic["Range"],
            },
            "runtimeRequirements": requirements,
            "unmappedUntilBehaviorReview": ["Magic", "Class", "School", "Property", "Description"],
        })

    payload = {
        "schemaVersion": 1,
        "policy": {
            "source": "Crystal Jev effective MagicInfo",
            "destination": "Zircon MagicInfo",
            "automaticOverlayWrites": False,
            "levelRange": [0, 1, 2, 3],
            "levelCostProjection": "Zircon.LevelCost = Crystal.LevelCost * 3",
            "requirementsProjection": "Crystal Level1/2/3 -> Zircon NeedLevel1/2/3; Crystal Need1/2/3 -> Zircon Experience1/2/3",
            "schoolClassPropertyRequireBehaviorReview": True,
        },
        "counts": {
            "jevEffectiveSpells": len(jev["magics"]),
            "exactPowerProjection": exact_power,
            "specialPowerFormulaRequired": special_power,
            "levelScaledCooldownRequired": delay_reduction,
            "multiplierHandlerRequired": multiplier_override,
            "nonDefaultRange": non_default_range,
        },
        "projections": rows,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(
        f"Crystal numeric projection: {exact_power} exact power mappings, "
        f"{special_power} special power formulas, {delay_reduction} level-scaled cooldowns"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
