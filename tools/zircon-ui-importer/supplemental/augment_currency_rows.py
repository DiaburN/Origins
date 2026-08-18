#!/usr/bin/env python3
"""Legacy compatibility pass for CurrencyDialog deterministic rows.

The authoritative source expansion is augment_currency_array_controls.py and is
strictly verified by audit_currency_array_controls.py. The supplemental runner
executes every augment_*.py, so this older emitter must not add a second set of
four CurrencyRow controls.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def assert_source(root: Path) -> None:
    text = (root / "Client/Scenes/Views/CurrencyDialog.cs").read_text(encoding="utf-8-sig")
    for needle in (
        "CurrencyRow[] CurrencyRows;",
        "CurrencyRows = new CurrencyRow[4];",
        "CurrencyRows[i] = new CurrencyRow",
        "Location = new Point(10, 35 + i * 40)",
        "public sealed class CurrencyRow : DXControl",
    ):
        if needle not in text:
            raise SystemExit(f"Legacy Currency source compatibility changed: missing {needle!r}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--zircon-root", type=Path, required=True)
    args = parser.parse_args()

    assert_source(args.zircon_root)
    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    window = next((w for w in spec.get("windows", []) if w.get("field") == "CurrencyBox"), None)
    if window is None:
        raise SystemExit("CurrencyBox missing from manifest")

    authoritative = window.get("currencyArrayControlPass") or {}
    if authoritative.get("passed") is not True or authoritative.get("controlsAdded") != 4:
        raise SystemExit(f"Authoritative Currency array pass must run before legacy compatibility gate: {authoritative}")

    legacy = [
        str(control.get("name") or "")
        for control in window.get("controls", [])
        if str(control.get("sourceGenerated") or "").startswith("deterministic-currency:CurrencyDialog constructor loop")
    ]
    if legacy:
        raise SystemExit(f"Legacy duplicate Currency rows remain before compatibility gate: {legacy}")

    window["legacyCurrencyRowCompatibility"] = {
        "passed": True,
        "legacyControlsEmitted": 0,
        "authoritativeOwner": "augment_currency_array_controls.py",
        "duplicateRowsInvented": False,
    }
    args.spec.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("Legacy Currency row compatibility: PASS -> emitted=0; authoritative rows=4")


if __name__ == "__main__":
    main()
