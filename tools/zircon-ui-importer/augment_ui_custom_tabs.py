#!/usr/bin/env python3
"""Augment the Zircon UI manifest with source-built tabs missed by the base parser.

The base inventory intentionally parses direct `new DX...` controls in each
GameScene window constructor. Zircon also uses:
- custom DXTab subclasses (QuestTab, MilestoneTab, MissionTab),
- helper methods that build plain DXTab instances (GuildDialog),
- runtime/data-driven custom tabs (MagicTab).

This pass adds only deterministic static tab instances to `controls` and records
Magic's data-driven schools as templates. It does not invent active player data.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from build_ui_source_spec import constructor_body, match_brace, named_method_body, split_top_level

CLASS_RE = re.compile(r"\bclass\s+([A-Za-z_][A-Za-z0-9_]*)\s*:\s*([A-Za-z_][A-Za-z0-9_]*)")
GENERIC_INIT_RE = re.compile(
    r"(?:(?:[A-Za-z_][A-Za-z0-9_<>]*\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*)"
    r"new\s+([A-Za-z_][A-Za-z0-9_]*)\s*\{"
)


def normalise(value: str) -> str:
    return " ".join(value.strip().split())


def class_bases(zircon_root: Path) -> dict[str, str]:
    bases: dict[str, str] = {}
    for path in (zircon_root / "Client").rglob("*.cs"):
        try:
            text = path.read_text(encoding="utf-8-sig")
        except UnicodeDecodeError:
            continue
        for name, base in CLASS_RE.findall(text):
            bases[name] = base
    return bases


def derives_from(name: str, target: str, bases: dict[str, str]) -> bool:
    seen: set[str] = set()
    current = name
    while current and current not in seen:
        if current == target:
            return True
        seen.add(current)
        current = bases.get(current, "")
    return False


def parse_initializers(body: str, allowed_types: set[str]) -> list[dict]:
    out: list[dict] = []
    for match in GENERIC_INIT_RE.finditer(body):
        name, source_type = match.groups()
        if source_type not in allowed_types:
            continue
        opening = body.find("{", match.start())
        try:
            closing = match_brace(body, opening)
        except ValueError:
            continue
        chunk = body[opening + 1:closing]
        props: dict[str, str] = {}
        for entry in split_top_level(chunk, ','):
            prop = re.match(r"\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.+?)\s*$", entry, re.S)
            if prop:
                props[prop.group(1)] = normalise(prop.group(2))
        out.append({"name": name, "sourceType": source_type, "properties": props, "sourceOffset": match.start()})
    return out


def tab_button_explicitly_hidden(properties: dict) -> bool:
    expression = str(properties.get("TabButton", ""))
    return bool(re.search(r"\bVisible\s*=\s*false\b", expression))


def as_tab_control(instance: dict, source_kind: str) -> dict:
    props = dict(instance["properties"])
    hidden = tab_button_explicitly_hidden(props)
    if hidden:
        # Runtime reference equivalent: a hidden tab button cannot be selected
        # by DXTabControl.TabsChanged(), so its content begins hidden as well.
        props["Visible"] = "false"
    return {
        "name": instance["name"],
        "type": "DXTab",
        "sourceType": instance["sourceType"],
        "properties": props,
        "customTab": True,
        "customTabSource": source_kind,
        "tabButtonVisible": not hidden,
    }


def add_quest_tabs(window: dict, source: str, custom_tab_types: set[str]) -> int:
    body = constructor_body(source, window["class"])
    instances = [
        instance for instance in parse_initializers(body, custom_tab_types)
        if instance["properties"].get("Parent") == "TabControl"
    ]
    existing = {control["name"] for control in window.get("controls", [])}
    controls = [as_tab_control(instance, "window-constructor-custom-tab") for instance in instances if instance["name"] not in existing]

    # DXTabControl completely removes non-user-visible tab buttons from its
    # horizontal layout. The base reference resolver is a flat source geometry
    # pass, so append currently visible tabs first to reproduce the same visible
    # ordering without allocating a fake gap for Completed/Mission.
    controls.sort(key=lambda control: 0 if control["tabButtonVisible"] else 1)
    window["controls"].extend(controls)

    if controls:
        window["customTabModel"] = {
            "kind": "static-custom-tabs",
            "sourceBacked": True,
            "sourceOrder": [instance["name"] for instance in instances],
            "renderOrder": [control["name"] for control in controls],
            "defaultSelectionRule": "DXTabControl selects first user-visible tab",
        }
    return len(controls)


def guild_default_visibility(name: str) -> tuple[bool, str]:
    # GuildDialog constructor calls ClearGuild() before GuildInfo is assigned.
    # GuildInfo is therefore null in the initial source state.
    if name == "CreateTab":
        return True, "GuildInfo == null"
    if name == "CastleTab":
        return False, "GuildInfo != null && current guild owns a castle"
    return False, "GuildInfo != null"


def add_guild_tabs(window: dict, source: str) -> int:
    ctor = constructor_body(source, window["class"])
    helper_calls = re.findall(r"\b(Create[A-Za-z0-9_]*Tab)\s*\(\s*\)\s*;", ctor)
    existing = {control["name"] for control in window.get("controls", [])}
    added = 0
    state_rows = []
    pending = []
    for helper in helper_calls:
        body = named_method_body(source, helper)
        for instance in parse_initializers(body, {"DXTab"}):
            if instance["name"] in existing or instance["properties"].get("Parent") != "GuildTabs":
                continue
            visible, runtime_expression = guild_default_visibility(instance["name"])
            control = as_tab_control(instance, f"helper:{helper}")
            control["properties"]["Visible"] = "true" if visible else "false"
            control["tabButtonVisible"] = visible
            control["sourceRuntimeVisibilityExpression"] = runtime_expression
            pending.append(control)
            existing.add(instance["name"])
            state_rows.append({
                "tab": instance["name"],
                "initialNoGuildVisible": visible,
                "runtimeVisibility": runtime_expression,
            })
            added += 1
    pending.sort(key=lambda control: 0 if control["tabButtonVisible"] else 1)
    window["controls"].extend(pending)
    if added:
        window["customTabModel"] = {
            "kind": "source-state-tabs",
            "sourceBacked": True,
            "initialState": "noGuild",
            "states": state_rows,
            "defaultSelection": "CreateTab in noGuild state; HomeTab after GuildInfo is populated",
        }
    return added


def add_magic_templates(window: dict, source: str) -> int:
    # Magic tabs are created only after runtime MagicInfo + player class filtering.
    # Record the exact source artwork per school without claiming any are active.
    if not re.search(r"\bclass\s+MagicTab\s*:\s*DXTab\b", source):
        return 0
    ctor = constructor_body(source, "MagicTab")
    templates = []
    case_re = re.compile(
        r"case\s+MagicSchool\.([A-Za-z_][A-Za-z0-9_]*)\s*:\s*"
        r"(.*?)(?=\bcase\s+MagicSchool\.|\bdefault\s*:|\}\s*\n\s*ScrollBar\s*=)",
        re.S,
    )
    for school, block in case_re.findall(ctor):
        index = re.search(r"TabButton\.Index\s*=\s*(\d+)", block)
        hover = re.search(r"TabButton\.HoverIndex\s*=\s*(\d+)", block)
        pressed = re.search(r"TabButton\.PressedIndex\s*=\s*(\d+)", block)
        if not index:
            continue
        templates.append({
            "school": school,
            "normalIndex": int(index.group(1)),
            "hoverIndex": int(hover.group(1)) if hover else int(index.group(1)),
            "pressedIndex": int(pressed.group(1)) if pressed else int(index.group(1)),
            "library": "Interface",
        })
    window["dynamicTabTemplates"] = {
        "sourceType": "MagicTab",
        "baseType": "DXTab",
        "runtimeCreationMethod": "MagicDialog.CreateTabs",
        "runtimeDependentOn": ["Globals.MagicInfoList", "MapObject.User.Class", "owned/item-required magics"],
        "doNotAssumeVisibleSchools": True,
        "templates": templates,
    }
    return len(templates)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--zircon-root", type=Path, required=True)
    args = parser.parse_args()

    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    bases = class_bases(args.zircon_root)
    custom_tab_types = {name for name in bases if name != "DXTab" and derives_from(name, "DXTab", bases)}

    quest_added = guild_added = magic_templates = 0
    for window in spec.get("windows", []):
        source_path = window.get("sourcePath")
        if not source_path:
            continue
        path = args.zircon_root / source_path
        if not path.exists():
            continue
        source = path.read_text(encoding="utf-8-sig")
        if window.get("field") == "QuestBox":
            quest_added += add_quest_tabs(window, source, custom_tab_types)
        elif window.get("field") == "GuildBox":
            guild_added += add_guild_tabs(window, source)
        elif window.get("field") == "MagicBox":
            magic_templates += add_magic_templates(window, source)

    spec["customTabPass"] = {
        "sourceBacked": True,
        "questStaticTabsAdded": quest_added,
        "guildStaticTabsAdded": guild_added,
        "magicDynamicTemplates": magic_templates,
        "customDXTabSubclassCount": len(custom_tab_types),
        "dynamicMagicVisibilityInvented": False,
    }
    args.spec.write_text(json.dumps(spec, indent=2, ensure_ascii=False), encoding="utf-8")

    print("Quest custom tabs added:", quest_added)
    print("Guild helper-built tabs added:", guild_added)
    print("Magic dynamic tab templates:", magic_templates)
    print("Custom DXTab subclasses discovered:", len(custom_tab_types))


if __name__ == "__main__":
    main()
