#!/usr/bin/env python3
"""Generate a deterministic MagicInfo overlay for authored runtime-ready Crystal spells.

Resolution order for each runtime-ready Crystal spell:
1. `mapExistingMagicInfo.Magic` explicitly maps to an existing Zircon MagicType.
2. otherwise an exact normalized display-name match updates the existing row.
3. otherwise `createMagicInfo` creates a Crystal-only row with reserved identities.

The authored behavior manifest contains two historical leaf schemas: most batches
use `decisions`, while Archer uses `spells`. Both are accepted so the root
manifest can always be traversed even while Archer rows remain authored as
runtimeReady=false until the full compile/activation gate runs.
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


def load_decisions(path: pathlib.Path) -> dict:
    payload = load(path)
    if "includes" not in payload:
        rows = payload.get("decisions", payload.get("spells"))
        if rows is None:
            raise RuntimeError(f"Decision file {path} has neither decisions/spells nor includes")
        return {
            "schemaVersion": payload.get("schemaVersion", 1),
            "decisions": rows,
            "manifest": str(path),
            "includes": [],
        }

    decisions = []
    seen = set()
    for include in payload["includes"]:
        child_path = (path.parent / include).resolve()
        child = load_decisions(child_path)
        for decision in child["decisions"]:
            key = norm(decision.get("crystalSpell") or "")
            if not key:
                raise RuntimeError(f"Decision without crystalSpell in {child_path}")
            if key in seen:
                raise RuntimeError(f"Duplicate Crystal spell decision across manifest: {decision['crystalSpell']}")
            seen.add(key)
            decisions.append(decision)

    return {
        "schemaVersion": payload.get("schemaVersion", 1),
        "decisions": decisions,
        "manifest": str(path),
        "includes": payload["includes"],
    }


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
    decisions = load_decisions(args.behavior_decisions)
    zircon_rows = load(args.zircon_magic_snapshot)

    projection_by_name = {
        norm(row.get("crystalName") or ""): row
        for row in projection["projections"]
        if row.get("crystalName")
    }
    zircon_by_name: dict[str, list[dict]] = {}
    zircon_by_magic: dict[int, list[dict]] = {}
    for row in zircon_rows:
        key = norm(row.get("Name") or "")
        if key:
            zircon_by_name.setdefault(key, []).append(row)
        if row.get("Magic") is not None:
            zircon_by_magic.setdefault(int(row["Magic"]), []).append(row)

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
        if numeric.get("status") not in {"projected_by_name", "projected_from_pinned_source"}:
            raise RuntimeError(
                f"Numeric projection for {spell} is not a verified source/name projection: {numeric.get('status')}"
            )

        fields = numeric["directFieldProjection"]
        set_values = numeric_set(fields, numeric)
        name_matches = zircon_by_name.get(key, [])
        semantic_map = decision.get("mapExistingMagicInfo")
        create = decision.get("createMagicInfo")
        force_create = bool((create or {}).get("ForceCreate", False))

        if semantic_map and create:
            raise RuntimeError(f"{spell} cannot declare both mapExistingMagicInfo and createMagicInfo")

        if semantic_map:
            if "Magic" not in semantic_map:
                raise RuntimeError(f"mapExistingMagicInfo for {spell} must declare Magic")
            requested_magic = int(semantic_map["Magic"])
            mapped = zircon_by_magic.get(requested_magic, [])
            if len(mapped) != 1:
                raise RuntimeError(
                    f"Expected exactly one Zircon MagicInfo with Magic={requested_magic} for {spell}; found {len(mapped)}"
                )
            target = mapped[0]
            index = int(target["Index"])
            magic_type = int(target["Magic"])
            mode = "map_existing_magic"
            zircon_name = target.get("Name")
            if semantic_map.get("RenameToCrystalName", False):
                set_values["Name"] = fields.get("Name") or spell

        elif len(name_matches) > 1 and not force_create:
            raise RuntimeError(f"Expected at most one Zircon MagicInfo name match for {spell}; found {len(name_matches)}")

        elif len(name_matches) == 1 and not force_create:
            target = name_matches[0]
            index = int(target["Index"])
            magic_type = int(target["Magic"])
            mode = "update_existing"
            zircon_name = target.get("Name")

        else:
            if not create:
                raise RuntimeError(
                    f"No unique Zircon MagicInfo target for {spell}; Crystal-only spells must declare createMagicInfo"
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
            mode = "force_create_origins" if force_create else "create_origins"
            zircon_name = None
            used_magic_types.add(magic_type)

        if index in used_indices:
            raise RuntimeError(f"Duplicate MagicInfo overlay index {index} while processing {spell}")
        used_indices.add(index)

        source_id = decision.get("crystalSourceSpellId", decision.get("id"))
        if source_id is None:
            raise RuntimeError(f"Runtime-ready decision for {spell} is missing a source spell id")

        operations.append({
            "Action": "upsert",
            "AssemblyName": "LibraryCore",
            "TypeName": "Library.SystemModels.MagicInfo",
            "Index": index,
            "Set": set_values,
        })
        included.append({
            "crystalSpell": spell,
            "crystalSourceSpellId": int(source_id),
            "jevSpellId": numeric.get("jevSpellId"),
            "legacyIdMismatch": numeric.get("legacyIdMismatch", False),
            "zirconIndex": index,
            "zirconName": zircon_name,
            "zirconMagic": magic_type,
            "mode": mode,
            "executionKind": decision.get("executionKind", decision.get("mode", "CrystalAdapted")),
            "runtimeRequirements": numeric.get("runtimeRequirements", []),
            "set": set_values,
        })

    payload = {
        "SchemaVersion": 5,
        "Name": "Runtime-ready Crystal spells mapped or created in Zircon MagicInfo",
        "Operations": operations,
        "$audit": {
            "generatedFromNumericSchemaVersion": projection.get("schemaVersion"),
            "decisionManifest": decisions.get("manifest", str(args.behavior_decisions)),
            "decisionIncludes": decisions.get("includes", []),
            "numericJoinKey": "normalized Crystal spell name",
            "existingZirconIndicesPreserved": True,
            "semanticMappingsRequireExplicitMagicType": True,
            "crystalOnlyRowsRequireReservedExplicitIdentity": True,
            "forceCreateProtectsCrossClassNameCollisions": True,
            "included": included,
            "skipped": skipped,
        },
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    updates = sum(1 for item in included if item["mode"] in {"update_existing", "map_existing_magic"})
    creates = len(included) - updates
    print(f"Ready Crystal magic overlay candidate: {updates} updates/maps, {creates} creates, {len(skipped)} skipped")
    for item in included:
        print(
            f"- {item['crystalSpell']} -> MagicInfo#{item['zirconIndex']} "
            f"MagicType={item['zirconMagic']} ({item['mode']})"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
