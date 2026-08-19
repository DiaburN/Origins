#!/usr/bin/env python3
"""Strict gate for CompanionDialog's target-typed deterministic bonus rows."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

LEVELS = (3, 5, 7, 10, 11, 13, 15)


def props(control: dict | None) -> dict:
    return (control or {}).get("properties") or {}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--zircon-root", type=Path, required=True)
    args = parser.parse_args()

    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    window = next((w for w in spec.get("windows", []) if w.get("field") == "CompanionBox"), None)
    if window is None:
        raise SystemExit("CompanionBox missing")
    contract = window.get("deterministicCompanionBonusRows") or {}
    expected = {
        "passed": True,
        "rows": 7,
        "childrenPerRow": 2,
        "controlsAdded": 21,
        "levels": list(LEVELS),
        "rowHeight": 57,
        "firstY": 5,
        "scrollMax": 414,
        "runtimeBonusStatsInvented": False,
        "runtimeBonusTextInvented": False,
        "targetTypedNewSource": True,
    }
    for key, value in expected.items():
        if contract.get(key) != value:
            raise SystemExit(f"Companion bonus contract drifted: {key}={contract.get(key)!r}, expected {value!r}")

    by = {str(control.get("name") or ""): control for control in window.get("controls", [])}
    for index, level in enumerate(LEVELS):
        row_name = f"CompanionBonusStatSource{index + 1:02d}"
        row = by.get(row_name)
        if row is None or row.get("sourceType") != "CompanionBonusStat":
            raise SystemExit(f"Companion bonus source row missing: {row_name}")
        p = props(row)
        if p.get("Parent") != "BonusControl" or p.get("Size") != "new Size(215, 57)":
            raise SystemExit(f"Companion bonus source row geometry drifted: {row_name} -> {p}")
        if p.get("Location") != f"new Point(0, {5 + index * 57})" or p.get("Index") != str(index) or p.get("Level") != str(level):
            raise SystemExit(f"Companion bonus source row sequence drifted: {row_name} -> {p}")
        for suffix in ("LevelLabel", "StatLabel"):
            label = by.get(f"{row_name}{suffix}")
            if label is None or label.get("type") != "DXLabel":
                raise SystemExit(f"Companion bonus constructor label missing: {row_name}{suffix}")
            if props(label).get("Parent") != row_name:
                raise SystemExit(f"Companion bonus constructor label parent drifted: {row_name}{suffix}")
            if label.get("resolvedText") not in ("", None):
                raise SystemExit(f"Fabricated companion bonus text leaked: {row_name}{suffix}={label.get('resolvedText')!r}")

    generated = [
        control for control in window.get("controls", [])
        if str(control.get("sourceGenerated") or "").startswith("deterministic-companion-bonus:")
    ]
    if len(generated) != 21:
        raise SystemExit(f"Companion bonus generated control count drifted: {len(generated)}")
    if any(control.get("runtimePayloadInvented") is not False for control in generated):
        raise SystemExit("Companion bonus pass introduced runtime payloads")

    scroll = by.get("BonusScrollBar")
    if scroll is None:
        raise SystemExit("Companion BonusScrollBar missing from base source controls")

    spec["companionBonusRowAudit"] = {
        "passed": True,
        "rows": 7,
        "deterministicControls": 21,
        "targetTypedNewSource": True,
        "runtimeBonusStatsInvented": False,
        "runtimeBonusTextInvented": False,
    }
    args.spec.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("Companion bonus row audit: PASS (7 rows / 21 controls; no live stats)")


if __name__ == "__main__":
    main()
