#!/usr/bin/env python3
"""Materialise CurrencyDialog's deterministic CurrencyTree shell.

CurrencyDialog always constructs CurrencyTree and CurrencyTree always constructs
its scrollbar. Category headers and currency items are created later by
ListChanged() from GameScene.Game.User.Currencies, so they remain absent in the
neutral desktop reference.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

PREFIX = "deterministic-currency-tree:"


def make(name: str, type_name: str, properties: dict[str, str], *, source_type: str | None = None) -> dict:
    control = {
        "name": name,
        "type": type_name,
        "properties": dict(properties),
        "sourceGenerated": PREFIX + "CurrencyDialog/CurrencyTree constructor",
        "runtimePayloadInvented": False,
    }
    if source_type:
        control["sourceType"] = source_type
    return control


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--zircon-root", type=Path, required=True)
    args = parser.parse_args()

    source = (args.zircon_root / "Client/Scenes/Views/CurrencyDialog.cs").read_text(encoding="utf-8-sig")
    needles = (
        "SetClientSize(new Size(227, 7 * 43 + 1));",
        "BindTree = new CurrencyTree",
        "Location = new Point(ClientArea.X, ClientArea.Y)",
        "Size = new Size(ClientArea.Width, ClientArea.Height)",
        "public class CurrencyTree : DXControl",
        "Border = true;",
        "BorderColour = Constants.PrimaryColour;",
        "ScrollBar = new DXVScrollBar",
        "Change = 22",
        "ScrollBar.Size = new Size(14, Size.Height);",
        "ScrollBar.Location = new Point(Size.Width - 14, 0);",
        "ScrollBar.VisibleSize = Size.Height;",
        "foreach (KeyValuePair<string, List<ClientUserCurrency>> pair in TreeList)",
        "CurrencyTreeHeader header = new CurrencyTreeHeader",
        "CurrencyItem entry = new CurrencyItem",
    )
    for needle in needles:
        if needle not in source:
            raise SystemExit(f"Currency tree source changed: missing {needle!r}")

    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    window = next((w for w in spec.get("windows", []) if w.get("field") == "CurrencyBox"), None)
    if window is None:
        raise SystemExit("CurrencyBox missing")

    controls = [
        control for control in window.get("controls", [])
        if not str(control.get("sourceGenerated") or "").startswith(PREFIX)
    ]
    tree_name = "CurrencyTreeSource"
    scrollbar_name = "CurrencyTreeSourceScrollBar"
    generated = [
        make(tree_name, "DXControl", {
            "Parent": "this",
            "Location": "ClientArea.Location",
            "Size": "ClientArea.Size",
            "Border": "true",
            "BorderColour": "Constants.PrimaryColour",
            "RuntimeTreeList": "GameScene.Game.User.Currencies; empty in neutral reference",
        }, source_type="CurrencyTree"),
        make(scrollbar_name, "DXVScrollBar", {
            "Parent": tree_name,
            "Change": "22",
            "Size": f"new Size(14, {tree_name}.Size.Height)",
            "Location": f"new Point({tree_name}.Size.Width - 14, 0)",
            "VisibleSize": f"{tree_name}.Size.Height",
            "MaxValue": "0",
        }),
    ]

    window["controls"] = generated + controls
    window["deterministicCurrencyTree"] = {
        "passed": True,
        "controlsAdded": 2,
        "treeShells": 1,
        "scrollbars": 1,
        "runtimeHeadersInvented": False,
        "runtimeCurrencyItemsInvented": False,
        "runtimeCurrencyDataInvented": False,
        "sourceClientSize": [227, 302],
    }
    args.spec.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("Currency deterministic tree shell expanded: 2 controls; no user currency rows")


if __name__ == "__main__":
    main()
