#!/usr/bin/env python3
"""Materialize CompanionDialog's deterministic enum-backed filter controls.

DrawClassFilter, DrawRarityFilter and DrawItemTypeFilter are called by the
constructor and create fixed DXCheckBox + DXLabel pairs from checked-in enums.
Only later RefreshFilter() applies the user's saved checked state, so neutral
reference controls stay unchecked and carry no user/runtime payload.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

SOURCE_PATH = "Client/Scenes/Views/CompanionDialog.cs"
ENUM_PATH = "LibraryCore/Enum.cs"
PREFIX = "deterministic-companion-filter:"

ITEM_SKIP = {
    "Nothing", "Consumable", "Torch", "Poison", "Amulet", "Meat", "Ore",
    "Currency", "DarkStone", "RefineSpecial", "HorseArmour", "CompanionFood",
    "System", "ItemPart", "Hook", "Float", "Bait", "Finder", "Reel",
}

SOURCE_EVIDENCE = (
    "DrawClassFilter();",
    "DrawRarityFilter();",
    "DrawItemTypeFilter();",
    "Array classes = Enum.GetValues(typeof(MirClass));",
    "Array rarityList = Enum.GetValues(typeof(Rarity));",
    "Array itemTypes = Enum.GetValues(typeof(ItemType));",
    'itemType.ToString().Contains("Companion")',
    "new Point(10 + (110 * index), 30 + (18 * row))",
    "new Point(10 + (110 * index), 90 + (18 * row))",
    "new Point(10 + (110 * index), 150 + (18 * row))",
)


def enum_members(text: str, enum_name: str) -> list[str]:
    match = re.search(rf"\b(?:public\s+)?enum\s+{re.escape(enum_name)}\b[^{{]*\{{", text)
    if not match:
        raise SystemExit(f"Enum missing: {enum_name}")
    opening = text.find("{", match.start())
    depth = 0
    closing = -1
    for index in range(opening, len(text)):
        if text[index] == "{":
            depth += 1
        elif text[index] == "}":
            depth -= 1
            if depth == 0:
                closing = index
                break
    if closing < 0:
        raise SystemExit(f"Enum body unterminated: {enum_name}")
    body = text[opening + 1:closing]
    members: list[str] = []
    for raw in body.splitlines():
        line = raw.split("//", 1)[0].strip()
        if not line or line.startswith("["):
            continue
        member = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s*(?:=|,|$)", line)
        if member:
            members.append(member.group(1))
    if not members:
        raise SystemExit(f"Enum has no parsed members: {enum_name}")
    return members


def display_name(member: str) -> str:
    # Zircon's InsertSpace().ToUpperByWord(): split PascalCase/acronym edges,
    # then title each word. Current enum members contain no punctuation.
    spaced = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", member)
    spaced = re.sub(r"(?<=[A-Z])(?=[A-Z][a-z])", " ", spaced)
    return " ".join(word[:1].upper() + word[1:].lower() for word in spaced.split())


def make_pair(helper: str, group: str, member: str, ordinal: int, base_y: int, fore: str) -> list[dict]:
    column = ordinal % 2
    row = ordinal // 2
    checkbox_name = f"Companion{group}Filter{member}"
    label_name = f"{checkbox_name}Label"
    x = 10 + 110 * column
    label_x = 25 + 110 * column
    y = base_y + 18 * row
    generated = f"{PREFIX}CompanionDialog.{helper}"
    return [
        {
            "name": checkbox_name,
            "sourceName": checkbox_name,
            "type": "DXCheckBox",
            "sourceType": "DXCheckBox",
            "properties": {
                "Parent": "FilterControl",
                "Hint": f'"Pick {member.lower()} items"',
                "Location": f"new Point({x}, {y})",
            },
            "resolvedText": "",
            "sourceGenerated": generated,
            "deterministicHelperControl": True,
            "helper": helper,
            "runtimeCheckedState": "user config applied later by RefreshFilter; neutral default false",
            "runtimePayloadInvented": False,
        },
        {
            "name": label_name,
            "sourceName": label_name,
            "type": "DXLabel",
            "sourceType": "DXLabel",
            "properties": {
                "Parent": "FilterControl",
                "Outline": "true",
                "ForeColour": fore,
                "OutlineColour": "Color.Black",
                "IsControl": "false",
                "Text": f'"{display_name(member)}"',
                "Location": f"new Point({label_x}, {y})",
            },
            "resolvedText": display_name(member),
            "sourceGenerated": generated,
            "deterministicHelperControl": True,
            "helper": helper,
            "runtimePayloadInvented": False,
        },
    ]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--zircon-root", type=Path, required=True)
    args = parser.parse_args()

    source = (args.zircon_root / SOURCE_PATH).read_text(encoding="utf-8-sig")
    missing = [needle for needle in SOURCE_EVIDENCE if needle not in source]
    if missing:
        raise SystemExit("Companion filter source contract changed:\n- " + "\n- ".join(missing))

    enum_text = (args.zircon_root / ENUM_PATH).read_text(encoding="utf-8-sig")
    classes = enum_members(enum_text, "MirClass")
    rarities = enum_members(enum_text, "Rarity")
    item_types = [
        member for member in enum_members(enum_text, "ItemType")
        if member not in ITEM_SKIP and "Companion" not in member
    ]

    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    window = next((w for w in spec.get("windows", []) if w.get("field") == "CompanionBox"), None)
    if window is None:
        raise SystemExit("CompanionBox missing")

    controls = [
        control for control in window.get("controls", [])
        if not str(control.get("sourceGenerated") or "").startswith(PREFIX)
    ]
    existing_names = {str(control.get("name") or "") for control in controls}
    generated: list[dict] = []

    groups = (
        ("DrawClassFilter", "Class", classes, 30),
        ("DrawRarityFilter", "Rarity", rarities, 90),
        ("DrawItemTypeFilter", "ItemType", item_types, 150),
    )
    for helper, group, members, base_y in groups:
        for ordinal, member in enumerate(members):
            fore = "Color.White"
            if group == "Class":
                fore = "Color.AntiqueWhite"
            elif group == "Rarity":
                fore = {
                    "Common": "Color.AntiqueWhite",
                    "Elite": "Color.MediumPurple",
                    "Superior": "Color.PaleGreen",
                }.get(member, "Color.AntiqueWhite")
            pair = make_pair(helper, group, member, ordinal, base_y, fore)
            collisions = [control["name"] for control in pair if control["name"] in existing_names]
            if collisions:
                raise SystemExit(f"Companion filter name collision: {collisions}")
            generated.extend(pair)

    expected_controls = 2 * (len(classes) + len(rarities) + len(item_types))
    if len(generated) != expected_controls:
        raise SystemExit(f"Companion filter generated count mismatch: {len(generated)} != {expected_controls}")
    if any((control.get("properties") or {}).get("Checked") == "true" for control in generated):
        raise SystemExit("Companion filter materializer fabricated checked user state")
    if any(control.get("runtimePayloadInvented") is not False for control in generated):
        raise SystemExit("Companion filter materializer introduced runtime payloads")

    window["controls"] = generated + controls
    window["deterministicCompanionFilters"] = {
        "passed": True,
        "classValues": classes,
        "rarityValues": rarities,
        "itemTypeValues": item_types,
        "classPairs": len(classes),
        "rarityPairs": len(rarities),
        "itemTypePairs": len(item_types),
        "controlsAdded": len(generated),
        "helpers": [helper for helper, _, _, _ in groups],
        "twoColumnLayout": True,
        "runtimeCheckedStateInvented": False,
        "runtimePayloadsInvented": False,
        "enumBacked": True,
        "sourceBackedOnly": True,
    }
    args.spec.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(
        "Companion filter rows expanded: "
        f"classes={len(classes)}, rarities={len(rarities)}, itemTypes={len(item_types)}, "
        f"controls={len(generated)}; neutral checked state"
    )


if __name__ == "__main__":
    main()
