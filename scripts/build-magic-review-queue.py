#!/usr/bin/env python3
"""Merge generated magic research into one conservative review queue."""
from __future__ import annotations

import argparse
import json
import pathlib
import re


def load(path: pathlib.Path):
    return json.loads(path.read_text(encoding="utf-8"))


def norm(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (value or "").lower())


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source_catalog", type=pathlib.Path)
    parser.add_argument("jev_effective", type=pathlib.Path)
    parser.add_argument("jev_differences", type=pathlib.Path)
    parser.add_argument("zircon_comparison", type=pathlib.Path)
    parser.add_argument("implementation_index", type=pathlib.Path)
    parser.add_argument("output", type=pathlib.Path)
    args = parser.parse_args()

    source = load(args.source_catalog)
    jev = load(args.jev_effective)
    diffs = load(args.jev_differences)
    comparison = load(args.zircon_comparison)
    implementations = load(args.implementation_index)

    jev_by_name = {norm(m.get("Name") or m.get("Spell") or ""): m for m in jev["magics"]}
    diff_by_name = {
        norm(e.get("crystalName") or e.get("jevName") or ""): e
        for e in diffs["entries"]
        if e.get("crystalName") or e.get("jevName")
    }
    cmp_by_name = {norm(e["crystal"]["name"]): e for e in comparison["entries"]}
    impl_by_name = {norm(e["crystal"]["name"]): e for e in implementations["entries"]}

    queue = []
    for spell in source["spells"]:
        spell_name = spell["name"]
        spell_key = norm(spell_name)
        source_spell_id = spell["spellId"]
        kind = spell["kind"]
        cmp = cmp_by_name.get(spell_key, {})
        impl = impl_by_name.get(spell_key, {})
        jev_row = jev_by_name.get(spell_key)
        diff = diff_by_name.get(spell_key)

        if kind == "map_event":
            review_state = "excluded_map_event"
            priority = 90
        elif kind == "deferred_class":
            review_state = "deferred_archer"
            priority = 80
        elif kind == "none":
            review_state = "excluded_none"
            priority = 99
        elif cmp.get("status") == "name_match_needs_behavior_check":
            review_state = "ready_exact_name_behavior_review"
            priority = 10
        elif kind == "custom_player_candidate":
            review_state = "ready_custom_behavior_review"
            priority = 30
        else:
            review_state = "ready_semantic_behavior_review"
            priority = 20

        crystal_calls = ((impl.get("crystal") or {}).get("serverCallSites") or [])
        zircon_handlers = impl.get("zirconExactMagicTypeHandlers") or []
        jev_spell_id = jev_row.get("SpellId") if jev_row else None

        queue.append({
            "priority": priority,
            "reviewState": review_state,
            "verified": False,
            "decision": None,
            "crystal": {
                "name": spell_name,
                "sourceSpellId": source_spell_id,
                "category": spell["category"],
                "kind": kind,
                "sourceDefault": (spell.get("defaultMagicInfo") or {}).get("fields"),
                "updateOverrides": (spell.get("updateOverrides") or {}).get("fields"),
                "jevEffective": jev_row,
                "jevSpellId": jev_spell_id,
                "legacyIdMismatch": jev_spell_id is not None and jev_spell_id != source_spell_id,
                "jevDifference": diff,
                "serverCallSites": crystal_calls
            },
            "zircon": {
                "nameComparisonStatus": cmp.get("status"),
                "nameMatches": cmp.get("zirconNameMatches", []),
                "exactMagicTypeHandlers": zircon_handlers
            },
            "requiredReview": [
                "Crystal cast/target/cost/cooldown path",
                "Crystal damage/buff/debuff/summon/teleport behavior",
                "Zircon MagicObject MagicCast/MagicComplete/passive behavior",
                "numeric field mapping Crystal -> Zircon",
                "client animation/effect mapping kept separate from server damage timing"
            ] if priority < 80 else []
        })

    queue.sort(key=lambda e: (e["priority"], e["crystal"]["category"], e["crystal"]["sourceSpellId"]))

    counts = {}
    for entry in queue:
        counts[entry["reviewState"]] = counts.get(entry["reviewState"], 0) + 1

    payload = {
        "schemaVersion": 2,
        "policy": {
            "joinKeyForJev": "normalized spell name",
            "numericSpellIdUsedAsJevJoinKey": False,
            "automaticVerification": False,
            "automaticOverlayWrites": False,
            "runtime": "Zircon MagicObject",
            "crystalDatabaseEngineImported": False
        },
        "counts": counts,
        "queue": queue
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("Magic review queue: " + ", ".join(f"{k}={v}" for k, v in sorted(counts.items())))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
