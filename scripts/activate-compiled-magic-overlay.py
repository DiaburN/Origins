#!/usr/bin/env python3
"""Bind the final 119-row ORIGINS spell overlay to compiled Zircon handlers.

The catalogue generator intentionally materializes unvalidated spells with
reserved placeholder MagicType values and School/Property=None. Once the full
runtime has applied cleanly, all routed handlers have compiled, and handler
registration has been verified, this finalizer replaces those placeholders with
the actual MagicType identities from the patched Zircon enum.

When a routed MagicType already has a native Zircon MagicInfo row, ORIGINS reuses
that row's index instead of creating a second MagicInfo with the same MagicType.
This is essential for renamed Crystal identities such as Fencing ->
Swordsmanship, Healing -> Heal, and similar semantic handler mappings.

Exactly one active spell remains disabled: FastMove. The pinned Crystal source
contains only a commented/unfinished placeholder for it and no usable server
handler, so ORIGINS preserves its identity without inventing runtime behaviour.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re

EXPECTED_TOTAL = 119
EXPECTED_RUNTIME_ROUTES = 118
EXPECTED_SOURCE_STUBS = 1
EXPECTED_COUNTS = {"Warrior": 21, "Wizard": 28, "Taoist": 27, "Assassin": 19, "Archer": 24}

MAGIC_SCHOOL_PASSIVE = 1
MAGIC_SCHOOL_ACTIVE = 2
MAGIC_PROPERTY_ACTIVE = 1
MAGIC_PROPERTY_PASSIVE = 2


def norm(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (value or "").lower())


def load_json(path: pathlib.Path):
    return json.loads(path.read_text(encoding="utf-8"))


def load_decisions(path: pathlib.Path) -> list[dict]:
    payload = load_json(path)
    if "includes" not in payload:
        return payload.get("decisions", payload.get("spells", []))

    result: list[dict] = []
    seen: set[str] = set()
    for include in payload["includes"]:
        child_path = path.parent / include
        for decision in load_decisions(child_path):
            key = norm(decision.get("crystalSpell", ""))
            if not key:
                raise RuntimeError(f"Decision without crystalSpell in {child_path}")
            if key in seen:
                raise RuntimeError(f"Duplicate Crystal decision: {decision['crystalSpell']}")
            seen.add(key)
            result.append(decision)
    return result


def strip_line_comment(line: str) -> str:
    return line.split("//", 1)[0].strip()


def parse_magic_type_enum(path: pathlib.Path) -> dict[str, int]:
    text = path.read_text(encoding="utf-8-sig")
    marker = re.search(r"\bpublic\s+enum\s+MagicType\b", text)
    if marker is None:
        raise RuntimeError(f"Could not locate public enum MagicType in {path}")

    open_brace = text.find("{", marker.end())
    if open_brace < 0:
        raise RuntimeError(f"Could not locate MagicType opening brace in {path}")

    depth = 0
    close_brace = -1
    for pos in range(open_brace, len(text)):
        ch = text[pos]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                close_brace = pos
                break
    if close_brace < 0:
        raise RuntimeError(f"Could not locate MagicType closing brace in {path}")

    values: dict[str, int] = {}
    last_value = -1
    for raw_line in text[open_brace + 1:close_brace].splitlines():
        line = strip_line_comment(raw_line)
        if not line:
            continue
        if line.endswith(","):
            line = line[:-1].strip()
        if not line:
            continue

        match = re.fullmatch(r"(?P<name>[A-Za-z_][A-Za-z0-9_]*)(?:\s*=\s*(?P<value>-?\d+))?", line)
        if match is None:
            raise RuntimeError(f"Unsupported MagicType enum entry while parsing {path}: {raw_line.strip()}")

        name = match.group("name")
        raw_value = match.group("value")
        value = int(raw_value) if raw_value is not None else last_value + 1
        if name in values:
            raise RuntimeError(f"Duplicate MagicType enum name {name}")
        values[name] = value
        last_value = value

    return values


def is_passive(decision: dict) -> bool:
    behavior = decision.get("portedBehavior", [])
    if not isinstance(behavior, list):
        behavior = [behavior]

    metadata = " ".join([
        str(decision.get("mode", "")),
        str(decision.get("executionKind", "")),
        str(decision.get("sourceStatus", "")),
        *(str(item) for item in behavior),
    ]).lower()

    explicit_passive = {"focus", "meditation"}
    return "passive" in metadata or norm(decision.get("crystalSpell", "")) in explicit_passive


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input_overlay", type=pathlib.Path)
    parser.add_argument("behavior_decisions", type=pathlib.Path)
    parser.add_argument("zircon_enum", type=pathlib.Path)
    parser.add_argument("zircon_magic_snapshot", type=pathlib.Path)
    parser.add_argument("output_overlay", type=pathlib.Path)
    args = parser.parse_args()

    overlay = load_json(args.input_overlay)
    operations = overlay.get("Operations", [])
    audit = overlay.get("$audit", {})
    spells = audit.get("spells", [])
    zircon_rows = load_json(args.zircon_magic_snapshot)

    if len(operations) != EXPECTED_TOTAL or len(spells) != EXPECTED_TOTAL:
        raise RuntimeError(
            f"Expected {EXPECTED_TOTAL} overlay operations/audit rows, found "
            f"{len(operations)}/{len(spells)}"
        )
    if audit.get("classCounts") != EXPECTED_COUNTS:
        raise RuntimeError(f"Unexpected active class counts: {audit.get('classCounts')}")
    if audit.get("deferredMonkSpellsExcluded") != 9:
        raise RuntimeError(
            f"Expected 9 deferred Monk spells, found {audit.get('deferredMonkSpellsExcluded')}"
        )

    all_decisions = load_decisions(args.behavior_decisions)
    decision_by_name: dict[str, dict] = {}
    for decision in all_decisions:
        key = norm(decision.get("crystalSpell", ""))
        if not key:
            raise RuntimeError("Encountered behavior decision without crystalSpell")
        if key in decision_by_name:
            raise RuntimeError(f"Duplicate behavior decision for {decision['crystalSpell']}")
        decision_by_name[key] = decision

    routed = [d for d in all_decisions if d.get("zirconMagicType")]
    if len(routed) != EXPECTED_RUNTIME_ROUTES:
        raise RuntimeError(
            f"Expected {EXPECTED_RUNTIME_ROUTES} routed decisions, found {len(routed)}"
        )

    enum_values = parse_magic_type_enum(args.zircon_enum)

    op_by_original_index = {int(op["Index"]): op for op in operations}
    if len(op_by_original_index) != EXPECTED_TOTAL:
        raise RuntimeError("Pre-activation overlay contains duplicate MagicInfo operation indices")

    base_by_magic: dict[int, list[dict]] = {}
    for row in zircon_rows:
        if row.get("Magic") is None:
            continue
        base_by_magic.setdefault(int(row["Magic"]), []).append(row)

    activated = 0
    source_stubs = 0
    actual_magic_values: set[int] = set()
    activated_spells: list[dict] = []

    for spell_audit in spells:
        spell = spell_audit["crystalSpell"]
        key = norm(spell)
        decision = decision_by_name.get(key)
        if decision is None:
            raise RuntimeError(f"No behavior decision found for active spell {spell}")

        original_index = int(spell_audit["zirconMagicInfoIndex"])
        operation = op_by_original_index.get(original_index)
        if operation is None:
            raise RuntimeError(f"No MagicInfo operation #{original_index} for {spell}")
        fields = operation.setdefault("Set", {})

        magic_type_name = decision.get("zirconMagicType")
        if not magic_type_name:
            if key != "fastmove" or decision.get("executionKind") != "SourceStub":
                raise RuntimeError(f"Unrouted active spell is not the approved FastMove source stub: {spell}")
            source_stubs += 1
            fields["School"] = 0
            fields["Property"] = 0
            spell_audit["status"] = "catalog_source_stub"
            spell_audit["runtimeActivated"] = False
            continue

        if magic_type_name not in enum_values:
            raise RuntimeError(f"MagicType.{magic_type_name} for {spell} is absent from patched Zircon Enum.cs")
        actual_magic = enum_values[magic_type_name]
        if actual_magic in actual_magic_values:
            raise RuntimeError(f"Duplicate routed MagicType value {actual_magic} while activating {spell}")
        actual_magic_values.add(actual_magic)

        desired_class = int(fields.get("Class", -1))
        existing_rows = base_by_magic.get(actual_magic, [])
        if len(existing_rows) > 1:
            raise RuntimeError(
                f"Native Zircon snapshot contains {len(existing_rows)} MagicInfo rows for MagicType "
                f"{actual_magic} ({magic_type_name})"
            )

        reused_native = False
        if len(existing_rows) == 1:
            native = existing_rows[0]
            native_class = int(native.get("Class", -1))
            if native_class != desired_class:
                raise RuntimeError(
                    f"Cross-class MagicType reuse rejected for {spell}: desired class={desired_class}, "
                    f"native MagicInfo#{native['Index']} class={native_class}, MagicType={actual_magic}"
                )

            native_index = int(native["Index"])
            operation["Index"] = native_index
            spell_audit["zirconMagicInfoIndex"] = native_index
            reused_native = True

            if int(fields.get("School", 0)) == 0 and int(native.get("School", 0)) != 0:
                fields["School"] = int(native["School"])
            if int(fields.get("Property", 0)) == 0 and int(native.get("Property", 0)) != 0:
                fields["Property"] = int(native["Property"])
            if not fields.get("Description") and native.get("Description"):
                fields["Description"] = native["Description"]

        fields["Magic"] = actual_magic

        passive = is_passive(decision)
        if int(fields.get("School", 0)) == 0:
            fields["School"] = MAGIC_SCHOOL_PASSIVE if passive else MAGIC_SCHOOL_ACTIVE
        if int(fields.get("Property", 0)) == 0:
            fields["Property"] = MAGIC_PROPERTY_PASSIVE if passive else MAGIC_PROPERTY_ACTIVE

        if int(fields["School"]) == 0 or int(fields["Property"]) == 0:
            raise RuntimeError(f"Activated spell {spell} still has disabled School/Property metadata")

        final_index = int(operation["Index"])
        spell_audit["magicType"] = actual_magic
        spell_audit["magicTypeName"] = magic_type_name
        spell_audit["status"] = "compiled_runtime_ready"
        spell_audit["runtimeActivated"] = True
        spell_audit["reusedNativeMagicInfo"] = reused_native
        activated += 1
        activated_spells.append({
            "spell": spell,
            "magicTypeName": magic_type_name,
            "magicType": actual_magic,
            "magicInfoIndex": final_index,
            "reusedNativeMagicInfo": reused_native,
            "school": int(fields["School"]),
            "property": int(fields["Property"]),
        })

    final_indices = [int(op["Index"]) for op in operations]
    if len(final_indices) != len(set(final_indices)):
        duplicates = sorted({idx for idx in final_indices if final_indices.count(idx) > 1})
        raise RuntimeError(f"Runtime activation produced duplicate MagicInfo target indices: {duplicates}")

    if activated != EXPECTED_RUNTIME_ROUTES:
        raise RuntimeError(f"Expected {EXPECTED_RUNTIME_ROUTES} activated spells, got {activated}")
    if source_stubs != EXPECTED_SOURCE_STUBS:
        raise RuntimeError(f"Expected one source stub, got {source_stubs}")

    audit["runtimeReady"] = activated
    audit["catalogPendingRuntime"] = 0
    audit["sourceStubs"] = source_stubs
    audit["runtimeActivation"] = {
        "status": "compiled_handlers_bound",
        "activated": activated,
        "sourceStubs": source_stubs,
        "nativeMagicInfoRowsReused": sum(1 for item in activated_spells if item["reusedNativeMagicInfo"]),
        "originsMagicInfoRowsUsed": sum(1 for item in activated_spells if not item["reusedNativeMagicInfo"]),
        "magicTypeSource": str(args.zircon_enum),
        "magicInfoBase": str(args.zircon_magic_snapshot),
        "policy": (
            "All 118 explicitly routed active spells are bound to the numeric MagicType values "
            "compiled into patched Zircon. Existing native MagicInfo rows are reused by MagicType "
            "to prevent duplicate handler identities for renamed Crystal spells. FastMove remains "
            "disabled because upstream Crystal contains no usable MagicInfo/server handler. New "
            "ORIGINS rows receive non-None integration metadata, with passive decisions retained "
            "as passive."
        ),
        "spells": activated_spells,
    }

    args.output_overlay.parent.mkdir(parents=True, exist_ok=True)
    args.output_overlay.write_text(json.dumps(overlay, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(
        f"Compiled Crystal runtime activation OK: {activated}/{EXPECTED_RUNTIME_ROUTES} routed spells bound; "
        f"{audit['runtimeActivation']['nativeMagicInfoRowsReused']} native MagicInfo rows reused; "
        f"{source_stubs} source stub retained; 0 pending runtime rows"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
