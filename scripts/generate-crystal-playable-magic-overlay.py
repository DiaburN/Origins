#!/usr/bin/env python3
"""Materialize the complete Crystal + Crystal-Monk playable spell catalogue in Zircon MagicInfo.

Runtime-ready spells reuse the separately validated ready overlay. Every other
playable spell is present in System.db with a reserved ORIGINS placeholder
MagicType so it cannot accidentally execute unrelated Zircon behaviour before
its Crystal handler has been reviewed/ported.

A source enum can legitimately contain an unfinished spell with no MagicInfo
record and no server handler (currently Crystal FastMove). Such a spell is still
materialized as an identity-only, disabled catalogue row. No costs, levels,
power, delay, icon, school or property are invented for that source stub.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re

CLASS_IDS = {"Warrior":0,"Wizard":1,"Taoist":2,"Assassin":3,"Archer":4,"Monk":5}
EXPECTED_COUNTS = {"Warrior":21,"Wizard":28,"Taoist":27,"Assassin":19,"Archer":24,"Monk":9}
EXPECTED_TOTAL = 128
PENDING_MAGIC_TYPE_BASE = 3000
PENDING_INDEX_BASE = 3000
SOURCE_STUB_STATUS = "stub_no_magicinfo_no_server_handler"


def load(path: pathlib.Path):
    return json.loads(path.read_text(encoding="utf-8"))


def norm(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (value or "").lower())


def projection_map(payload: dict) -> dict[str, dict]:
    return {norm(row["crystalName"]): row for row in payload["projections"] if row.get("crystalName")}


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

    for class_name, spells in catalog["classes"].items():
        if class_name not in CLASS_IDS:
            raise RuntimeError(f"Unsupported playable class in catalog: {class_name}")
        for spell in spells:
            counts[class_name] += 1
            source_id = int(spell["id"])
            name = spell["name"]
            key = norm(name)
            ready_op = ready_by_name.get(key)

            if ready_op is not None:
                op = json.loads(json.dumps(ready_op))
                op.setdefault("Set", {})["Name"] = name
                op["Set"]["Class"] = CLASS_IDS[class_name]
                index = int(op["Index"])
                existing = next((r for r in zircon_rows if int(r["Index"]) == index), None)
                magic_type = int(op["Set"].get("Magic", existing["Magic"] if existing else 0))
                status = "runtime_ready"
                runtime_ready_count += 1
                numeric_source = "runtime-ready Crystal overlay"
            else:
                projection = base_numeric.get(key) or extension_numeric.get(key)

                if projection is None and spell.get("sourceStatus") == SOURCE_STUB_STATUS:
                    # The upstream source itself has no MagicInfo values to copy.
                    # Keep only the stable identity/class. All omitted MagicInfo
                    # fields retain Zircon defaults and the reserved MagicType has
                    # no registered handler, so the stub cannot execute.
                    magic_type = PENDING_MAGIC_TYPE_BASE + source_id
                    index = PENDING_INDEX_BASE + source_id
                    fields = {
                        "Name": name,
                        "Magic": magic_type,
                        "Class": CLASS_IDS[class_name],
                        "School": 0,
                        "Property": 0,
                        "Description": "",
                    }
                    op = {
                        "Action":"upsert",
                        "AssemblyName":"LibraryCore",
                        "TypeName":"Library.SystemModels.MagicInfo",
                        "Index":index,
                        "Set":fields,
                    }
                    status = "catalog_source_stub"
                    numeric_source = "Crystal source enum only; MagicInfo/runtime absent upstream"
                    source_stub_count += 1
                else:
                    if projection is None:
                        raise RuntimeError(f"Missing numeric projection for playable spell {class_name}.{name}")
                    if projection.get("status") not in {"projected_by_name", "projected_from_pinned_source"}:
                        raise RuntimeError(f"Unverified numeric projection for {class_name}.{name}: {projection.get('status')}")

                    fields = dict(projection["directFieldProjection"])
                    fields["LevelDelayReduction"] = int(projection.get("proof", {}).get("crystalDelayReduction", 0))
                    fields["Name"] = name
                    fields["Class"] = CLASS_IDS[class_name]
                    magic_type = PENDING_MAGIC_TYPE_BASE + source_id
                    fields["Magic"] = magic_type

                    matches = zircon_by_name.get(key, [])
                    available_matches = [r for r in matches if int(r["Index"]) not in used_indices]
                    if len(available_matches) > 1:
                        raise RuntimeError(f"Ambiguous Zircon normalized-name match for {name}: {len(available_matches)} rows")
                    if len(available_matches) == 1:
                        target = available_matches[0]
                        index = int(target["Index"])
                        fields["School"] = int(target.get("School", 0))
                        fields["Property"] = int(target.get("Property", 0))
                        fields["Description"] = target.get("Description", "")
                    else:
                        index = PENDING_INDEX_BASE + source_id
                        fields["School"] = 0
                        fields["Property"] = 0
                        fields["Description"] = ""

                    op = {"Action":"upsert","AssemblyName":"LibraryCore","TypeName":"Library.SystemModels.MagicInfo","Index":index,"Set":fields}
                    status = "catalog_pending_runtime"
                    pending_count += 1
                    numeric_source = "Crystal-Monk pinned source" if key in extension_numeric else "Crystal Jev effective MagicInfo"

            if index in used_indices:
                raise RuntimeError(f"Duplicate MagicInfo target index {index} while materializing {name}")
            used_indices.add(index)
            if magic_type in used_magic_types:
                raise RuntimeError(f"Duplicate playable MagicType {magic_type} while materializing {name}")
            used_magic_types.add(magic_type)
            operations.append(op)
            audit.append({
                "class":class_name,
                "crystalSpell":name,
                "crystalSpellId":source_id,
                "zirconMagicInfoIndex":index,
                "magicType":magic_type,
                "status":status,
                "numericSource":numeric_source,
                "sourceStatus":spell.get("sourceStatus", "defined"),
            })

    if counts != EXPECTED_COUNTS:
        raise RuntimeError(f"Playable class counts mismatch: {counts}")
    if len(operations) != EXPECTED_TOTAL:
        raise RuntimeError(f"Expected {EXPECTED_TOTAL} playable MagicInfo operations, generated {len(operations)}")

    payload = {
        "SchemaVersion": 7,
        "Name": "Complete Crystal + Crystal-Monk playable spell catalogue for ORIGINS",
        "Operations": operations,
        "$audit": {
            "requiredPlayableSpells": EXPECTED_TOTAL,
            "classCounts": counts,
            "runtimeReady": runtime_ready_count,
            "catalogPendingRuntime": pending_count,
            "sourceStubs": source_stub_count,
            "pendingMagicTypeRange": "3000 + Crystal/Crystal-Monk SpellId",
            "pendingMagicInfoIndexRange": "3000 + SpellId when no legacy row is reused",
            "policy": "Pending spells exist in System.db but cannot silently execute unrelated Zircon logic. Source stubs preserve identity only and never receive invented numerics.",
            "spells": audit,
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Playable Crystal magic overlay: {len(operations)}/128 rows; {runtime_ready_count} runtime-ready, {pending_count} pending runtime, {source_stub_count} source stub(s)")
    for class_name in CLASS_IDS:
        print(f"- {class_name}: {counts[class_name]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
