#!/usr/bin/env python3
"""Compare Crystal source defaults with effective Jev MagicInfo values.

Crystal.Database/Jev predates the pinned 2026 source and can retain historical
numeric Spell ids. Spell identity is therefore joined by normalized name; ids
are diagnostics only and are never used as the join key.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re

FIELDS = [
    "Name", "BaseCost", "LevelCost", "Icon", "Level1", "Level2", "Level3",
    "Need1", "Need2", "Need3", "DelayBase", "DelayReduction", "PowerBase",
    "PowerBonus", "MPowerBase", "MPowerBonus", "MultiplierBase",
    "MultiplierBonus", "Range"
]


def norm(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (value or "").lower())


def is_unresolved(value):
    return isinstance(value, dict) and set(value.keys()) == {"raw"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source_catalog", type=pathlib.Path)
    parser.add_argument("jev_export", type=pathlib.Path)
    parser.add_argument("output", type=pathlib.Path)
    args = parser.parse_args()

    source = json.loads(args.source_catalog.read_text(encoding="utf-8"))
    jev = json.loads(args.jev_export.read_text(encoding="utf-8"))
    source_by_name = {norm(s["name"]): s for s in source["spells"]}

    entries = []
    changed = 0
    jev_only = 0
    unresolved_spell_count = 0
    unresolved_field_count = 0
    id_mismatch_count = 0

    for row in jev["magics"]:
        jev_name = row.get("Name") or row.get("Spell") or ""
        src = source_by_name.get(norm(jev_name))
        if src is None:
            entries.append({
                "crystalName": None,
                "sourceSpellId": None,
                "jevName": jev_name,
                "jevSpellId": row.get("SpellId"),
                "status": "legacy_unknown_name_not_in_current_source",
                "differences": {},
                "unresolvedSourceFields": []
            })
            jev_only += 1
            continue

        source_id = src["spellId"]
        jev_id = row.get("SpellId")
        id_mismatch = source_id != jev_id
        if id_mismatch:
            id_mismatch_count += 1

        defaults = ((src.get("defaultMagicInfo") or {}).get("fields") or {}).copy()
        overrides = ((src.get("updateOverrides") or {}).get("fields") or {})
        defaults.update(overrides)
        differences = {}
        unresolved = []

        for field in FIELDS:
            source_value = defaults.get(field)
            jev_value = row.get(field)
            if is_unresolved(source_value):
                unresolved.append({
                    "field": field,
                    "sourceExpression": source_value["raw"],
                    "jevEffective": jev_value
                })
                continue
            if source_value != jev_value:
                differences[field] = {
                    "sourceEffectiveDefault": source_value,
                    "jevEffective": jev_value
                }

        if unresolved:
            unresolved_spell_count += 1
            unresolved_field_count += len(unresolved)

        if differences:
            status = "jev_overrides_source_defaults"
            changed += 1
        elif unresolved:
            status = "matches_known_defaults_with_unresolved_source_fields"
        else:
            status = "jev_matches_source_defaults"

        entries.append({
            "crystalName": src["name"],
            "sourceSpellId": source_id,
            "jevName": jev_name,
            "jevSpellId": jev_id,
            "legacyIdMismatch": id_mismatch,
            "category": src["category"],
            "kind": src["kind"],
            "status": status,
            "differences": differences,
            "unresolvedSourceFields": unresolved
        })

    output = {
        "schemaVersion": 2,
        "sourceCatalogCommit": source["source"]["commit"],
        "jevDatabaseCommit": jev["source"]["commit"],
        "jevDatabaseVersion": jev["reader"]["loadVersion"],
        "policy": {
            "joinKey": "normalized spell name",
            "numericSpellIdUsedAsJoinKey": False,
            "unresolvedSourceExpressionCountsAsOverride": False,
            "legacyUnknownNameAutoImported": False
        },
        "counts": {
            "effectiveJevSpells": len(jev["magics"]),
            "jevOverridesSourceDefaults": changed,
            "jevOnlyUnknownName": jev_only,
            "legacyIdMismatches": id_mismatch_count,
            "spellsWithUnresolvedSourceFields": unresolved_spell_count,
            "unresolvedSourceFieldCount": unresolved_field_count
        },
        "entries": entries
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(
        f"Crystal Jev/default comparison: {len(entries)} effective rows, "
        f"{changed} proven value differences, {jev_only} unknown names, "
        f"{id_mismatch_count} historical id mismatches, "
        f"{unresolved_field_count} unresolved source fields"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
