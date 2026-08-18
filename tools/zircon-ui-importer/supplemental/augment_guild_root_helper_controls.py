#!/usr/bin/env python3
"""Materialise deterministic GuildDialog helper controls parented to the window.

augment_ui_composites intentionally follows helper children whose Parent chain
reaches a Guild tab. GuildDialog also creates six bottom action panels directly
under `this` from constructor-called Create*Tab helpers. Those controls are just
as deterministic as the tabs and must exist in the neutral desktop reference.
Runtime CastleInfo rows and click-created modal windows remain absent.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


PREFIX = "deterministic-guild-root:"
PANEL_NAMES = (
    "CreatePanel", "TreasuryPanel", "AddMemberPanel", "StoragePanel",
    "WarPanel", "CastlePanel",
)


def english(spec: dict, key: str, fallback: str = "") -> str:
    return str(((spec.get("language") or {}).get("English") or {}).get(key) or fallback)


def format_source_number(template: str, value: int) -> str:
    """Resolve the numeric String.Format shape used by current Guild labels."""
    formatted = f"{value:,}"
    value_text = str(value)
    result = re.sub(r"\{0:(?:#,##0|N0)\}", formatted, template)
    return result.replace("{0}", value_text)


def make(name: str, type_name: str, properties: dict[str, str], *, helper: str,
         resolved_text: str | None = None, state: str | None = None) -> dict:
    item = {
        "name": name,
        "type": type_name,
        "properties": dict(properties),
        "sourceGenerated": f"{PREFIX}GuildDialog.{helper}",
        "sourceHelper": helper,
        "runtimePayloadInvented": False,
    }
    if resolved_text is not None:
        item["resolvedText"] = resolved_text
    if state:
        item["sourceInitialState"] = state
    return item


def panel(name: str, helper: str, visible: bool) -> dict:
    return make(name, "DXControl", {
        "Parent": "this",
        "Location": "new Point(10, 500)",
        "Size": "new Size(436, 50)",
        "Border": "false",
        "Visible": "true" if visible else "false",
    }, helper=helper, state=(
        "source initializer Visible=true; final constructor noGuild/CreateTab selection keeps visible"
        if visible else
        "source initializer Visible=true; final constructor noGuild/CreateTab click hides panel"
    ))


def button(name: str, parent: str, helper: str, *, x: int, width: int,
           label_expression: str, text: str, enabled: bool | None = None,
           visible: bool | None = None, source_location: str | None = None) -> dict:
    props = {
        "Parent": parent,
        "Location": f"new Point({x}, 10)",
        "ButtonType": "ButtonType.Default",
        "Size": f"new Size({width}, DefaultHeight)",
        "LabelStyle": "ButtonLabelStyle.Gold",
        "Label": label_expression,
    }
    if enabled is not None:
        props["Enabled"] = "true" if enabled else "false"
    if visible is not None:
        props["Visible"] = "true" if visible else "false"
    item = make(name, "DXButton", props, helper=helper, resolved_text=text)
    if source_location:
        item["sourceLocationExpression"] = source_location
        item["sourceLocationDerivedExactly"] = True
    return item


def assert_source(root: Path) -> tuple[str, int]:
    guild_path = root / "Client/Scenes/Views/GuildDialog.cs"
    globals_path = root / "LibraryCore/Globals.cs"
    guild = guild_path.read_text(encoding="utf-8-sig")
    globals_text = globals_path.read_text(encoding="utf-8-sig")
    needles = (
        "CreateCreateTab();", "CreateHomeTab();", "CreateMemberTab();",
        "CreateStorageTab();", "CreateWarTab();", "CreateStyleTab();",
        "CreateCastleTab();", "ClearGuild();",
        "CreatePanel = new DXControl", "StarterGuildButton = new DXButton",
        "TreasuryPanel = new DXControl", "SetTaxButton = new DXButton",
        "AddMemberPanel = new DXControl", "AddMemberButton = new DXButton",
        "EditDefaultMemberButton = new DXButton", "IncreaseMemberButton = new DXButton",
        "StoragePanel = new DXControl", "IncreaseStorageButton = new DXButton",
        "WarPanel = new DXControl", "StartWarButton = new DXButton",
        "CastlePanel = new DXControl", "ToggleGates = new DXButton",
        "RepairGates = new DXButton", "RepairGuards = new DXButton",
        "foreach (CastleInfo castle in CEnvir.CastleInfoList.Binding)",
        "CastlePanels[castle] = new GuildCastlePanel",
    )
    for needle in needles:
        if needle not in guild:
            raise SystemExit(f"Guild root-helper source changed: missing {needle!r}")
    cost_match = re.search(r"GuildStorageCost\s*=\s*(\d+)", globals_text)
    if not cost_match:
        raise SystemExit("Globals.GuildStorageCost literal no longer source-resolvable")
    return guild, int(cost_match.group(1))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--zircon-root", type=Path, required=True)
    args = parser.parse_args()

    _, storage_cost = assert_source(args.zircon_root)
    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    guild = next((w for w in spec.get("windows", []) if w.get("field") == "GuildBox"), None)
    if guild is None:
        raise SystemExit("GuildBox missing from promoted manifest")

    controls = [
        control for control in guild.get("controls", [])
        if not str(control.get("sourceGenerated") or "").startswith(PREFIX)
    ]
    existing_names = {str(control.get("name") or "") for control in controls}
    expected_names = {
        "CreatePanel", "StarterGuildButton",
        "TreasuryPanel", "SetTaxButton",
        "AddMemberPanel", "AddMemberButton", "EditDefaultMemberButton", "IncreaseMemberButton",
        "StoragePanel", "IncreaseStorageButton",
        "WarPanel", "StartWarButton",
        "CastlePanel", "ToggleGates", "RepairGates", "RepairGuards",
    }
    collisions = sorted(expected_names & existing_names)
    if collisions:
        raise SystemExit(
            "Guild root-helper controls became materialised by an earlier pass; "
            f"reconcile this supplemental instead of duplicating them: {collisions}"
        )

    storage_template = english(spec, "GuildDialogManageTabUpgradeStorageIncreaseButtonLabel")
    storage_label = format_source_number(storage_template, storage_cost)

    generated = [
        panel("CreatePanel", "CreateCreateTab", True),
        button(
            "StarterGuildButton", "CreatePanel", "CreateCreateTab", x=10, width=120,
            label_expression="CEnvir.Language.GuildDialogCreateTabStarterGuildButtonLabel",
            text=english(spec, "GuildDialogCreateTabStarterGuildButtonLabel"),
        ),
        panel("TreasuryPanel", "CreateHomeTab", False),
        button(
            "SetTaxButton", "TreasuryPanel", "CreateHomeTab", x=10, width=120,
            label_expression="CEnvir.Language.GuildDialogManageTabTreasuryChangeButtonLabel",
            text=english(spec, "GuildDialogManageTabTreasuryChangeButtonLabel"),
        ),
        panel("AddMemberPanel", "CreateMemberTab", False),
        button(
            "AddMemberButton", "AddMemberPanel", "CreateMemberTab", x=10, width=110,
            label_expression="CEnvir.Language.GuildDialogManageTabMembershipAddButtonLabel",
            text=english(spec, "GuildDialogManageTabMembershipAddButtonLabel"),
        ),
        button(
            "EditDefaultMemberButton", "AddMemberPanel", "CreateMemberTab", x=125, width=110,
            label_expression="CEnvir.Language.GuildDialogManageTabMembershipEditDefaultButtonLabel",
            text=english(spec, "GuildDialogManageTabMembershipEditDefaultButtonLabel"),
            source_location="new Point(AddMemberButton.DisplayArea.Right + 5, 10)",
        ),
        button(
            "IncreaseMemberButton", "AddMemberPanel", "CreateMemberTab", x=240, width=110,
            label_expression="CEnvir.Language.GuildDialogManageTabMembershipMembersIncreaseButtonLabel",
            text=english(spec, "GuildDialogManageTabMembershipMembersIncreaseButtonLabel"),
            source_location="new Point(EditDefaultMemberButton.DisplayArea.Right + 5, 10)",
        ),
        panel("StoragePanel", "CreateStorageTab", False),
        button(
            "IncreaseStorageButton", "StoragePanel", "CreateStorageTab", x=10, width=110,
            label_expression="string.Format(CEnvir.Language.GuildDialogManageTabUpgradeStorageIncreaseButtonLabel, Globals.GuildStorageCost)",
            text=storage_label,
        ),
        panel("WarPanel", "CreateWarTab", False),
        button(
            "StartWarButton", "WarPanel", "CreateWarTab", x=10, width=110,
            label_expression="CEnvir.Language.GuildDialogWarTabGuildWarStartWarButtonLabel",
            text=english(spec, "GuildDialogWarTabGuildWarStartWarButtonLabel"),
        ),
        panel("CastlePanel", "CreateCastleTab", False),
        button(
            "ToggleGates", "CastlePanel", "CreateCastleTab", x=10, width=120,
            label_expression='"Open/Close Gates"', text="Open/Close Gates", enabled=False, visible=True,
        ),
        button(
            "RepairGates", "CastlePanel", "CreateCastleTab", x=220, width=100,
            label_expression='"Repair Gates"', text="Repair Gates", enabled=False, visible=True,
        ),
        button(
            "RepairGuards", "CastlePanel", "CreateCastleTab", x=330, width=100,
            label_expression='"Repair Guards"', text="Repair Guards", enabled=False, visible=True,
        ),
    ]

    unresolved = [control["name"] for control in generated if control["type"] == "DXButton" and not str(control.get("resolvedText") or "").strip()]
    if unresolved:
        raise SystemExit(f"Guild root-helper button source text unresolved: {unresolved}")

    guild["controls"] = generated + controls
    guild["deterministicGuildRootHelperControls"] = {
        "passed": True,
        "controlsAdded": len(generated),
        "expectedControls": 16,
        "panels": 6,
        "buttons": 10,
        "finalNoGuildVisiblePanels": ["CreatePanel"],
        "finalNoGuildHiddenPanels": ["TreasuryPanel", "AddMemberPanel", "StoragePanel", "WarPanel", "CastlePanel"],
        "guildStorageCostSourceValue": storage_cost,
        "runtimeCastlePanelsInvented": False,
        "clickCreatedModalsInvented": False,
        "runtimeGuildInfoInvented": False,
        "source": "GuildDialog constructor -> Create*Tab helpers -> ClearGuild/CreateTab initial state",
    }
    spec.setdefault("deterministicSourceRowPass", {}).setdefault("runtimePayloadsInvented", False)
    args.spec.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("Guild root helper controls expanded: 6 panels + 10 buttons = 16 deterministic controls")


if __name__ == "__main__":
    main()
