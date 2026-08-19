#!/usr/bin/env python3
"""Strict source contract for deterministic GuildDialog root helper controls."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


PANELS = {
    "CreatePanel": "true",
    "TreasuryPanel": "false",
    "AddMemberPanel": "false",
    "StoragePanel": "false",
    "WarPanel": "false",
    "CastlePanel": "false",
}
BUTTONS = {
    "StarterGuildButton": ("CreatePanel", "new Point(10, 10)", "new Size(120, DefaultHeight)", None, None),
    "SetTaxButton": ("TreasuryPanel", "new Point(10, 10)", "new Size(120, DefaultHeight)", None, None),
    "AddMemberButton": ("AddMemberPanel", "new Point(10, 10)", "new Size(110, DefaultHeight)", None, None),
    "EditDefaultMemberButton": ("AddMemberPanel", "new Point(125, 10)", "new Size(110, DefaultHeight)", None, None),
    "IncreaseMemberButton": ("AddMemberPanel", "new Point(240, 10)", "new Size(110, DefaultHeight)", None, None),
    "IncreaseStorageButton": ("StoragePanel", "new Point(10, 10)", "new Size(110, DefaultHeight)", None, None),
    "StartWarButton": ("WarPanel", "new Point(10, 10)", "new Size(110, DefaultHeight)", None, None),
    "ToggleGates": ("CastlePanel", "new Point(10, 10)", "new Size(120, DefaultHeight)", "false", "true"),
    "RepairGates": ("CastlePanel", "new Point(220, 10)", "new Size(100, DefaultHeight)", "false", "true"),
    "RepairGuards": ("CastlePanel", "new Point(330, 10)", "new Size(100, DefaultHeight)", "false", "true"),
}


def props(control: dict | None) -> dict:
    return (control or {}).get("properties") or {}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--zircon-root", type=Path, required=True)
    args = parser.parse_args()

    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    guild = next((w for w in spec.get("windows", []) if w.get("field") == "GuildBox"), None)
    if guild is None:
        raise SystemExit("GuildBox missing")
    contract = guild.get("deterministicGuildRootHelperControls") or {}
    if contract.get("passed") is not True or contract.get("controlsAdded") != 16:
        raise SystemExit(f"Guild root helper expansion incomplete: {contract}")
    if contract.get("panels") != 6 or contract.get("buttons") != 10:
        raise SystemExit(f"Guild root helper matrix drifted: {contract}")
    if contract.get("guildStorageCostSourceValue") != 350000:
        raise SystemExit(f"GuildStorageCost source contract changed: {contract}")
    for key in ("runtimeCastlePanelsInvented", "clickCreatedModalsInvented", "runtimeGuildInfoInvented"):
        if contract.get(key) is not False:
            raise SystemExit(f"Guild root helper runtime boundary broken: {key} -> {contract}")

    by = {str(control.get("name") or ""): control for control in guild.get("controls", [])}
    for name, visible in PANELS.items():
        control = by.get(name)
        if control is None or control.get("type") != "DXControl":
            raise SystemExit(f"Guild root helper panel missing: {name}")
        p = props(control)
        expected = {
            "Parent": "this",
            "Location": "new Point(10, 500)",
            "Size": "new Size(436, 50)",
            "Border": "false",
            "Visible": visible,
        }
        for key, value in expected.items():
            if p.get(key) != value:
                raise SystemExit(f"Guild panel source state drifted: {name}.{key}={p.get(key)!r}, expected {value!r}")

    for name, (parent, location, size, enabled, visible) in BUTTONS.items():
        control = by.get(name)
        if control is None or control.get("type") != "DXButton":
            raise SystemExit(f"Guild root helper button missing: {name}")
        p = props(control)
        expected = {
            "Parent": parent,
            "Location": location,
            "Size": size,
            "ButtonType": "ButtonType.Default",
            "LabelStyle": "ButtonLabelStyle.Gold",
        }
        for key, value in expected.items():
            if p.get(key) != value:
                raise SystemExit(f"Guild button source state drifted: {name}.{key}={p.get(key)!r}, expected {value!r}")
        if enabled is not None and p.get("Enabled") != enabled:
            raise SystemExit(f"Guild button Enabled drifted: {name} -> {p.get('Enabled')}")
        if visible is not None and p.get("Visible") != visible:
            raise SystemExit(f"Guild button Visible drifted: {name} -> {p.get('Visible')}")
        if not str(control.get("resolvedText") or "").strip():
            raise SystemExit(f"Guild root helper button text unresolved: {name}")
        if control.get("runtimePayloadInvented") is not False:
            raise SystemExit(f"Guild root helper runtime payload marker invalid: {name}")

    if by["EditDefaultMemberButton"].get("sourceLocationExpression") != "new Point(AddMemberButton.DisplayArea.Right + 5, 10)":
        raise SystemExit("Guild EditDefaultMemberButton source-relative geometry lost")
    if by["IncreaseMemberButton"].get("sourceLocationExpression") != "new Point(EditDefaultMemberButton.DisplayArea.Right + 5, 10)":
        raise SystemExit("Guild IncreaseMemberButton source-relative geometry lost")

    # Runtime-created castle panels must remain absent from the neutral manifest.
    fabricated_castles = [
        control.get("name") for control in guild.get("controls", [])
        if control.get("sourceType") == "GuildCastlePanel"
        or "GuildCastlePanel" in str(control.get("sourceGenerated") or "")
    ]
    if fabricated_castles:
        raise SystemExit(f"Runtime CastleInfo GuildCastlePanel rows were fabricated: {fabricated_castles}")

    spec["guildRootHelperAudit"] = {
        "passed": True,
        "deterministicControls": 16,
        "panels": 6,
        "buttons": 10,
        "finalVisiblePanels": ["CreatePanel"],
        "runtimeCastlePanelsInvented": False,
        "clickCreatedModalsInvented": False,
    }
    args.spec.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("Guild root helper audit: PASS (16 deterministic controls; no runtime castles/modals)")


if __name__ == "__main__":
    main()
