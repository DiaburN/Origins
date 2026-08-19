#!/usr/bin/env python3
"""Strict gate for CurrencyDialog's source-created CurrencyTree shell."""
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
    window = next((w for w in spec.get("windows", []) if w.get("field") == "CurrencyBox"), None)
    if window is None:
        raise SystemExit("CurrencyBox missing")
    contract = window.get("deterministicCurrencyTree") or {}
    expected = {
        "passed": True,
        "controlsAdded": 2,
        "treeShells": 1,
        "scrollbars": 1,
        "runtimeHeadersInvented": False,
        "runtimeCurrencyItemsInvented": False,
        "runtimeCurrencyDataInvented": False,
        "sourceClientSize": [227, 302],
    }
    for key, value in expected.items():
        if contract.get(key) != value:
            raise SystemExit(f"Currency tree contract drifted: {key}={contract.get(key)!r}, expected {value!r}")

    by = {str(control.get("name") or ""): control for control in window.get("controls", [])}
    tree = by.get("CurrencyTreeSource")
    scroll = by.get("CurrencyTreeSourceScrollBar")
    if tree is None or tree.get("sourceType") != "CurrencyTree":
        raise SystemExit("CurrencyTree source shell missing")
    p = props(tree)
    if p.get("Parent") != "this" or p.get("Location") != "ClientArea.Location" or p.get("Size") != "ClientArea.Size":
        raise SystemExit(f"CurrencyTree exact ClientArea geometry drifted: {p}")
    if p.get("Border") != "true" or p.get("BorderColour") != "Constants.PrimaryColour":
        raise SystemExit(f"CurrencyTree source border contract drifted: {p}")

    s = props(scroll)
    if s.get("Parent") != "CurrencyTreeSource" or s.get("Change") != "22":
        raise SystemExit(f"CurrencyTree scrollbar parent/change drifted: {s}")
    if s.get("Size") != "new Size(14, CurrencyTreeSource.Size.Height)" or s.get("Location") != "new Point(CurrencyTreeSource.Size.Width - 14, 0)":
        raise SystemExit(f"CurrencyTree scrollbar OnSizeChanged geometry drifted: {s}")
    if s.get("VisibleSize") != "CurrencyTreeSource.Size.Height" or s.get("MaxValue") != "0":
        raise SystemExit(f"CurrencyTree neutral scrollbar range drifted: {s}")

    generated = [
        control for control in window.get("controls", [])
        if str(control.get("sourceGenerated") or "").startswith("deterministic-currency-tree:")
    ]
    if len(generated) != 2 or any(control.get("runtimePayloadInvented") is not False for control in generated):
        raise SystemExit("Currency tree generated source shell count/payload contract drifted")
    if any(control.get("sourceType") in {"CurrencyTreeHeader", "CurrencyItem"} for control in window.get("controls", [])):
        raise SystemExit("Currency runtime user rows were pre-created")

    spec["currencyTreeAudit"] = {
        "passed": True,
        "deterministicControls": 2,
        "runtimeHeadersInvented": False,
        "runtimeCurrencyItemsInvented": False,
        "runtimeCurrencyDataInvented": False,
    }
    args.spec.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("Currency tree audit: PASS (2 deterministic controls; no user currency rows)")


if __name__ == "__main__":
    main()
