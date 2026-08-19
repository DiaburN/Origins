#!/usr/bin/env python3
"""Generate a deterministic MagicInfo overlay for runtime-ready Crystal spells.

Existing Zircon rows are matched by normalized display name and updated in-place.
Crystal-only spells may be created only when the behavior decision explicitly
supplies a reserved ORIGINS Index and MagicType plus class/school/property.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re


def norm(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (value or "").lower())


def load(path: pathlib.Path):
    return json.loads(path.read_text(encoding="utf-8"))


def numeric_set(fields: dict, numeric: dict) -> dict:
    return {
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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("numeric_projection", type=pathlib.Path)
    parser.add_argument("behavior_decisions", type=pathlib.Path)
    parser.add_argument("zircon_magic_snapshot", type=pathlib.Path)
    parser.add_argument("output", type=pathlib.Path)
    args = parser.parse_args()

    projection = load(args.numeric_projection)
    decisions = load(args.behavior_decisions)
    zircon_rows = load(args.zircon_magic_snapshot)

    projection_by_name = {
        norm(row.get("crystalName") or ""): row
        for row in projection["projections"]
        if row.get("crystalName")
    }
    zircon_by_name = {}
    for row in zircon_rows:
        key = norm(row.get("Name") or "")
        if not key:
            continue
        zircon_by_name.setdefault(key, []).append(row)

    operations = []
    included = []
    skipped = []
    used_indices = set()
    used_magic_types = {int(row["Magic"]) for row in zircon_rows if row.get("Magic") is not None}

    for decision in decisions["decisions"]:
        if not decision.get("runtimeReady"):
            skipped.append({"spell": decision["crystalSpell"], "reason": "runtime_not_ready"})
            continue

        spell = decision["crystalSpell"]
        key = norm(spell)
        numeric = projection_by_name.get(key)
        if numeric is None:
            raise RuntimeError(f"No numeric projection found by name for runtime-ready spell {spell}")
        if numeric.get("status") != "projected_by_name":
            raise RuntimeError(
                f"Numeric projection for {spell} is not a verified name projection: {numeric.get('status')}"
            )

        fields = numeric["directFieldProjection"]
        set_values = numeric_set(fields, numeric)
        matches = zircon_by_name.get(key, [])

        if len(matches) > 1:
            raise RuntimeError(f"Expected at most one Zircon MagicInfo name match for {spell}; found {len(matches)}")

        if len(matches) == 1:
            target = matches[0]
            index = int(target["Index"])
            magic_type = int(target["Magic"])
            mode = "update_existing"
            zircon_name = target.get("Name")
        else:
            create = decision.get("createMagicInfo")
            if not create:
                raise RuntimeError(
                    f"No Zircon MagicInfo name match for {spell}; runtime-ready Crystal-only spells must declare createMagicInfo"
                )

            required = ["Index", "Magic", "Class", "School", "Property"]
            missing = [name for name in required if name not in create]
            if missing:
                raise RuntimeError(f"createMagicInfo for {spell} is missing: {', '.join(missing)}")

            index = int(create["Index"])
            magic_type = int(create["Magic"])
            if index < 1000:
                raise RuntimeError(f"Crystal-only MagicInfo {spell} must use reserved ORIGINS index >= 1000, got {index}")
            if magic_type < 1000:
                raise RuntimeError(f"Crystal-only MagicType {spell} must use reserved ORIGINS value >= 1000, got {magic_type}")
            if magic_type in used_magic_types:
                raise RuntimeError(f"Crystal-only MagicType collision for {spell}: {magic_type}")

            set_values = {
                "Name": fields.get("Name") or spell,
                "Magic": magic_type,
                "Class": int(create["Class"]),
                "School": int(create["School"]),
                "Property": int(create["Property"]),
                "Description": create.get("Description", ""),
                **set_values,
            }
            mode = "create_origins"
            zircon_name = None
            used_magic_types.add(magic_type)

        if index in used_indices:
            raise RuntimeError(f"Duplicate MagicInfo overlay index {index} while processing {spell}")
        used_indices.add(index)

        operations.append({
            "Action": "upsert",
            "AssemblyName": "LibraryCore",
            "TypeName": "Library.SystemModels.MagicInfo",
            "Index": index,
            "Set": set_values,
        })
        included.append({
            "crystalSpell": spell,
            "crystalSourceSpellId": decision["crystalSourceSpellId"],
            "jevSpellId": numeric.get("jevSpellId"),
            "legacyIdMismatch": numeric.get("legacyIdMismatch", False),
            "zirconIndex": index,
            "zirconName": zircon_name,
            "zirconMagic": magic_type,
            "mode": mode,
            "executionKind": decision["executionKind"],
            "runtimeRequirements": numeric.get("runtimeRequirements", []),
            "set": set_values,
        })

    payload = {
        "SchemaVersion": 2,
        "Name": "Runtime-ready Crystal spells mapped or created in Zircon MagicInfo",
        "Operations": operations,
        "$audit": {
            "generatedFromNumericSchemaVersion": projection.get("schemaVersion"),
            "joinKey": "normalized spell name",
            "existingZirconIndicesPreserved": True,
            "crystalOnlyRowsRequireReservedExplicitIdentity": True,
            "included": included,
            "skipped": skipped,
        },
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    updates = sum(1 for item in included if item["mode"] == "update_existing")
    creates = sum(1 for item in included if item["mode"] == "create_origins")
    print(f"Ready Crystal magic overlay candidate: {updates} updates, {creates} creates, {len(skipped)} skipped")
    for item in included:
        print(
            f"- {item['crystalSpell']} -> MagicInfo#{item['zirconIndex']} "
            f"MagicType={item['zirconMagic']} ({item['mode']})"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
