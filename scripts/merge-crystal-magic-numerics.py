#!/usr/bin/env python3
"""Merge verified playable Crystal and Crystal-Monk numeric projections.

The base Jev database contains more than ORIGINS' five-class playable catalogue:
legacy rows, map-event effects and Crystal custom spell candidates are also
present. Some non-playable rows even have historical duplicate aliases (Blink,
Portal). Those rows are useful audit evidence but must never participate in the
119-spell runtime projection.

Activation therefore accepts only named projections with `kind == player`.
Unnamed legacy rows and named non-player rows are retained separately in the
output. If an eligible playable name is duplicated, the duplicate is resolved
only when exactly one row has the current Crystal SpellId; selection by input
order is never allowed.
"""
from __future__ import annotations

import argparse
import copy
import json
import pathlib
import re


def norm(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (value or "").lower())


def load(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def ids_match(row: dict) -> bool:
    source_id = row.get("sourceSpellId")
    jev_id = row.get("jevSpellId")
    if source_id is None or jev_id is None:
        return False
    return int(source_id) == int(jev_id)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("base_projection", type=pathlib.Path)
    parser.add_argument("extension_projection", type=pathlib.Path)
    parser.add_argument("output", type=pathlib.Path)
    args = parser.parse_args()

    base = load(args.base_projection)
    extension = load(args.extension_projection)
    merged: list[dict] = []
    skipped_legacy_unknown: list[dict] = []
    skipped_non_playable_named: list[dict] = []
    skipped_historical_duplicates: list[dict] = []
    seen: dict[str, str] = {}
    playable_by_source = {"Crystal/Jev": 0, "Crystal-Monk pinned source": 0}

    for source_name, payload in (("Crystal/Jev", base), ("Crystal-Monk pinned source", extension)):
        named_groups: dict[str, list[dict]] = {}
        group_order: list[str] = []

        for original in payload.get("projections", []):
            row = copy.deepcopy(original)
            name = row.get("crystalName")
            status = row.get("status")
            key = norm(name or "")

            if not key:
                if source_name == "Crystal/Jev" and status == "legacy_unknown_name_not_in_current_source":
                    skipped_legacy_unknown.append(row)
                    continue
                raise RuntimeError(
                    f"Unnamed projection is not an approved legacy-unknown row in {source_name}: {row}"
                )

            # ORIGINS activates only the player catalogue. Crystal custom spells
            # such as Blink/Portal and map-event effects are intentionally outside
            # the 119 active spell scope and cannot block or enter this merge.
            if row.get("kind") != "player":
                skipped_non_playable_named.append({
                    **row,
                    "numericSource": source_name,
                    "skipReason": "non_playable_kind_excluded_from_runtime_merge",
                })
                continue

            if key not in named_groups:
                named_groups[key] = []
                group_order.append(key)
            named_groups[key].append(row)

        for key in group_order:
            candidates = named_groups[key]
            chosen: dict

            if len(candidates) == 1:
                chosen = candidates[0]
            else:
                exact = [row for row in candidates if ids_match(row)]
                if len(exact) != 1:
                    summary = [
                        {
                            "crystalName": row.get("crystalName"),
                            "sourceSpellId": row.get("sourceSpellId"),
                            "jevSpellId": row.get("jevSpellId"),
                            "legacyIdMismatch": row.get("legacyIdMismatch"),
                        }
                        for row in candidates
                    ]
                    raise RuntimeError(
                        f"Duplicate playable projection group in {source_name} cannot be resolved by current SpellId: {summary}"
                    )

                chosen = exact[0]
                for rejected in candidates:
                    if rejected is chosen:
                        continue
                    if not rejected.get("legacyIdMismatch"):
                        raise RuntimeError(
                            f"Rejected playable duplicate for {chosen.get('crystalName')} is not marked as a legacy ID mismatch: "
                            f"{rejected}"
                        )
                    skipped_historical_duplicates.append({
                        "source": source_name,
                        "selectedCrystalName": chosen.get("crystalName"),
                        "selectedSourceSpellId": chosen.get("sourceSpellId"),
                        "selectedJevSpellId": chosen.get("jevSpellId"),
                        "rejected": rejected,
                    })

            name = chosen.get("crystalName")
            status = chosen.get("status")
            if status not in {"projected_by_name", "projected_from_pinned_source"}:
                raise RuntimeError(f"Unverified playable numeric projection for {name}: {status}")

            if key in seen:
                raise RuntimeError(f"Duplicate playable numeric projection for {name}: {seen[key]} and {source_name}")

            chosen["sourceProjectionStatus"] = status
            chosen["status"] = "projected_by_name"
            chosen["numericSource"] = source_name
            seen[key] = source_name
            merged.append(chosen)
            playable_by_source[source_name] += 1

    expected_unknown = int(base.get("counts", {}).get("legacyUnknownNames", 0))
    if len(skipped_legacy_unknown) != expected_unknown:
        raise RuntimeError(
            f"Legacy-unknown audit count mismatch: base reports {expected_unknown}, "
            f"merge skipped {len(skipped_legacy_unknown)}"
        )

    # Base Crystal exposes 105 playable identities; FastMove is the sole source
    # stub without MagicInfo numerics, so 104 base player projections must exist.
    if playable_by_source["Crystal/Jev"] != 104:
        raise RuntimeError(
            "Playable Crystal/Jev numeric coverage changed: expected 104 "
            f"(105 base spells minus FastMove), found {playable_by_source['Crystal/Jev']}"
        )

    # Crystal-Monk contributes 14 non-Monk variants plus 9 deferred Monk spells.
    # All 23 retain source numerics; the later active catalogue excludes Monk.
    if playable_by_source["Crystal-Monk pinned source"] != 23:
        raise RuntimeError(
            "Crystal-Monk playable numeric coverage changed: expected 23, found "
            f"{playable_by_source['Crystal-Monk pinned source']}"
        )

    payload = {
        "schemaVersion": 4,
        "baseProjection": str(args.base_projection),
        "extensionProjection": str(args.extension_projection),
        "projectionCount": len(merged),
        "playableProjectionCountBySource": playable_by_source,
        "skippedLegacyUnknownCount": len(skipped_legacy_unknown),
        "skippedLegacyUnknown": skipped_legacy_unknown,
        "skippedNonPlayableNamedCount": len(skipped_non_playable_named),
        "skippedNonPlayableNamed": skipped_non_playable_named,
        "skippedHistoricalDuplicateCount": len(skipped_historical_duplicates),
        "skippedHistoricalDuplicates": skipped_historical_duplicates,
        "policy": {
            "joinKey": "normalized spell name",
            "eligibleKind": "player",
            "legacyUnknownRowsEnterActiveOverlay": False,
            "customAndMapEventRowsEnterActiveOverlay": False,
            "playableDuplicateResolution": "require exactly one row where jevSpellId equals current sourceSpellId",
            "selectionByInputOrder": False,
        },
        "projections": merged,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(
        f"Merged playable magic numeric projections: {len(merged)} "
        f"(Crystal/Jev={playable_by_source['Crystal/Jev']}, "
        f"Crystal-Monk={playable_by_source['Crystal-Monk pinned source']}); "
        f"skipped legacy unknown={len(skipped_legacy_unknown)}, "
        f"non-playable named={len(skipped_non_playable_named)}, "
        f"playable historical duplicates={len(skipped_historical_duplicates)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
