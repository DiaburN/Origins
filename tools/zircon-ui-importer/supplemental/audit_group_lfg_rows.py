#!/usr/bin/env python3
"""Strict gate for GroupDialog's five deterministic LFG rows."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def props(control: dict | None) -> dict:
    return (control or {}).get("properties") or {}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--zircon-root", type=Path, required=True)
    args = parser.parse_args()

    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    group = next((w for w in spec.get("windows", []) if w.get("field") == "GroupBox"), None)
    if group is None:
        raise SystemExit("GroupBox missing")
    contract = group.get("deterministicGroupLFGRows") or {}
    expected = {
        "passed": True,
        "rows": 5,
        "controlsAdded": 20,
        "rowSize": [194, 19],
        "rowStep": 21,
        "neutralVisible": False,
        "runtimeLfgInvented": False,
        "runtimeGroupNamesInvented": False,
        "runtimeCountsInvented": False,
        "runtimeTypesInvented": False,
    }
    for key, value in expected.items():
        if contract.get(key) != value:
            raise SystemExit(f"Group LFG row contract drifted: {key}={contract.get(key)!r}, expected {value!r}")

    by = {str(control.get("name") or ""): control for control in group.get("controls", [])}
    labels = {
        "NameLabel": ("new Point(0, 0)", "new Size(100, 20)", "Color.White"),
        "StatusLabel": ("new Point(101, 0)", "new Size(50, 20)", "Color.Lime"),
        "TypeLabel": ("new Point(151, 0)", "new Size(42, 20)", "Color.Lime"),
    }
    for i in range(5):
        row_name = f"GroupLFGRowSource{i + 1:02d}"
        row = by.get(row_name)
        if row is None or row.get("sourceType") != "GroupLFGRow":
            raise SystemExit(f"Group LFG row missing: {row_name}")
        p = props(row)
        if p.get("Location") != f"new Point(13, {293 + i * 21})" or p.get("Size") != "new Size(194, 19)":
            raise SystemExit(f"Group LFG row geometry drifted: {row_name} -> {p}")
        if p.get("Visible") != "false" or p.get("Selected") != "false":
            raise SystemExit(f"Group LFG neutral row state drifted: {row_name} -> {p}")
        if "null in neutral reference" not in str(p.get("RuntimeInfo") or ""):
            raise SystemExit(f"Group LFG runtime Info boundary missing: {row_name}")
        for suffix, (location, size, colour) in labels.items():
            label = by.get(f"{row_name}{suffix}")
            if label is None:
                raise SystemExit(f"Group LFG row child missing: {row_name}{suffix}")
            lp = props(label)
            if lp.get("Location") != location or lp.get("Size") != size or lp.get("ForeColour") != colour:
                raise SystemExit(f"Group LFG label source geometry/style drifted: {row_name}{suffix} -> {lp}")
            if label.get("resolvedText") not in ("", None):
                raise SystemExit(f"Fabricated Group LFG data leaked: {row_name}{suffix}")

    generated = [
        control for control in group.get("controls", [])
        if str(control.get("sourceGenerated") or "").startswith("deterministic-group-lfg:")
    ]
    if len(generated) != 20:
        raise SystemExit(f"Group LFG generated control count drifted: {len(generated)}")
    if any(control.get("runtimePayloadInvented") is not False for control in generated):
        raise SystemExit("Group LFG supplemental introduced runtime payloads")

    group["groupLFGRowAudit"] = {
        "passed": True,
        "rows": 5,
        "deterministicControls": 20,
        "runtimeLfgInvented": False,
    }
    args.spec.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("Group LFG row audit: PASS (5 rows / 20 controls, no LFG data)")


if __name__ == "__main__":
    main()
