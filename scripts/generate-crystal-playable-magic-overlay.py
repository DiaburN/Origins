#!/usr/bin/env python3
"""Materialize the complete active Crystal + Crystal-Monk spell catalogue in Zircon MagicInfo.

Only the five active ORIGINS classes are projected. The nine Monk source spells
remain retained under deferredClasses.Monk in the catalogue and are deliberately
excluded from the active System.db overlay.

Runtime-ready spells reuse the separately validated ready overlay. Every other
active spell is present in System.db with a reserved ORIGINS placeholder
MagicType so it cannot accidentally execute unrelated Zircon behaviour before
its Crystal handler has been reviewed/ported.

A source enum can legitimately contain an unfinished spell with no MagicInfo
record and no server handler (currently Crystal FastMove). Such a spell is still
materialized as an identity-only, disabled catalogue row. No costs, levels,
power, delay, icon, school or property are invented for that source stub.

Pending automatic reuse is deliberately stricter than a normalized-name match:
the existing Zircon MagicInfo must also belong to the same MirClass. Same-name
spells in another class are never silently repurposed.

Historical Jev can also contain duplicate display names for old and current
SpellIds (currently Blink and Portal). Numeric lookup is therefore deterministic:
for a duplicated current Crystal name exactly one row must have
jevSpellId == sourceSpellId; that row wins regardless of JSON order.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re

CLASS_IDS = {"Warrior":0,"Wizard":1,"Taoist":2,"Assassin":3,"Archer":4}
EXPECTED_COUNTS = {"Warrior":21,"Wizard":28,"Taoist":27,"Assassin":19,"Archer":24}
EXPECTED_TOTAL = 119
EXPECTED_DEFERRED_MONK = 9
PENDING_MAGIC_TYPE_BASE = 3000
PENDING_INDEX_BASE = 3000
SOURCE_STUB_STATUS = "stub_no_magicinfo_no_server_handler"
OVERLAY_SCHEMA_VERSION = 1  # tools/Origins.Database.ApplyOverlay supports schema v1
GENERATOR_SCHEMA_VERSION = 8


def load(path: pathlib.Path):
    return json.loads(path.read_text(encoding="utf-8"))


def norm(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (value or "").lower())


def ids_match(row: dict) -> bool:
    source_id = row.get("sourceSpellId")
    jev_id = row.get("jevSpellId")
    if source_id is None or jev_id is None:
        return False
    return int(source_id) == int(jev_id)


def projection_map(payload: dict) -> dict[str, dict]:
    groups: dict[str, list[dict]] = {}
    for row in payload["projections"]:
        if not row.get("crystalName"):
            continue
        groups.setdefault(norm(row["crystalName"]), []).append(row)

    result: dict[str, dict] = {}
    for key, rows in groups.items():
        if len(rows) == 1:
            result[key] = rows[0]
            continue

        exact = [row for row in rows if ids_match(row)]
        if len(exact) != 1:
            summary = [
                {
                    "crystalName": row.get("crystalName"),
                    "sourceSpellId": row.get("sourceSpellId"),
                    "jevSpellId": row.get("jevSpellId"),
                    "legacyIdMismatch": row.get("legacyIdMismatch"),
                }
                for row in rows
            ]
            raise RuntimeError(
                f"Duplicate numeric projection for {rows[0].get('crystalName')} cannot be resolved by current SpellId: "
                f"{summary}"
            )
        result[key] = exact[0]

    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("base_numeric_projection", type=pathlib.Path)
    parser.add_argument("extension_numeric_projection", type=pathlib.Path)
    parser.add_argument("playable_catalog", type=pathlib.Path)
    parser.add_argument("runtime_ready_overlay", type=pathlib.Path)
    parser.add_argument("zircon_magic_snapshot", type=pathlib.Path)
    parser.add_argument("output", type=pathlib.Path)
    args = parser.parse_args()

    base_numeric = projection_map(load(args.base_numeric_projection))
    extension_numeric = projection_map(load(args.extension_numeric_projection))
    catalog = load(args.playable_catalog)
    ready = load(args.runtime_ready_overlay)
    zircon_rows = load(args.zircon_magic_snapshot)

    scope = catalog.get("scope", {})
    if scope.get("includeMonk") is not False:
        raise RuntimeError("Active overlay generation requires scope.includeMonk=false")
    if set(catalog.get("classes", {})) != set(CLASS_IDS):
        raise RuntimeError(
            f"Active catalogue classes mismatch: expected {sorted(CLASS_IDS)}, "
            f"found {sorted(catalog.get('classes', {}))}"
        )
    deferred_monk = catalog.get("deferredClasses", {}).get("Monk", {}).get("spells", [])
    if len(deferred_monk) != EXPECTED_DEFERRED_MONK:
        raise RuntimeError(
            f"Expected {EXPECTED_DEFERRED_MONK} deferred Monk source spells, found {len(deferred_monk)}"
        )

    ready_operations_by_index = {int(op["Index"]): op for op in ready["Operations"]}
    ready_by_name = {}
    for item in ready.get("$audit", {}).get("included", []):
        spell = item["crystalSpell"]
        index = int(item["zirconIndex"])
        op = ready_operations_by_index.get(index)
        if op is None:
            raise RuntimeError(f"Ready overlay audit references missing operation index {index} for {spell}")
        ready_by_name[norm(spell)] = op

    zircon_by_name: dict[str, list[dict]] = {}
    for row in zircon_rows:
        zircon_by_name.setdefault(norm(row.get("Name") or ""), []).append(row)

    operations, audit = [], []
    used_indices, used_magic_types = set(), set()
    counts = {name:0 for name in CLASS_IDS}
    runtime_ready_count = pending_count = source_stub_count = 0
    rejected_cross_class_name_matches = []

    for class_name, spells in catalog["classes"].items():
        if class_name not in CLASS_IDS:
            raise RuntimeError(f"Unsupported active playable class in catalog: {class_name}")
        desired_class = CLASS_IDS[class_name]

        for spell in spells:
            counts[class_name] += 1
            source_id = int(spell["id"])
            name = spell["name"]
            key = norm(name)
            ready_op = ready_by_name.get(key)

            if ready_op is not None:
                op = json.loads(json.dumps(ready_op))
                op.setdefault("Set", {})["Name"] = name
                op["Set"]["Class"] = desired_class
                index = int(op["Index"])
                existing = next((r for r in zircon_rows if int(r["Index"]) == index), None)
                magic_type = int(op["Set"].get("Magic", existing["Magic"] if existing else 0))
                status = "runtime_ready"
                runtime_ready_count += 1
            else:
                numeric = base_numeric.get(key) or extension_numeric.get(key)
                source_status = spell.get("sourceStatus")
                source_stub = source_status == SOURCE_STUB_STATUS

                if source_stub:
                    if numeric is not None:
                        raise RuntimeError(
                            f"Source stub {class_name}.{name} unexpectedly has numeric projection data; "
                            "do not materialize invented/legacy spell values"
                        )
                    fields = {
                        "Name": name,
                        "Magic": PENDING_MAGIC_TYPE_BASE + source_id,
                        "Class": desired_class,
                        "School": 0,
                        "Property": 0,
                        "Description": "",
                        "Icon": 0,
                        "BaseCost": 0,
                        "LevelCost": 0,
                        "NeedLevel1": 0,
                        "NeedLevel2": 0,
                        "NeedLevel3": 0,
                        "Experience1": 0,
                        "Experience2": 0,
                        "Experience3": 0,
                        "Delay": 0,
                        "LevelDelayReduction": 0,
                        "MinBasePower": 0,
                        "MaxBasePower": 0,
                        "MinLevelPower": 0,
                        "MaxLevelPower": 0,
                    }
                    magic_type = int(fields["Magic"])
                    index = PENDING_INDEX_BASE + source_id
                    op = {
                        "Action": "upsert",
                        "AssemblyName": "LibraryCore",
                        "TypeName": "Library.SystemModels.MagicInfo",
                        "Index": index,
                        "Set": fields,
                    }
                    status = "catalog_source_stub"
                    source_stub_count += 1
                else:
                    if numeric is None:
                        raise RuntimeError(f"No numeric projection found for active spell {class_name}.{name}")

                    fields = numeric["directFieldProjection"]
                    name_matches = zircon_by_name.get(key, [])
                    same_class = [row for row in name_matches if int(row.get("Class", -1)) == desired_class]
                    if len(same_class) > 1:
                        raise RuntimeError(
                            f"Multiple same-class Zircon MagicInfo name matches for {class_name}.{name}: "
                            f"{[row['Index'] for row in same_class]}"
                        )
                    if len(same_class) == 1:
                        existing = same_class[0]
                        index = int(existing["Index"])
                        magic_type = int(existing["Magic"])
                        set_fields = {
                            "Name": name,
                            "Class": desired_class,
                            "Icon": fields["Icon"],
                            "BaseCost": fields["BaseCost"],
                            "LevelCost": fields["LevelCost"],
                            "NeedLevel1": fields["NeedLevel1"],
                            "NeedLevel2": fields["NeedLevel2"],
                            "NeedLevel3": fields["NeedLevel3"],
                            "Experience1": fields["Experience1"],
                            "Experience2": fields["Experience2"],
                            "Experience3": fields["Experience3"],
                            "Delay": fields["Delay"],
                            "LevelDelayReduction": numeric["proof"]["crystalDelayReduction"],
                            "MinBasePower": fields["MinBasePower"],
                            "MaxBasePower": fields["MaxBasePower"],
                            "MinLevelPower": fields["MinLevelPower"],
                            "MaxLevelPower": fields["MaxLevelPower"],
                        }
                        op = {
                            "Action": "upsert",
                            "AssemblyName": "LibraryCore",
                            "TypeName": "Library.SystemModels.MagicInfo",
                            "Index": index,
                            "Set": set_fields,
                        }
                        status = "catalog_existing_runtime_pending"
                    else:
                        if name_matches:
                            rejected_cross_class_name_matches.append({
                                "crystalSpell": name,
                                "crystalClass": class_name,
                                "zirconMatches": [
                                    {
                                        "index": int(row["Index"]),
                                        "name": row.get("Name"),
                                        "class": int(row.get("Class", -1)),
                                        "magic": int(row.get("Magic", -1)),
                                    }
                                    for row in name_matches
                                ],
                            })
                        index = PENDING_INDEX_BASE + source_id
                        magic_type = PENDING_MAGIC_TYPE_BASE + source_id
                        set_fields = {
                            "Name": name,
                            "Magic": magic_type,
                            "Class": desired_class,
                            "School": 0,
                            "Property": 0,
                            "Description": "",
                            "Icon": fields["Icon"],
                            "BaseCost": fields["BaseCost"],
                            "LevelCost": fields["LevelCost"],
                            "NeedLevel1": fields["NeedLevel1"],
                            "NeedLevel2": fields["NeedLevel2"],
                            "NeedLevel3": fields["NeedLevel3"],
                            "Experience1": fields["Experience1"],
                            "Experience2": fields["Experience2"],
                            "Experience3": fields["Experience3"],
                            "Delay": fields["Delay"],
                            "LevelDelayReduction": numeric["proof"]["crystalDelayReduction"],
                            "MinBasePower": fields["MinBasePower"],
                            "MaxBasePower": fields["MaxBasePower"],
                            "MinLevelPower": fields["MinLevelPower"],
                            "MaxLevelPower": fields["MaxLevelPower"],
                        }
                        op = {
                            "Action": "upsert",
                            "AssemblyName": "LibraryCore",
                            "TypeName": "Library.SystemModels.MagicInfo",
                            "Index": index,
                            "Set": set_fields,
                        }
                        status = "catalog_reserved_runtime_pending"
                    pending_count += 1

            if index in used_indices:
                raise RuntimeError(f"Duplicate active MagicInfo index {index} while processing {class_name}.{name}")
            if magic_type in used_magic_types:
                raise RuntimeError(f"Duplicate active MagicType {magic_type} while processing {class_name}.{name}")
            used_indices.add(index)
            used_magic_types.add(magic_type)
            operations.append(op)
            audit.append({
                "class": class_name,
                "crystalSpell": name,
                "crystalSourceSpellId": source_id,
                "sourceStatus": spell.get("sourceStatus", "source_spell"),
                "zirconMagicInfoIndex": index,
                "magicType": magic_type,
                "status": status,
            })

    if counts != EXPECTED_COUNTS:
        raise RuntimeError(f"Per-class count mismatch: expected {EXPECTED_COUNTS}, got {counts}")
    if len(operations) != EXPECTED_TOTAL:
        raise RuntimeError(f"Expected {EXPECTED_TOTAL} active spell operations, got {len(operations)}")
    if source_stub_count != 1:
        raise RuntimeError(f"Expected exactly one active source stub (FastMove), found {source_stub_count}")

    payload = {
        "SchemaVersion": OVERLAY_SCHEMA_VERSION,
        "Name": "Complete active Crystal / Crystal-Monk spell catalogue for ORIGINS",
        "Operations": operations,
        "$audit": {
            "generatorSchemaVersion": GENERATOR_SCHEMA_VERSION,
            "scope": "five active classes; Monk source retained but deferred",
            "playableClassCount": len(CLASS_IDS),
            "playableSpellCount": len(operations),
            "classCounts": counts,
            "deferredMonkSpellsExcluded": len(deferred_monk),
            "runtimeReady": runtime_ready_count,
            "catalogPendingRuntime": pending_count,
            "sourceStubs": source_stub_count,
            "sourceStubPolicy": "identity only; no invented MagicInfo/server behavior",
            "rejectedCrossClassNameMatches": rejected_cross_class_name_matches,
            "spells": audit,
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(
        f"Active Crystal spell overlay: {len(operations)} spells / {len(CLASS_IDS)} classes; "
        f"runtime-ready={runtime_ready_count}; catalog-pending={pending_count}; "
        f"source-stubs={source_stub_count}; deferred Monk={len(deferred_monk)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
