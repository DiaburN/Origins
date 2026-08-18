#!/usr/bin/env python3
"""Final supplemental manifest matrix gate.

Runs last (audit_zz_*) after all source augmenters/auditors. This keeps the
promoter/build contract authoritative even if a workflow's reporting assertions
lag a commit behind. It never alters controls; it only records/validates the
current desktop source-fidelity floor and critical runtime-neutral boundaries.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--zircon-root", type=Path, required=True)
    args = parser.parse_args()

    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    by = {window.get("field"): window for window in spec.get("windows", [])}
    game_controls = sum(len(window.get("controls", [])) for window in spec.get("windows", []))
    nested_controls = sum(len(window.get("controls", [])) for window in spec.get("nestedWindows", []))

    failures: list[str] = []
    if len(spec.get("windows", [])) != 65:
        failures.append(f"GameScene inventory {len(spec.get('windows', []))} != 65")
    if len(spec.get("nestedWindows", [])) != 15:
        failures.append(f"nested inventory {len(spec.get('nestedWindows', []))} != 15")
    if game_controls < 2466:
        failures.append(f"GameScene control floor regressed: {game_controls} < 2466")
    if nested_controls < 143:
        failures.append(f"nested control floor regressed: {nested_controls} < 143")

    anonymous = spec.get("anonymousConstructorControlAudit") or {}
    if anonymous.get("passed") is not True:
        failures.append(f"anonymous constructor audit missing/not PASS: {anonymous}")
    if anonymous.get("parserSyntheticSmokePassed") is not True:
        failures.append(f"anonymous parser synthetic smoke missing/not PASS: {anonymous}")
    if anonymous.get("sourceAnonymousControls") != anonymous.get("manifestAnonymousControls"):
        failures.append(f"anonymous source/manifest count mismatch: {anonymous}")
    if anonymous.get("tradeAnonymousGoldLabels") != 2:
        failures.append(f"Trade anonymous Gold contract drifted: {anonymous}")
    if anonymous.get("controlsFabricatedByAudit") is not False or anonymous.get("runtimePayloadsInvented") is not False:
        failures.append(f"anonymous audit runtime/fabrication boundary broken: {anonymous}")

    custom = spec.get("customCompositeInventory") or {}
    if custom.get("passed") is not True or custom.get("version") != 2:
        failures.append(f"custom composite inventory missing/not v2 PASS: {custom}")
    if custom.get("constructorAndHelperReachability") is not True or custom.get("eventCallbacksExcluded") is not True:
        failures.append(f"custom composite reachability boundary broken: {custom}")
    if custom.get("controlsFabricatedByAudit") is not False or custom.get("runtimePayloadsInvented") is not False:
        failures.append(f"custom composite audit fabricated state: {custom}")

    direct = spec.get("directCustomCompositeInventory") or {}
    if direct.get("passed") is not True or direct.get("unresolvedDeterministic") != []:
        failures.append(f"direct custom composite inventory incomplete: {direct}")

    rows = spec.get("deterministicSourceRowAudit") or {}
    if rows.get("passed") is not True:
        failures.append("deterministic row audit missing/not PASS")
    expected_rows = {"rankingRows": 12, "dungeonRows": 9, "fortuneRows": 9, "bigMapRows": 48}
    for key, value in expected_rows.items():
        if rows.get(key) != value:
            failures.append(f"deterministic {key}={rows.get(key)!r}, expected {value}")

    checks = (
        ("Guild member rows", spec.get("guildMemberRowAudit"), "passed", True),
        ("Guild root helpers", spec.get("guildRootHelperAudit"), "passed", True),
        ("GameStore", spec.get("gameStoreCompositeAudit"), "passed", True),
        ("Communication", spec.get("communicationReceivedRowAudit"), "passed", True),
        ("Consignment", spec.get("consignmentCompositeAudit"), "passed", True),
        ("Consignment headers", spec.get("consignmentHeaderHelperAudit"), "passed", True),
        ("Currency", spec.get("currencyArrayControlAudit"), "passed", True),
        ("UI helper inventory", spec.get("uiCreationHelperInventory"), "passed", True),
        ("source search flows", spec.get("sourceSearchFlowAudit"), "passed", True),
        ("literal asset refs", spec.get("supplementalLiteralAssetRefPass"), "passed", True),
    )
    for label, report, key, expected in checks:
        if not isinstance(report, dict) or report.get(key) is not expected:
            failures.append(f"{label} audit missing/not PASS: {report}")

    group_lfg = (by.get("GroupBox") or {}).get("groupLFGRowAudit") or {}
    if group_lfg.get("passed") is not True or group_lfg.get("rows") != 5 or group_lfg.get("runtimeLfgInvented") is not False:
        failures.append(f"Group LFG audit incomplete: {group_lfg}")

    consignment = spec.get("consignmentCompositeAudit") or {}
    if consignment.get("version") != 2 or consignment.get("deterministicControls") != 135 or consignment.get("itemTypeButtons") != 38:
        failures.append(f"Consignment v2 matrix drifted: {consignment}")
    header = spec.get("consignmentHeaderHelperAudit") or {}
    if header.get("deterministicControls") != 10 or header.get("duplicateControls") != 0:
        failures.append(f"Consignment header compatibility matrix drifted: {header}")

    currency = spec.get("currencyArrayControlAudit") or {}
    if currency.get("deterministicArrayControls") != 4 or currency.get("controlsAdded") != 4 or currency.get("rowSpacing") != 40:
        failures.append(f"Currency deterministic array matrix drifted: {currency}")

    helpers = spec.get("uiCreationHelperInventory") or {}
    helper_flags = (
        "knownBigMapHelpersMaterialized",
        "chatOptionsAddNewTabDeferredLocal",
        "helpPagesRemainRuntimeBound",
        "magicTabsRemainRuntimeBound",
        "guildConstructorHelpersMaterialized",
        "guildWarRuntimeCastlePanelsRemainNeutral",
        "eventCallbacksExcludedFromCreationClassification",
        "staticGlobalsDoNotImplyRuntimeData",
    )
    if helpers.get("version") != 2:
        failures.append(f"UI helper inventory version drifted: {helpers.get('version')}")
    for flag in helper_flags:
        if helpers.get(flag) is not True:
            failures.append(f"UI helper inventory flag missing: {flag}")
    if helpers.get("controlsFabricatedByAudit") is not False or helpers.get("runtimePayloadsInvented") is not False:
        failures.append("UI helper inventory fabricated controls/runtime payloads")

    report = {
        "passed": not failures,
        "gameSceneWindows": len(spec.get("windows", [])),
        "nestedWindows": len(spec.get("nestedWindows", [])),
        "gameSceneControls": game_controls,
        "nestedControls": nested_controls,
        "minimumGameSceneControls": 2466,
        "minimumNestedControls": 143,
        "anonymousSourceControls": anonymous.get("sourceAnonymousControls"),
        "anonymousManifestControls": anonymous.get("manifestAnonymousControls"),
        "runtimePayloadsInvented": False,
        "controlsFabricatedByGate": False,
        "failures": failures,
    }
    spec["finalSupplementalSourceMatrix"] = report
    args.spec.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if failures:
        raise SystemExit("Final supplemental source matrix failed:\n- " + "\n- ".join(failures))
    print(
        "Final supplemental source matrix: PASS -> "
        f"65+15 windows, {game_controls}+{nested_controls} controls, anonymous={anonymous.get('manifestAnonymousControls')}"
    )


if __name__ == "__main__":
    main()
