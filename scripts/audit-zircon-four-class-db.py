#!/usr/bin/env python3
"""Audit canonical Zircon MagicInfo rows for the four native player classes.

The report separates source enum coverage from actual System.db content. It never
creates missing spells and never treats enum-only entries as playable.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

CLASS_NUMERIC = {
    "Warrior": 0,
    "Wizard": 1,
    "Taoist": 2,
    "Assassin": 3,
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", type=pathlib.Path, required=True)
    parser.add_argument("--magic-info", type=pathlib.Path, required=True)
    parser.add_argument("--output", type=pathlib.Path, required=True)
    args = parser.parse_args()

    catalog = json.loads(args.catalog.read_text(encoding="utf-8"))
    rows = json.loads(args.magic_info.read_text(encoding="utf-8"))
    if not isinstance(rows, list):
        raise SystemExit("MagicInfo snapshot must be a JSON array")

    report_classes: dict[str, dict[str, object]] = {}
    errors: list[str] = []

    for class_name, class_numeric in CLASS_NUMERIC.items():
        source_entries = catalog["classes"][class_name]
        source_by_id = {int(entry["id"]): entry for entry in source_entries}
        db_rows = [row for row in rows if int(row.get("Class", -999)) == class_numeric]

        db_entries: list[dict[str, object]] = []
        seen_magic: set[int] = set()
        for row in sorted(db_rows, key=lambda item: int(item.get("Index", 0))):
            magic = int(row.get("Magic", -1))
            name = str(row.get("Name", ""))
            if magic not in source_by_id:
                errors.append(
                    f"{class_name} MagicInfo index {row.get('Index')} ({name}) uses unknown/out-of-class MagicType {magic}"
                )
                source_status = "NOT_IN_FOUR_CLASS_CATALOG"
            else:
                source_status = str(source_by_id[magic]["status"])

            if magic in seen_magic:
                errors.append(f"{class_name} has duplicate MagicInfo rows for MagicType {magic}")
            seen_magic.add(magic)

            db_entries.append({
                "index": int(row.get("Index", 0)),
                "magicType": magic,
                "name": name,
                "sourceStatus": source_status,
                "icon": row.get("Icon"),
                "school": row.get("School"),
                "property": row.get("Property"),
                "dbStatus": "DB_PRESENT"
            })

        missing = [
            entry for entry in source_entries
            if int(entry["id"]) not in seen_magic
        ]
        playable_candidates = [
            entry for entry in db_entries
            if entry["sourceStatus"] == "ENUM_DEFINED"
        ]
        upstream_incomplete_present = [
            entry for entry in db_entries
            if entry["sourceStatus"] in {"UPSTREAM_NOT_CODED", "UPSTREAM_UNUSED"}
        ]

        report_classes[class_name] = {
            "classNumeric": class_numeric,
            "sourceEnumCount": len(source_entries),
            "dbPresentCount": len(db_entries),
            "playableCandidateCount": len(playable_candidates),
            "dbEntries": db_entries,
            "missingFromCanonicalDb": missing,
            "upstreamIncompletePresentInDb": upstream_incomplete_present
        }

    report = {
        "schemaVersion": 1,
        "sourceCommit": catalog["source"]["commit"],
        "policy": {
            "enumPresenceMeansPlayable": False,
            "dbPresenceMeansRuntimeHandler": False,
            "nextGate": "RUNTIME_HANDLER_PRESENT"
        },
        "classes": report_classes,
        "totals": {
            "sourceEnum": sum(int(value["sourceEnumCount"]) for value in report_classes.values()),
            "dbPresent": sum(int(value["dbPresentCount"]) for value in report_classes.values()),
            "playableCandidates": sum(int(value["playableCandidateCount"]) for value in report_classes.values())
        },
        "errors": errors
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(
        "Zircon MagicInfo four-class audit: "
        + ", ".join(
            f"{name}={value['dbPresentCount']}/{value['sourceEnumCount']} DB/enum"
            for name, value in report_classes.items()
        )
    )
    print(
        f"Total DB rows={report['totals']['dbPresent']}; "
        f"enum={report['totals']['sourceEnum']}; "
        f"playable candidates={report['totals']['playableCandidates']}"
    )

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
