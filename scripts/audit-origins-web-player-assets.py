#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

DIRECT_ACTIONS = [
    "Standing", "Moving", "Pushed", "Attack", "Mining", "Fishing", "Taming",
    "RangeAttack", "Spell", "Struck", "Die", "Dead", "Harvest",
]
UNMAPPED_ACTIONS = ["Show", "Hide", "Mount", "Idle"]
SELECTOR_MAPS = ["ArmourList", "CostumeList", "WeaponList", "ShieldList", "HelmetList"]


def check(rows: list[dict], name: str, condition: bool, details: str) -> None:
    rows.append({"name": name, "pass": bool(condition), "details": details})


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--runtime", type=Path, required=True)
    parser.add_argument("--sprite-runtime", type=Path, required=True)
    parser.add_argument("--exporter", type=Path, required=True)
    parser.add_argument("--player-source", type=Path, required=True)
    parser.add_argument("--map-source", type=Path, required=True)
    parser.add_argument("--functions-source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    contract = json.loads(args.contract.read_text(encoding="utf-8"))
    runtime = args.runtime.read_text(encoding="utf-8")
    sprite = args.sprite_runtime.read_text(encoding="utf-8")
    exporter = args.exporter.read_text(encoding="utf-8")
    player = args.player_source.read_text(encoding="utf-8-sig")
    map_source = args.map_source.read_text(encoding="utf-8-sig")
    functions = args.functions_source.read_text(encoding="utf-8-sig")

    rows: list[dict] = []
    frames = contract.get("playerFrames", {})
    animations = contract.get("mirAnimation", {})
    magic_map = contract.get("magicAnimationMap", {})
    libraries = contract.get("playerLibraries", [])
    selectors = contract.get("playerLibrarySelectors", {})
    hide_weapon_shapes = contract.get("costumeShapeHideWeapon", [])
    lib_names = {row.get("libraryFile") for row in libraries}

    check(rows, "Generated contract schema", contract.get("schema") == "origins.zircon.web-player-assets.v1", contract.get("schema", "missing"))
    check(rows, "All FrameSet.Players entries", len(frames) == 42, f"count={len(frames)}")
    check(rows, "Player frames are MirAnimation values", all(name in animations for name in frames), f"frames={len(frames)}, enum={len(animations)}")
    check(rows, "Magic animation map extracted", len(magic_map) >= 100, f"cases={len(magic_map)}")
    check(rows, "Core body libraries", {"M_Hum", "WM_Hum", "M_HumA", "WM_HumA"}.issubset(lib_names), ", ".join(sorted(name for name in ["M_Hum", "WM_Hum", "M_HumA", "WM_HumA"] if name in lib_names)))
    check(rows, "Player layer library families", all(any(name.startswith(prefix) for name in lib_names) for prefix in ["M_Hair", "M_Weapon", "M_Helmet", "M_Shield", "Horse"]), f"libraries={len(libraries)}")

    constants = contract.get("playerConstants", {})
    check(rows, "Female offset", constants.get("FemaleOffSet") == 5000, str(constants.get("FemaleOffSet")))
    check(rows, "Assassin offset", constants.get("AssassinOffSet") == 50000, str(constants.get("AssassinOffSet")))
    check(rows, "Right-hand offset", constants.get("RightHandOffSet") == 50, str(constants.get("RightHandOffSet")))

    check(rows, "All PlayerObject selector dictionaries extracted", all(name in selectors and selectors[name] for name in SELECTOR_MAPS), ", ".join(f"{name}={len(selectors.get(name, {}))}" for name in SELECTOR_MAPS))
    check(rows, "Male/female body selectors", selectors.get("ArmourList", {}).get("0") == "M_Hum" and selectors.get("ArmourList", {}).get("5000") == "WM_Hum", "M_Hum / WM_Hum")
    check(rows, "Assassin body selectors", selectors.get("ArmourList", {}).get("50000") == "M_HumA" and selectors.get("ArmourList", {}).get("55000") == "WM_HumA", "M_HumA / WM_HumA")
    check(rows, "Assassin dual weapon selectors", selectors.get("WeaponList", {}).get("120") == "M_WeaponADL1" and selectors.get("WeaponList", {}).get("170") == "M_WeaponADR1", "ADL/ADR")
    check(rows, "Costume weapon-hide list", hide_weapon_shapes == [6, 7, 8, 9, 10, 11, 12, 13, 16, 17, 18], str(hide_weapon_shapes))
    check(rows, "Web PlayerObject library selection", "resolvePlayerLibrarySelection" in runtime and "ZIRCON_PLAYER_LIBRARY_SELECTORS" in runtime and "rightHandOffset" in runtime, "body/hair/helmet/weapon/shield/horse selection")

    formula = "DrawFrame = FrameIndex + CurrentFrame.StartIndex + CurrentFrame.OffSet * (int)Direction;"
    check(rows, "Pinned DrawFrame formula", formula in map_source, formula)
    check(rows, "Web DrawFrame formula", "localFrame + frame.startIndex + frame.offset * direction" in runtime, "start + local + offset*direction")
    check(rows, "Pinned Player Pushed override", "Race == ObjectType.Player && CurrentAction == MirAction.Pushed" in map_source and "frame = 0;" in map_source, "Player Pushed -> frame 0")
    check(rows, "Web Player Pushed override", "action === 'Pushed'" in runtime and "pushedPlayerFrameOverride" in runtime, "Player Pushed -> contract frame 0")

    for action in DIRECT_ACTIONS:
        check(rows, f"Action mapping {action}", f"case MirAction.{action}:" in player and f"case '{action}':" in runtime, "pinned PlayerObject + web resolver")
    check(rows, "No fabricated direct Show/Hide/Mount/Idle", all(name in runtime for name in UNMAPPED_ACTIONS) and "DIRECT_UNMAPPED_PLAYER_ACTIONS" in runtime, ", ".join(UNMAPPED_ACTIONS))

    attack_tokens = [
        "case MagicType.Slaying:", "case MagicType.HalfMoon:", "case MagicType.DragonRise:",
        "case MagicType.BladeStorm:", "case MagicType.FullBloom:", "case MagicType.SweetBrier:",
        "case MirClass.Assassin:",
    ]
    check(rows, "Pinned attack animation branches", all(token in functions for token in attack_tokens), "GetAttackAnimation branches present")
    check(rows, "Web attack animation resolver", "resolveAttackAnimation" in runtime and "Combat13" in runtime and "Combat12" in runtime and "Combat11" in runtime, "weapon/class conditional resolver present")

    check(rows, "Assassin ArmourShift support", "ASSASSIN_ARMOUR_SHIFT" in runtime and "ArmourShift = -960" in player, "native shifts + Combat2 carry-over")
    check(rows, "Layer frame composition", all(token in runtime for token in ["armourShapeOffset", "weaponShapeOffset", "hairTypeOffset", "horseType"]), "body/hair/helmet/weapon/shield/horse")

    draw_tokens = [
        "case MirDirection.Up:", "case MirDirection.DownLeft:", "case MirDirection.Left:", "case MirDirection.UpLeft:",
        "case MirDirection.UpRight:", "case MirDirection.Right:", "case MirDirection.DownRight:",
        "bool hideWeapon = CostumeShapeHideWeapon.Contains(CostumeShape);",
    ]
    check(rows, "Pinned direction-aware DrawBody order", all(token in player for token in draw_tokens), "weapon/shield before/after body branches present")
    check(rows, "Web direction-aware draw plan", "resolvePlayerDrawPlan" in runtime and "behindWeapon1Directions" in runtime and "frontWeapon1Directions" in runtime and "ZIRCON_COSTUME_HIDE_WEAPON.includes" in runtime, "weapon/shield/body/head depth plan")
    check(rows, "Horse draw-order support", "HORSE_ANIMATIONS" in runtime and "horseShapeEffect" in runtime and "frameMode" in runtime, "horse first + dark/royal overlay")

    check(rows, "Exporter reads Zircon Mir3Library", "Mir3Library library = new(source)" in exporter, "LibraryEditor.Mir3Library")
    check(rows, "Exporter preserves image offsets", "OffsetX = image.OffSetX" in exporter and "OffsetY = image.OffSetY" in exporter, "OffSetX/OffSetY -> manifest")
    check(rows, "Exporter writes PNG atlas", "ImageFormat.Png" in exporter and "page_{_pageIndex:000}.png" in exporter, "RGBA atlas pages")
    check(rows, "Browser applies Zircon offsets", "anchorX + frame.offsetX" in sprite and "anchorY + frame.offsetY" in sprite, "atlas frame offsets used at draw time")
    check(rows, "Browser uses pixel rendering", "imageSmoothingEnabled = false" in sprite, "nearest/pixel rendering")

    forbidden = ["vendor/crystal", "crystal-spells", "Crystal-Monk", "crystal-player-actions"]
    active_text = "\n".join([runtime, sprite, exporter])
    check(rows, "No Crystal runtime fallback", not any(token.lower() in active_text.lower() for token in forbidden), "no Crystal paths or archive runtime references")

    result = {
        "schema": "origins.zircon.web-player-assets-audit.v1",
        "pass": all(row["pass"] for row in rows),
        "frameCount": len(frames),
        "magicAnimationCases": len(magic_map),
        "playerLibraryCount": len(libraries),
        "selectorCount": sum(len(mapping) for mapping in selectors.values()),
        "checks": rows,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
