#!/usr/bin/env python3
"""Audit native Zircon spell runtime coverage for ORIGINS-DxR.

This mirrors SEnvir.CreateMagic(): only non-abstract classes whose direct base
is MagicObject and which carry MagicTypeAttribute are runtime-registered.
The audit combines source enum, canonical MagicInfo DB rows and those registered
handler classes without inventing or patching any spell.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys
from collections import defaultdict
from typing import Any

CLASS_NUMERIC = {
    "Warrior": 0,
    "Wizard": 1,
    "Taoist": 2,
    "Assassin": 3,
}

INCOMPLETE_SOURCE_STATUSES = {"UPSTREAM_NOT_CODED", "UPSTREAM_UNUSED"}

# Exact fields present on Library.SystemModels.MagicInfo in pinned Zircon
# cbf1aa919083bc13fc3f23f93772a8ab8370632d. LevelDelayReduction is
# deliberately absent: it is not a property of the pinned model.
MAGIC_INFO_FIELDS = (
    "Index",
    "Name",
    "Magic",
    "Class",
    "School",
    "Property",
    "Icon",
    "MinBasePower",
    "MaxBasePower",
    "MinLevelPower",
    "MaxLevelPower",
    "BaseCost",
    "LevelCost",
    "NeedLevel1",
    "NeedLevel2",
    "NeedLevel3",
    "Experience1",
    "Experience2",
    "Experience3",
    "Delay",
    "Description",
)

CLASS_DECL = re.compile(
    r"(?P<attrs>(?:\s*\[[^\]]+\]\s*)+)"
    r"(?P<mods>(?:(?:public|internal|private|protected|sealed|partial|abstract)\s+)*)"
    r"class\s+(?P<class>[A-Za-z_][A-Za-z0-9_]*)\s*:\s*(?P<base>[A-Za-z_][A-Za-z0-9_]*)",
    re.MULTILINE,
)
MAGIC_ATTR = re.compile(r"MagicType\s*\(\s*MagicType\.([A-Za-z_][A-Za-z0-9_]*)\s*\)")


def scan_handlers(root: pathlib.Path) -> tuple[dict[str, list[dict[str, str]]], list[dict[str, str]]]:
    registered: dict[str, list[dict[str, str]]] = defaultdict(list)
    rejected: list[dict[str, str]] = []

    for path in sorted(root.rglob("*.cs")):
        text = path.read_text(encoding="utf-8-sig", errors="ignore")
        for match in CLASS_DECL.finditer(text):
            attrs = match.group("attrs")
            magic_names = MAGIC_ATTR.findall(attrs)
            if not magic_names:
                continue

            mods = set(match.group("mods").split())
            base = match.group("base")
            entry = {
                "className": match.group("class"),
                "baseType": base,
                "path": str(path.relative_to(root.parent.parent.parent)),
            }

            qualifies = base == "MagicObject" and "abstract" not in mods
            for magic_name in magic_names:
                if qualifies:
                    registered[magic_name].append(dict(entry))
                else:
                    rejected.append(
                        {
                            **entry,
                            "magicTypeName": magic_name,
                            "reason": "does_not_match_SEnvir_CreateMagic_gate",
                        }
                    )

    return dict(registered), rejected


def magic_info_payload(row: dict[str, Any]) -> dict[str, Any]:
    return {field[0].lower() + field[1:]: row.get(field) for field in MAGIC_INFO_FIELDS}


def empty_counts() -> dict[str, int]:
    return {
        "enum": 0,
        "dbPresent": 0,
        "handlerPresent": 0,
        "playable": 0,
        "enumOnly": 0,
        "dbWithoutHandler": 0,
        "handlerWithoutDb": 0,
        "upstreamNotCoded": 0,
        "upstreamUnused": 0,
        "upstreamIncomplete": 0,
    }


def classify(source_status: str, db_present: bool, handler_present: bool) -> str:
    if source_status == "UPSTREAM_NOT_CODED":
        return "UPSTREAM_NOT_CODED"
    if source_status == "UPSTREAM_UNUSED":
        return "UPSTREAM_UNUSED"
    if db_present and handler_present:
        return "PLAYABLE"
    if db_present:
        return "DB_PRESENT_NO_RUNTIME_HANDLER"
    if handler_present:
        return "RUNTIME_HANDLER_NO_DB"
    return "ENUM_ONLY"


def add_classification(counts: dict[str, int], status: str) -> None:
    if status == "PLAYABLE":
        counts["playable"] += 1
    elif status == "ENUM_ONLY":
        counts["enumOnly"] += 1
    elif status == "DB_PRESENT_NO_RUNTIME_HANDLER":
        counts["dbWithoutHandler"] += 1
    elif status == "RUNTIME_HANDLER_NO_DB":
        counts["handlerWithoutDb"] += 1
    elif status == "UPSTREAM_NOT_CODED":
        counts["upstreamNotCoded"] += 1
        counts["upstreamIncomplete"] += 1
    elif status == "UPSTREAM_UNUSED":
        counts["upstreamUnused"] += 1
        counts["upstreamIncomplete"] += 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", type=pathlib.Path, required=True)
    parser.add_argument("--magic-info", type=pathlib.Path, required=True)
    parser.add_argument("--magics-root", type=pathlib.Path, required=True)
    parser.add_argument("--output", type=pathlib.Path, required=True)
    args = parser.parse_args()

    catalog = json.loads(args.catalog.read_text(encoding="utf-8-sig"))
    db_rows = json.loads(args.magic_info.read_text(encoding="utf-8-sig"))
    handlers, rejected_handlers = scan_handlers(args.magics_root)

    if not isinstance(db_rows, list):
        raise SystemExit("MagicInfo snapshot must be a JSON array")

    errors: list[str] = []
    classes: dict[str, dict[str, object]] = {}
    totals = empty_counts()

    for class_name, class_numeric in CLASS_NUMERIC.items():
        source_entries = catalog["classes"][class_name]
        source_by_id = {int(entry["id"]): entry for entry in source_entries}
        source_by_name = {str(entry["name"]): entry for entry in source_entries}
        rows = [row for row in db_rows if int(row.get("Class", -999)) == class_numeric]

        db_by_magic: dict[int, list[dict[str, Any]]] = defaultdict(list)
        for row in rows:
            db_by_magic[int(row.get("Magic", -1))].append(row)

        entries: list[dict[str, object]] = []
        class_counts = empty_counts()
        class_counts["enum"] = len(source_entries)
        totals["enum"] += len(source_entries)

        for source in source_entries:
            magic_id = int(source["id"])
            magic_name = str(source["name"])
            source_status = str(source["status"])
            matching_db = db_by_magic.get(magic_id, [])
            matching_handlers = handlers.get(magic_name, [])

            if len(matching_db) > 1:
                errors.append(f"{class_name}/{magic_name}: duplicate MagicInfo rows ({len(matching_db)})")
            if len(matching_handlers) > 1:
                errors.append(f"{class_name}/{magic_name}: multiple registered handlers ({len(matching_handlers)})")

            db_present = len(matching_db) == 1
            handler_present = len(matching_handlers) == 1
            final_status = classify(source_status, db_present, handler_present)

            if db_present:
                class_counts["dbPresent"] += 1
                totals["dbPresent"] += 1
            if handler_present:
                class_counts["handlerPresent"] += 1
                totals["handlerPresent"] += 1

            add_classification(class_counts, final_status)
            add_classification(totals, final_status)

            db_payload = magic_info_payload(matching_db[0]) if db_present else None
            entries.append(
                {
                    "magicType": magic_id,
                    "magicTypeName": magic_name,
                    "sourceStatus": source_status,
                    "dbPresent": db_present,
                    "runtimeHandlerPresent": handler_present,
                    "status": final_status,
                    "magicInfo": db_payload,
                    "runtimeHandler": matching_handlers[0] if handler_present else None,
                }
            )

        # DB rows claiming this class must map to the class's native MagicType catalog.
        for magic_id, matching_db in sorted(db_by_magic.items()):
            if magic_id not in source_by_id:
                names = [str(row.get("Name", "")) for row in matching_db]
                errors.append(f"{class_name}: DB MagicType {magic_id} not in native class catalog: {names}")

        # Defensive invariant: every catalog name is unique inside its class.
        if len(source_by_name) != len(source_entries):
            errors.append(f"{class_name}: duplicate MagicType names in catalog")

        classified = (
            class_counts["playable"]
            + class_counts["enumOnly"]
            + class_counts["dbWithoutHandler"]
            + class_counts["handlerWithoutDb"]
            + class_counts["upstreamNotCoded"]
            + class_counts["upstreamUnused"]
        )
        if classified != class_counts["enum"]:
            errors.append(
                f"{class_name}: classification invariant failed; enum={class_counts['enum']} classified={classified}"
            )

        classes[class_name] = {
            "classNumeric": class_numeric,
            "counts": class_counts,
            "dbRowCountForClass": len(rows),
            "entries": entries,
        }

    catalog_names = {
        str(entry["name"])
        for class_payload in catalog["classes"].values()
        for entry in class_payload
    }
    registered_outside_catalog = [
        {"magicTypeName": name, "handlers": rows}
        for name, rows in sorted(handlers.items())
        if name not in catalog_names
    ]

    classified_total = (
        totals["playable"]
        + totals["enumOnly"]
        + totals["dbWithoutHandler"]
        + totals["handlerWithoutDb"]
        + totals["upstreamNotCoded"]
        + totals["upstreamUnused"]
    )
    if classified_total != totals["enum"]:
        errors.append(
            f"TOTAL: classification invariant failed; enum={totals['enum']} classified={classified_total}"
        )

    report = {
        "schemaVersion": 2,
        "source": {
            "repository": catalog["source"]["repository"],
            "commit": catalog["source"]["commit"],
            "registrationRule": "SEnvir.CreateMagic: direct base MagicObject + non-abstract + MagicTypeAttribute",
        },
        "policy": {
            "activeClasses": list(CLASS_NUMERIC),
            "crystalRuntimeAllowed": False,
            "playableDefinition": "ENUM_DEFINED + exactly one MagicInfo row + exactly one registered MagicObject handler",
            "upstreamIncompleteNeverPromotedToPlayable": True,
        },
        "pinnedMagicInfoModel": {
            "fields": list(MAGIC_INFO_FIELDS),
            "levelDelayReduction": {
                "presentInPinnedModel": False,
                "value": None,
                "note": "MagicInfo.LevelDelayReduction does not exist in pinned Zircon cbf1aa919083bc13fc3f23f93772a8ab8370632d; ORIGINS-DxR does not invent or restore it.",
            },
        },
        "activeClasses": list(CLASS_NUMERIC),
        "totals": totals,
        "classes": classes,
        "registeredHandlersOutsideFourClassCatalog": registered_outside_catalog,
        "annotatedClassesRejectedByRegistrationGate": rejected_handlers,
        "errors": errors,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(
        "Zircon four-class runtime audit: "
        f"enum={totals['enum']}, db={totals['dbPresent']}, handlers={totals['handlerPresent']}, "
        f"playable={totals['playable']}, enum-only={totals['enumOnly']}, "
        f"db-no-handler={totals['dbWithoutHandler']}, handler-no-db={totals['handlerWithoutDb']}, "
        f"not-coded={totals['upstreamNotCoded']}, unused={totals['upstreamUnused']}"
    )
    for class_name in CLASS_NUMERIC:
        c = classes[class_name]["counts"]
        print(
            f"  {class_name}: enum={c['enum']} db={c['dbPresent']} handlers={c['handlerPresent']} "
            f"playable={c['playable']} enum-only={c['enumOnly']} db-no-handler={c['dbWithoutHandler']} "
            f"handler-no-db={c['handlerWithoutDb']} not-coded={c['upstreamNotCoded']} unused={c['upstreamUnused']}"
        )

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
