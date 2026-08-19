#!/usr/bin/env python3
"""Merge verified Crystal and Crystal-Monk numeric projections for activation.

The base Jev projection can contain two kinds of historical rows that must not
enter the active ORIGINS projection:

1. legacy DB rows whose normalized names no longer exist in pinned Crystal;
2. legacy aliases whose display name now belongs to a newer spell identity.

The latter is visible in Jev for Blink and Portal: an old row shares the modern
display name, while a second row has the current Crystal SpellId. When a name is
duplicated we therefore select exactly one row whose `jevSpellId` equals the
current `sourceSpellId`; every rejected sibling must be explicitly marked as a
legacy ID mismatch. Nothing is selected by file order.

Crystal-Monk extension rows are projected directly from the pinned fork. All
accepted rows are normalized to status=projected_by_name while original status
and skipped historical evidence remain available for audit.
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
    skipped_historical_duplicates: list[dict] = []
    seen: dict[str, str] = {}

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
                        f"Duplicate projection group in {source_name} cannot be resolved by current SpellId: {summary}"
                    )

                chosen = exact[0]
                for rejected in candidates:
                    if rejected is chosen:
                        continue
                    if not rejected.get("legacyIdMismatch"):
                        raise RuntimeError(
                            f"Rejected duplicate for {chosen.get('crystalName')} is not marked as a legacy ID mismatch: "
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
                raise RuntimeError(f"Unverified numeric projection for {name}: {status}")

            if key in seen:
                raise RuntimeError(f"Duplicate numeric projection for {name}: {seen[key]} and {source_name}")

            chosen["sourceProjectionStatus"] = status
            chosen["status"] = "projected_by_name"
            chosen["numericSource"] = source_name
            seen[key] = source_name
            merged.append(chosen)

    expected_unknown = int(base.get("counts", {}).get("legacyUnknownNames", 0))
    if len(skipped_legacy_unknown) != expected_unknown:
        raise RuntimeError(
            f"Legacy-unknown audit count mismatch: base reports {expected_unknown}, "
            f"merge skipped {len(skipped_legacy_unknown)}"
        )

    payload = {
        "schemaVersion": 3,
        "baseProjection": str(args.base_projection),
        "extensionProjection": str(args.extension_projection),
        "projectionCount": len(merged),
        "skippedLegacyUnknownCount": len(skipped_legacy_unknown),
        "skippedLegacyUnknown": skipped_legacy_unknown,
        "skippedHistoricalDuplicateCount": len(skipped_historical_duplicates),
        "skippedHistoricalDuplicates": skipped_historical_duplicates,
        "policy": {
            "joinKey": "normalized spell name",
            "legacyUnknownRowsEnterActiveOverlay": False,
            "duplicateNameResolution": "require exactly one row where jevSpellId equals current sourceSpellId",
            "selectionByInputOrder": False,
        },
        "projections": merged,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(
        f"Merged verified magic numeric projections: {len(merged)}; "
        f"skipped legacy unknown rows: {len(skipped_legacy_unknown)}; "
        f"skipped historical duplicate aliases: {len(skipped_historical_duplicates)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
