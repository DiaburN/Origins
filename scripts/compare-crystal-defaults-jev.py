#!/usr/bin/env python3
"""Compare Crystal source defaults with effective Jev MagicInfo values."""
from __future__ import annotations

import argparse
import json
import pathlib

FIELDS = [
    "Name", "BaseCost", "LevelCost", "Icon", "Level1", "Level2", "Level3",
    "Need1", "Need2", "Need3", "DelayBase", "DelayReduction", "PowerBase",
    "PowerBonus", "MPowerBase", "MPowerBonus", "MultiplierBase",
    "MultiplierBonus", "Range"
]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source_catalog", type=pathlib.Path)
    parser.add_argument("jev_export", type=pathlib.Path)
    parser.add_argument("output", type=pathlib.Path)
    args = parser.parse_args()

    source = json.loads(args.source_catalog.read_text(encoding="utf-8"))
    jev = json.loads(args.jev_export.read_text(encoding="utf-8"))
    source_by_id = {s["spellId"]: s for s in source["spells"]}

    entries = []
    changed = 0
    jev_only = 0
    for row in jev["magics"]:
        spell_id = row["SpellId"]
        src = source_by_id.get(spell_id)
        if src is None:
            entries.append({"spellId": spell_id, "spell": row["Spell"], "status": "jev_only_unknown_enum", "differences": {}})
            jev_only += 1
            continue

        defaults = ((src.get("defaultMagicInfo") or {}).get("fields") or {}).copy()
        overrides = ((src.get("updateOverrides") or {}).get("fields") or {})
        defaults.update(overrides)
        differences = {}
        for field in FIELDS:
            source_field = "Name" if field == "Name" else field
            source_value = defaults.get(source_field)
            jev_value = row.get(field)
            if source_value != jev_value:
                differences[field] = {"sourceEffectiveDefault": source_value, "jevEffective": jev_value}

        status = "jev_matches_source_defaults" if not differences else "jev_overrides_source_defaults"
        if differences:
            changed += 1
        entries.append({
            "spellId": spell_id,
            "spell": row["Spell"],
            "category": src["category"],
            "kind": src["kind"],
            "status": status,
            "differences": differences
        })

    output = {
        "schemaVersion": 1,
        "sourceCatalogCommit": source["source"]["commit"],
        "jevDatabaseCommit": jev["source"]["commit"],
        "jevDatabaseVersion": jev["reader"]["loadVersion"],
        "counts": {
            "effectiveJevSpells": len(jev["magics"]),
            "jevOverridesSourceDefaults": changed,
            "jevOnlyUnknownEnum": jev_only
        },
        "entries": entries
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Crystal Jev/default comparison: {len(entries)} spells, {changed} with effective value differences, {jev_only} unknown")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
