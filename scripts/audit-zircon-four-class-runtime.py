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

CLASS_NUMERIC = {
    "Warrior": 0,
    "Wizard": 1,
    "Taoist": 2,
    "Assassin": 3,
}

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
                    rejected.append({**entry, "magicTypeName": magic_name, "reason": "does_not_match_SEnvir_CreateMagic_gate"})

    return dict(registered), rejected


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", type=pathlib.Path, required=True)
    parser.add_argument("--magic-info", type=pathlib.Path, required=True)
    parser.add_argument("--magics-root", type=pathlib.Path, required=True)
    parser.add_argument("--output", type=pathlib.Path, required=True)
    args = parser.parse_args()

    catalog = json.loads(args.catalog.read_text(encoding="utf-8"))
    db_rows = json.loads(args.magic_info.read_text(encoding="utf-8"))
    handlers, rejected_handlers = scan_handlers(args.magics_root)

    if not isinstance(db_rows, list):
        raise SystemExit("MagicInfo snapshot must be a JSON array")

    errors: list[str] = []
    classes: dict[str, dict[str, object]] = {}
    totals = {
        "enum": 0,
        "dbPresent": 0,
        "handlerPresent": 0,
        "playable": 0,
        "enumOnly": 0,
        "dbWithoutHandler": 0,
        "handlerWithoutDb": 0,
        "upstreamIncomplete": 0,
    }

    for class_name, class_numeric in CLASS_NUMERIC.items():
        source_entries = catalog["classes"][class_name]
        source_by_id = {int(entry["id"]): entry for entry in source_entries}
        source_by_name = {str(entry["name"]): entry for entry in source_entries}
        rows = [row for row in db_rows if int(row.get("Class", -999)) == class_numeric]

        db_by_magic: dict[int, list[dict]] = defaultdict(list)
        for row in rows:
            db_by_magic[int(row.get("Magic", -1))].append(row)

        entries: list[dict[str, object]] = []
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

            if source_status in {"UPSTREAM_NOT_CODED", "UPSTREAM_UNUSED"}:
                final_status = source_status
                totals["upstreamIncomplete"] += 1
            elif db_present and handler_present:
                final_status = "PLAYABLE"
                totals["playable"] += 1
            elif db_present:
                final_status = "DB_PRESENT_NO_RUNTIME_HANDLER"
                totals["dbWithoutHandler"] += 1
            elif handler_present:
                final_status = "RUNTIME_HANDLER_NO_DB"
                totals["handlerWithoutDb"] += 1
            else:
                final_status = "ENUM_ONLY"
                totals["enumOnly"] += 1

            if db_present:
                totals["dbPresent"] += 1
            if handler_present:
                totals["handlerPresent"] += 1

            db_payload = None
            if db_present:
                row = matching_db[0]
                db_payload = {
                    "index": int(row.get("Index", 0)),
                    "name": row.get("Name"),
                    "icon": row.get("Icon"),
                    "school": row.get("School"),
                    "property": row.get("Property"),
                }

            entries.append({
                "magicType": magic_id,
                "magicTypeName": magic_name,
                "sourceStatus": source_status,
                "dbPresent": db_present,
                "runtimeHandlerPresent": handler_present,
                "status": final_status,
                "magicInfo": db_payload,
                "runtimeHandler": matching_handlers[0] if handler_present else None,
            })

        # DB rows claiming this class must map to the class's native MagicType range/catalog.
        for magic_id, matching_db in sorted(db_by_magic.items()):
            if magic_id not in source_by_id:
                names = [str(row.get("Name", "")) for row in matching_db]
                errors.append(f"{class_name}: DB MagicType {magic_id} not in native class catalog: {names}")

        # A qualifying handler in this class range whose MagicType name is not in the catalog is also suspicious.
        class_handler_extras = []
        for magic_name, handler_rows in handlers.items():
            if magic_name in source_by_name:
                continue
            # Do not classify handlers from other class ranges here; only record globally below.
            if any(magic_name == str(entry["name"]) for entry in source_entries):
                class_handler_extras.extend(handler_rows)

        classes[class_name] = {
            "classNumeric": class_numeric,
            "enumCount": len(source_entries),
            "dbRowCount": len(rows),
            "playableCount": sum(1 for entry in entries if entry["status"] == "PLAYABLE"),
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

    report = {
        "schemaVersion": 1,
        "source": {
            "repository": catalog["source"]["repository"],
            "commit": catalog["source"]["commit"],
            "registrationRule": "SEnvir.CreateMagic: direct base MagicObject + non-abstract + MagicTypeAttribute",
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
        f"upstream-incomplete={totals['upstreamIncomplete']}"
    )

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
