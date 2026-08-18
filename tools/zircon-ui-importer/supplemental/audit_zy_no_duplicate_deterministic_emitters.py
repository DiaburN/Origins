#!/usr/bin/env python3
"""Reject known legacy/modern deterministic UI duplication.

Several source-fidelity passes evolved from narrow family emitters into complete
composite owners. Legacy scripts stay executable for source compatibility, but
must emit zero controls. This late audit locks one owner/identity per family so
control floors cannot be inflated by duplicate UI.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--zircon-root", type=Path, required=True)
    args = parser.parse_args()

    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    by = {window.get("field"): window for window in spec.get("windows", [])}
    failures: list[str] = []

    consignment = by.get("ConsignmentBox") or {}
    consignment_controls = consignment.get("controls") or []
    legacy_consignment = [
        str(control.get("name") or "") for control in consignment_controls
        if str(control.get("sourceGenerated") or "").startswith("deterministic-consignment:")
        or str(control.get("sourceGenerated") or "").startswith("deterministic-consignment-headers:")
    ]
    modern_consignment = [
        str(control.get("name") or "") for control in consignment_controls
        if str(control.get("sourceGenerated") or "").startswith("deterministic-consignment-v2:")
    ]
    legacy_consignment_report = consignment.get("legacyConsignmentCompositeCompatibility") or {}
    header_compat = consignment.get("consignmentHeaderCompatibility") or {}
    if legacy_consignment:
        failures.append(f"legacy Consignment controls remain: {legacy_consignment[:30]}")
    if len(modern_consignment) != 135:
        failures.append(f"authoritative Consignment v2 controls {len(modern_consignment)} != 135")
    if legacy_consignment_report.get("passed") is not True or legacy_consignment_report.get("legacyControlsEmitted") != 0:
        failures.append(f"legacy Consignment compatibility incomplete: {legacy_consignment_report}")
    if header_compat.get("passed") is not True or header_compat.get("controlsAddedByCompatibilityPass") != 0:
        failures.append(f"Consignment header compatibility incomplete: {header_compat}")

    currency = by.get("CurrencyBox") or {}
    currency_controls = currency.get("controls") or []
    legacy_currency = [
        str(control.get("name") or "") for control in currency_controls
        if str(control.get("sourceGenerated") or "").startswith("deterministic-currency:CurrencyDialog constructor loop")
    ]
    modern_currency = [
        str(control.get("name") or "") for control in currency_controls
        if str(control.get("sourceGenerated") or "").startswith("deterministic-currency-array:CurrencyDialog constructor array loop")
    ]
    currency_compat = currency.get("legacyCurrencyRowCompatibility") or {}
    if legacy_currency:
        failures.append(f"legacy Currency controls remain: {legacy_currency}")
    if len(modern_currency) != 4:
        failures.append(f"authoritative Currency array controls {len(modern_currency)} != 4")
    if currency_compat.get("passed") is not True or currency_compat.get("legacyControlsEmitted") != 0:
        failures.append(f"legacy Currency compatibility incomplete: {currency_compat}")

    # Identity uniqueness is strict for every final window. Repeated C# source
    # data may share visible text, but two controls may not share manifest names.
    duplicate_names: dict[str, list[str]] = {}
    for window in [*(spec.get("windows") or []), *(spec.get("nestedWindows") or [])]:
        names = [str(control.get("name") or "") for control in window.get("controls", [])]
        duplicates = sorted(name for name, count in Counter(names).items() if name and count > 1)
        if duplicates:
            duplicate_names[str(window.get("field") or window.get("id"))] = duplicates
    if duplicate_names:
        failures.append(f"duplicate manifest control identities: {duplicate_names}")

    report = {
        "passed": not failures,
        "consignmentLegacyControls": len(legacy_consignment),
        "consignmentAuthoritativeControls": len(modern_consignment),
        "currencyLegacyControls": len(legacy_currency),
        "currencyAuthoritativeControls": len(modern_currency),
        "duplicateControlIdentityWindows": duplicate_names,
        "runtimePayloadsInvented": False,
        "controlsFabricatedByAudit": False,
        "failures": failures,
    }
    spec["duplicateDeterministicEmitterAudit"] = report
    args.spec.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if failures:
        raise SystemExit("Duplicate deterministic emitter audit failed:\n- " + "\n- ".join(failures))
    print("Duplicate deterministic emitter audit: PASS -> Consignment=135 unique; Currency=4 unique; duplicate names=0")


if __name__ == "__main__":
    main()
