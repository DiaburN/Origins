#!/usr/bin/env python3
"""Refine the UI-helper inventory around structural creation vs event callbacks.

The first helper inventory established constructor/deferred coverage. This final
pass deliberately evaluates *creation-time* code with event lambda bodies
masked, so a deterministic panel is not labelled runtime merely because its
MouseClick callback later sends a packet. Static Globals constants also do not
make structural UI runtime data. Data-backed `.Binding` loops still do.

Known custom composites may be flattened into their exact DX base-control tree
by an earlier source-backed materializer. Those helpers are counted as
materialized only when the complete, named flattened tree still matches the
strict source contract.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path

from audit_ui_creation_helper_inventory import (
    calls,
    class_body,
    constructor_body,
    constructor_reachability,
    created_types,
    methods,
    named_creations,
    strip_event_lambdas,
)


RUNTIME_PATTERNS = (
    r"\.Binding\b",
    r"\bMapObject\.(?:User|Objects|ObjectsByLocation)\b",
    r"\bSelectedInfo\b",
    r"\bDataDictionary\b",
    r"\bRankInfo\b",
    r"\bInstanceInfo\b",
    r"\bHelpInfo\b",
    r"\bHelpItemInfo\b",
    r"\bMagicInfo\b",
    r"\bClientUserMagic\b",
    r"\bMonsterObject\b",
    r"\bNPCInfo\b",
    r"\bClientObjectData\b",
)

BIGMAP_FLATTENED_SOURCE = (
    "deterministic-rows:BigMapDialog CreateRows/CreateScrollBar + "
    "BigMapListRow constructor"
)


def external_runtime_bound(structural_chunk: str) -> bool:
    return any(re.search(pattern, structural_chunk) for pattern in RUNTIME_PATTERNS)


def flattened_bigmap_names(window: dict, helper: str) -> set[str]:
    """Recognize only the exact source-backed BigMap helper trees.

    BigMapListRow is a custom DXControl, so the neutral manifest deliberately
    flattens each instance to a DXControl + NameLabel pair. Local C# names
    (`rows`/`row`) therefore cannot match manifest names directly. Keep this
    recognition narrow and fail closed if the source-derived contract changes.
    """
    if window.get("field") != "BigMapBox" or helper not in {"CreateRows", "CreateScrollBar"}:
        return set()

    contract = window.get("deterministicBigMapRows") or {}
    if (
        contract.get("npcRows") != 24
        or contract.get("monsterRows") != 24
        or contract.get("neutralVisible") is not False
        or any(
            contract.get(key) is not False
            for key in ("runtimeMapInfoInvented", "runtimeNPCsInvented", "runtimeMonstersInvented")
        )
    ):
        return set()

    controls = {str(control.get("name") or ""): control for control in window.get("controls") or []}

    if helper == "CreateRows":
        expected: list[str] = []
        for prefix in ("BigMapNPCRowSource", "BigMapMonsterRowSource"):
            for index in range(1, 25):
                row_name = f"{prefix}{index:02d}"
                label_name = f"{row_name}NameLabel"
                row = controls.get(row_name)
                label = controls.get(label_name)
                if row is None or label is None:
                    return set()
                if row.get("type") != "DXControl" or label.get("type") != "DXLabel":
                    return set()
                if str(row.get("sourceGenerated") or "") != BIGMAP_FLATTENED_SOURCE:
                    return set()
                if str(label.get("sourceGenerated") or "") != BIGMAP_FLATTENED_SOURCE:
                    return set()
                if str((row.get("properties") or {}).get("Visible") or "") != "false":
                    return set()
                if label.get("resolvedText") not in ("", None):
                    return set()
                expected.extend((row_name, label_name))
        return set(expected) if len(expected) == 96 else set()

    expected = {"NPCScrollBar", "MonsterScrollBar"}
    for name in expected:
        control = controls.get(name)
        if control is None or control.get("type") != "DXVScrollBar":
            return set()
        if str(control.get("sourceGenerated") or "") != BIGMAP_FLATTENED_SOURCE:
            return set()
        if str((control.get("properties") or {}).get("Change") or "") != "1":
            return set()
    return expected


def materialized_names(window: dict, helper: str, named: list[str]) -> list[str]:
    controls = window.get("controls") or []
    control_names = {str(control.get("name") or "") for control in controls}
    found = {name for name in named if name in control_names}

    helper_marker = f"helper:{helper}"
    owned_tabs = {
        str(control.get("name") or "")
        for control in controls
        if str(control.get("customTabSource") or "") == helper_marker
    }
    for control in controls:
        name = str(control.get("name") or "")
        generated = str(control.get("sourceGenerated") or "")
        if f".{helper}" in generated or generated.endswith(helper):
            found.add(name)
        if str(control.get("customTabSource") or "") == helper_marker:
            found.add(name)
        if str(control.get("compositeOwner") or "") in owned_tabs:
            found.add(name)

    found.update(flattened_bigmap_names(window, helper))
    return sorted(value for value in found if value)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--zircon-root", type=Path, required=True)
    args = parser.parse_args()

    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    rows: list[dict] = []
    source_contracts: dict[str, dict] = {}

    for window in [*(spec.get("windows") or []), *(spec.get("nestedWindows") or [])]:
        source_path = str(window.get("sourcePath") or "")
        source_class = str(window.get("class") or window.get("sourceClass") or "")
        path = args.zircon_root / source_path
        if not source_path or not source_class or not path.exists():
            continue

        source_text = path.read_text(encoding="utf-8-sig")
        body = class_body(source_text, source_class)
        ctor = constructor_body(body, source_class)
        method_map = methods(body)
        if not ctor or not method_map:
            continue

        reach_depth = constructor_reachability(ctor, method_map)
        source_contracts[source_class] = {
            "immediateConstructorHelpers": sorted(name for name, depth in reach_depth.items() if depth == 1),
            "constructorReachableHelpers": sorted(reach_depth),
        }

        for helper in sorted(method_map):
            complete = "\n".join(method_map.get(helper) or [])
            structural = strip_event_lambdas(complete)
            structural_types = created_types(structural)
            if not structural_types:
                continue
            all_types = created_types(complete)
            callback_only_types = sorted(set(all_types) - set(structural_types))
            named = named_creations(structural)
            materialized = materialized_names(window, helper, named)
            reachable = helper in reach_depth
            runtime_data = external_runtime_bound(structural)

            if reachable:
                classification = "runtime-bound" if runtime_data else "deterministic-source"
                status = "materialized" if materialized else (
                    "runtime-bound" if runtime_data else "audited-source-only"
                )
            else:
                classification = "deferred-runtime" if runtime_data else "deferred-local-state"
                status = "audited-deferred-runtime" if runtime_data else "audited-deferred-local"

            rows.append({
                "id": window.get("id"),
                "field": window.get("field"),
                "sourceClass": source_class,
                "sourcePath": source_path,
                "helper": helper,
                "constructorReachable": reachable,
                "constructorReachDepth": reach_depth.get(helper),
                "deferredUntilCalled": not reachable,
                "createdTypes": structural_types,
                "callbackOnlyCreatedTypes": callback_only_types,
                "namedCreations": named,
                "materializedControlNames": materialized,
                "externalRuntimeData": runtime_data,
                "classification": classification,
                "status": status,
                "eventCallbacksExcludedFromCreationClassification": True,
                "staticGlobalsDoNotImplyRuntimeData": True,
                "sourceBackedOnly": True,
            })

    def rows_for(source_class: str) -> dict[str, dict]:
        return {row["helper"]: row for row in rows if row["sourceClass"] == source_class}

    # BigMap fixed helper construction: source rows/scrollbars are deterministic,
    # final layout/data waits for SelectedInfo. BigMapListRow is flattened into
    # its exact DXControl + NameLabel tree, so require the independent strict row
    # audit before accepting that helper as materialized.
    bigmap = rows_for("BigMapDialog")
    required_bigmap = {"CreateSidePanel", "CreateRows", "CreateScrollBar"}
    if not required_bigmap.issubset(bigmap):
        raise SystemExit(f"BigMap helper inventory incomplete: {sorted(required_bigmap - set(bigmap))}")
    bigmap_row_audit = spec.get("deterministicSourceRowAudit") or {}
    if bigmap_row_audit.get("passed") is not True or bigmap_row_audit.get("bigMapRows") != 48:
        raise SystemExit(f"BigMap flattened row audit missing/not exact: {bigmap_row_audit}")
    for helper in required_bigmap:
        if not bigmap[helper]["constructorReachable"]:
            raise SystemExit(f"BigMap {helper} lost constructor reachability")
    for helper in ("CreateRows", "CreateScrollBar"):
        if bigmap[helper]["classification"] != "deterministic-source" or bigmap[helper]["status"] != "materialized":
            raise SystemExit(f"BigMap {helper} materialization drifted: {bigmap[helper]}")
    if len(bigmap["CreateRows"]["materializedControlNames"]) != 96:
        raise SystemExit(f"BigMap CreateRows flattened tree incomplete: {bigmap['CreateRows']}")
    if set(bigmap["CreateScrollBar"]["materializedControlNames"]) != {"NPCScrollBar", "MonsterScrollBar"}:
        raise SystemExit(f"BigMap CreateScrollBar flattened tree incomplete: {bigmap['CreateScrollBar']}")

    # Chat Options: callback-created local user tab, never initial constructor UI.
    chat = rows_for("ChatOptionsDialog")
    add_tab = chat.get("AddNewTab")
    if not add_tab or add_tab["constructorReachable"]:
        raise SystemExit(f"ChatOptions.AddNewTab constructor boundary drifted: {add_tab}")
    if add_tab["classification"] != "deferred-local-state" or add_tab["status"] != "audited-deferred-local":
        raise SystemExit(f"ChatOptions.AddNewTab must remain deferred local state: {add_tab}")
    if not {"ChatOptionsPanel", "DXListBoxItem", "DXTabControl", "ChatTab"}.issubset(set(add_tab["createdTypes"])):
        raise SystemExit(f"ChatOptions.AddNewTab source template incomplete: {add_tab}")

    # Help and Magic remain data-backed because their creation loops enumerate
    # source model collections via Binding.
    help_row = rows_for("HelpDialog").get("Add")
    if not help_row or not help_row["constructorReachable"] or help_row["classification"] != "runtime-bound":
        raise SystemExit(f"HelpDialog.Add runtime boundary drifted: {help_row}")
    if "HelpContainer" not in help_row["createdTypes"]:
        raise SystemExit(f"HelpDialog.Add source-created HelpContainer missing: {help_row}")

    magic_row = rows_for("MagicDialog").get("CreateTabs")
    if not magic_row or magic_row["constructorReachable"]:
        raise SystemExit(f"MagicDialog.CreateTabs constructor boundary drifted: {magic_row}")
    if magic_row["classification"] != "deferred-runtime" or magic_row["status"] != "audited-deferred-runtime":
        raise SystemExit(f"MagicDialog.CreateTabs runtime boundary drifted: {magic_row}")
    if not {"MagicTab", "MagicCell"}.issubset(set(magic_row["createdTypes"])):
        raise SystemExit(f"MagicDialog.CreateTabs source-created controls drifted: {magic_row}")

    # Guild: seven Create*Tab helpers are called by the constructor. Six are
    # structurally deterministic. CreateWarTab is intentionally mixed because it
    # additionally loops over CEnvir.CastleInfoList.Binding; its deterministic
    # WarPanel/StartWarButton are materialised, but GuildCastlePanel rows are not.
    guild = rows_for("GuildDialog")
    guild_helpers = {
        "CreateCreateTab", "CreateHomeTab", "CreateMemberTab", "CreateStorageTab",
        "CreateWarTab", "CreateStyleTab", "CreateCastleTab",
    }
    if not guild_helpers.issubset(guild):
        raise SystemExit(f"Guild helper inventory incomplete: {sorted(guild_helpers - set(guild))}")
    deterministic_guild = guild_helpers - {"CreateWarTab"}
    for helper in deterministic_guild:
        row = guild[helper]
        if not row["constructorReachable"] or row["classification"] != "deterministic-source":
            raise SystemExit(f"Guild deterministic helper misclassified: {helper} -> {row}")
        if row["status"] != "materialized":
            raise SystemExit(f"Guild deterministic helper not materialized: {helper} -> {row}")
    war = guild["CreateWarTab"]
    if not war["constructorReachable"] or war["classification"] != "runtime-bound" or war["status"] != "materialized":
        raise SystemExit(f"Guild CreateWarTab mixed source/runtime contract drifted: {war}")
    if "GuildCastlePanel" not in war["createdTypes"] or not {"WarPanel", "StartWarButton"}.issubset(set(war["materializedControlNames"])):
        raise SystemExit(f"Guild CreateWarTab structure/runtime split incomplete: {war}")
    guild_window = next(w for w in spec.get("windows", []) if w.get("field") == "GuildBox")
    if any(control.get("sourceType") == "GuildCastlePanel" for control in guild_window.get("controls", [])):
        raise SystemExit("Guild runtime CastleInfo panels were materialized in neutral manifest")

    counts = Counter(row["classification"] for row in rows)
    statuses = Counter(row["status"] for row in rows)
    deferred = [row for row in rows if row["deferredUntilCalled"]]
    report = {
        "passed": True,
        "version": 2,
        "helperCount": len(rows),
        "deferredHelperCount": len(deferred),
        "classificationCounts": dict(counts),
        "statusCounts": dict(statuses),
        "rows": rows,
        "sourceContracts": source_contracts,
        "knownBigMapHelpers": sorted(required_bigmap),
        "knownBigMapHelpersMaterialized": True,
        "chatOptionsAddNewTabDeferredLocal": True,
        "helpPagesRemainRuntimeBound": True,
        "magicTabsRemainRuntimeBound": True,
        "guildConstructorHelpersMaterialized": True,
        "guildWarRuntimeCastlePanelsRemainNeutral": True,
        "eventCallbacksExcludedFromConstructorReachability": True,
        "eventCallbacksExcludedFromCreationClassification": True,
        "staticGlobalsDoNotImplyRuntimeData": True,
        "controlsFabricatedByAudit": False,
        "runtimePayloadsInvented": False,
        "sourceBackedOnly": True,
    }
    spec["uiCreationHelperInventory"] = report
    args.spec.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(
        "UI creation helper inventory v2: PASS -> "
        f"helpers={len(rows)} deferred={len(deferred)} classifications={dict(counts)} statuses={dict(statuses)}"
    )


if __name__ == "__main__":
    main()
