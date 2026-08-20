#!/usr/bin/env python3
"""Generate the browser player animation/asset contract from pinned Zircon source.

This script does not read Crystal and does not invent missing frames. It extracts the
actual FrameSet.Players table, magic-to-animation mapping, PlayerObject library
selectors/draw flags, and player-related LibraryList entries from the bootstrapped
pinned Zircon checkout.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

PLAYER_LIBRARY_PREFIXES = (
    "M_Hum", "WM_Hum", "M_Hair", "WM_Hair", "M_Costume", "WM_Costume",
    "Horse", "M_Shield", "WM_Shield", "M_Weapon", "WM_Weapon",
    "M_Helmet", "WM_Helmet",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def extract_block(text: str, marker: str) -> str:
    start = text.find(marker)
    if start < 0:
        raise RuntimeError(f"marker not found: {marker}")
    brace = text.find("{", start)
    if brace < 0:
        raise RuntimeError(f"opening brace not found after: {marker}")
    depth = 0
    for pos in range(brace, len(text)):
        char = text[pos]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[brace + 1:pos]
    raise RuntimeError(f"unterminated block: {marker}")


def parse_mir_animation(enum_text: str) -> list[str]:
    block = extract_block(enum_text, "public enum MirAnimation")
    block = re.sub(r"//.*", "", block)
    names = []
    for raw in block.split(","):
        token = raw.strip()
        if not token:
            continue
        token = token.split("=")[0].strip()
        if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", token):
            names.append(token)
    if len(names) < 40:
        raise RuntimeError(f"unexpected MirAnimation count: {len(names)}")
    return names


def parse_player_frames(frame_text: str) -> dict[str, dict]:
    block = extract_block(frame_text, "Players = new Dictionary<MirAnimation, Frame>")
    pattern = re.compile(
        r"\[MirAnimation\.(?P<name>\w+)\]\s*=\s*new Frame\(\s*"
        r"(?P<start>-?\d+)\s*,\s*(?P<count>\d+)\s*,\s*(?P<offset>-?\d+)\s*,\s*"
        r"TimeSpan\.FromMilliseconds\((?P<delay>\d+)\)\s*\)"
        r"(?:\s*\{(?P<flags>[^}]*)\})?",
        re.MULTILINE,
    )
    frames: dict[str, dict] = {}
    for match in pattern.finditer(block):
        name = match.group("name")
        count = int(match.group("count"))
        delay = int(match.group("delay"))
        flags = match.group("flags") or ""
        frames[name] = {
            "startIndex": int(match.group("start")),
            "frameCount": count,
            "offset": int(match.group("offset")),
            "delaysMs": [delay] * count,
            "reversed": bool(re.search(r"\bReversed\s*=\s*true\b", flags)),
            "staticSpeed": bool(re.search(r"\bStaticSpeed\s*=\s*true\b", flags)),
        }

    delay_pattern = re.compile(
        r"Players\[MirAnimation\.(?P<name>\w+)\]\.Delays\[(?P<index>\d+)\]\s*=\s*"
        r"TimeSpan\.FromMilliseconds\((?P<delay>\d+)\)"
    )
    for match in delay_pattern.finditer(frame_text):
        name = match.group("name")
        index = int(match.group("index"))
        delay = int(match.group("delay"))
        if name not in frames:
            raise RuntimeError(f"custom delay references unknown player frame {name}")
        if not 0 <= index < frames[name]["frameCount"]:
            raise RuntimeError(f"custom delay index out of range: {name}[{index}]")
        frames[name]["delaysMs"][index] = delay

    if len(frames) != 42:
        raise RuntimeError(f"expected 42 FrameSet.Players entries, got {len(frames)}")
    return frames


def parse_magic_animation_map(functions_text: str) -> dict[str, str]:
    block = extract_block(functions_text, "public static MirAnimation GetMagicAnimation")
    mapping: dict[str, str] = {}
    cursor = 0
    return_pattern = re.compile(r"return\s+MirAnimation\.(?P<animation>\w+)\s*;")
    case_pattern = re.compile(r"case\s+MagicType\.(?P<magic>\w+)\s*:")
    for match in return_pattern.finditer(block):
        segment = block[cursor:match.start()]
        animation = match.group("animation")
        for case in case_pattern.finditer(segment):
            magic = case.group("magic")
            if magic in mapping:
                raise RuntimeError(f"duplicate GetMagicAnimation case: {magic}")
            mapping[magic] = animation
        cursor = match.end()
    if len(mapping) < 100:
        raise RuntimeError(f"unexpected GetMagicAnimation case count: {len(mapping)}")
    return mapping


def parse_player_libraries(libraries_text: str) -> list[dict]:
    pattern = re.compile(
        r"\[LibraryFile\.(?P<key>\w+)\]\s*=\s*@\"(?P<path>Data\\[^\"]+\.Zl)\""
    )
    rows = []
    seen = set()
    for match in pattern.finditer(libraries_text):
        key = match.group("key")
        if not key.startswith(PLAYER_LIBRARY_PREFIXES):
            continue
        if key in seen:
            continue
        seen.add(key)
        source_path = match.group("path").replace("\\", "/")
        rows.append({
            "libraryFile": key,
            "sourcePath": source_path,
            "fileName": Path(source_path).name,
        })
    if not any(row["libraryFile"] == "M_Hum" for row in rows):
        raise RuntimeError("M_Hum player library was not extracted")
    if not any(row["libraryFile"] == "WM_Hum" for row in rows):
        raise RuntimeError("WM_Hum player library was not extracted")
    return rows


def evaluate_selector_expression(expression: str, constants: dict[str, int]) -> int:
    normalized = expression
    for name, value in constants.items():
        normalized = re.sub(rf"\b{re.escape(name)}\b", str(value), normalized)
    if not re.fullmatch(r"[0-9+\-\s]+", normalized):
        raise RuntimeError(f"unsupported PlayerObject selector expression: {expression}")
    return int(eval(normalized, {"__builtins__": {}}, {}))


def parse_selector_map(player_text: str, name: str, constants: dict[str, int]) -> dict[str, str]:
    marker = f"Dictionary<int, LibraryFile> {name}"
    block = extract_block(player_text, marker)
    pattern = re.compile(r"\[(?P<expr>[^\]]+)\]\s*=\s*LibraryFile\.(?P<library>\w+)")
    result: dict[str, str] = {}
    for match in pattern.finditer(block):
        key = evaluate_selector_expression(match.group("expr").strip(), constants)
        result[str(key)] = match.group("library")
    if not result:
        raise RuntimeError(f"PlayerObject selector map is empty: {name}")
    return result


def parse_int_list(player_text: str, marker: str) -> list[int]:
    block = extract_block(player_text, marker)
    values = [int(value) for value in re.findall(r"(?<![A-Za-z0-9_])-?\d+", block)]
    if not values:
        raise RuntimeError(f"integer list is empty: {marker}")
    return values


def build_contract(zroot: Path, commit: str) -> dict:
    enum_path = zroot / "LibraryCore" / "Enum.cs"
    frame_path = zroot / "LibraryCore" / "FrameSet.cs"
    libraries_path = zroot / "LibraryCore" / "Libraries.cs"
    player_path = zroot / "Client" / "Models" / "PlayerObject.cs"
    map_object_path = zroot / "Client" / "Models" / "MapObject.cs"
    functions_path = zroot / "LibraryCore" / "Functions.cs"
    required = [enum_path, frame_path, libraries_path, player_path, map_object_path, functions_path]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise RuntimeError("missing pinned Zircon source: " + ", ".join(missing))

    enum_text = enum_path.read_text(encoding="utf-8-sig")
    frame_text = frame_path.read_text(encoding="utf-8-sig")
    libraries_text = libraries_path.read_text(encoding="utf-8-sig")
    player_text = player_path.read_text(encoding="utf-8-sig")
    map_text = map_object_path.read_text(encoding="utf-8-sig")
    functions_text = functions_path.read_text(encoding="utf-8-sig")

    draw_formula = "DrawFrame = FrameIndex + CurrentFrame.StartIndex + CurrentFrame.OffSet * (int)Direction;"
    if draw_formula not in map_text:
        raise RuntimeError("pinned MapObject draw-frame formula changed")
    if "if (Race == ObjectType.Player && CurrentAction == MirAction.Pushed)" not in map_text:
        raise RuntimeError("pinned Player Pushed frame override changed")

    constants: dict[str, int] = {}
    for name in ("FemaleOffSet", "AssassinOffSet", "RightHandOffSet"):
        match = re.search(rf"\b{name}\s*=\s*(\d+)", player_text)
        if not match:
            raise RuntimeError(f"PlayerObject constant not found: {name}")
        constants[name] = int(match.group(1))

    selector_maps = {
        name: parse_selector_map(player_text, name, constants)
        for name in ("ArmourList", "CostumeList", "WeaponList", "ShieldList", "HelmetList")
    }

    return {
        "schema": "origins.zircon.web-player-assets.v1",
        "zirconCommit": commit,
        "sourceHashes": {
            "Enum.cs": sha256(enum_path),
            "FrameSet.cs": sha256(frame_path),
            "Libraries.cs": sha256(libraries_path),
            "PlayerObject.cs": sha256(player_path),
            "MapObject.cs": sha256(map_object_path),
            "Functions.cs": sha256(functions_path),
        },
        "mirAnimation": {name: index for index, name in enumerate(parse_mir_animation(enum_text))},
        "playerFrames": parse_player_frames(frame_text),
        "magicAnimationMap": parse_magic_animation_map(functions_text),
        "playerLibraries": parse_player_libraries(libraries_text),
        "playerConstants": constants,
        "playerLibrarySelectors": selector_maps,
        "costumeShapeHideWeapon": parse_int_list(player_text, "CostumeShapeHideWeapon = new()"),
        "drawFrameFormula": "frameIndex + startIndex + offset * direction",
        "pushedPlayerFrameOverride": 0,
        "notes": [
            "All player frame definitions are extracted from FrameSet.Players.",
            "Magic-to-body-animation cases are extracted from Functions.GetMagicAnimation.",
            "Armour/Costume/Weapon/Shield/Helmet selectors are extracted from PlayerObject dictionaries.",
            "Costume weapon-hiding shapes are extracted from PlayerObject.",
            "Real PNG/atlas payload is generated only when the corresponding Zircon .Zl files are supplied.",
            "No Crystal fallback is permitted.",
        ],
    }


def write_outputs(contract: dict, json_path: Path, js_path: Path) -> None:
    json_path.parent.mkdir(parents=True, exist_ok=True)
    js_path.parent.mkdir(parents=True, exist_ok=True)
    rendered = json.dumps(contract, indent=2, ensure_ascii=False) + "\n"
    json_path.write_text(rendered, encoding="utf-8")
    js_payload = json.dumps(contract, indent=2, ensure_ascii=False)
    js_path.write_text(
        "// GENERATED from pinned Suprcode/Zircon. Do not edit by hand.\n"
        f"export const ZIRCON_PLAYER_ASSET_CONTRACT = Object.freeze({js_payload});\n"
        "export const ZIRCON_PLAYER_FRAMESET = ZIRCON_PLAYER_ASSET_CONTRACT.playerFrames;\n"
        "export const ZIRCON_MIR_ANIMATION = ZIRCON_PLAYER_ASSET_CONTRACT.mirAnimation;\n"
        "export const ZIRCON_MAGIC_ANIMATION_MAP = ZIRCON_PLAYER_ASSET_CONTRACT.magicAnimationMap;\n"
        "export const ZIRCON_PLAYER_LIBRARY_SELECTORS = ZIRCON_PLAYER_ASSET_CONTRACT.playerLibrarySelectors;\n"
        "export const ZIRCON_COSTUME_HIDE_WEAPON = ZIRCON_PLAYER_ASSET_CONTRACT.costumeShapeHideWeapon;\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--zircon-root", type=Path, required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--js-output", type=Path, required=True)
    args = parser.parse_args()
    contract = build_contract(args.zircon_root, args.commit)
    write_outputs(contract, args.json_output, args.js_output)
    print(
        f"Generated {len(contract['playerFrames'])} player animations, "
        f"{len(contract['magicAnimationMap'])} magic mappings, "
        f"{len(contract['playerLibraries'])} player libraries and "
        f"{sum(len(v) for v in contract['playerLibrarySelectors'].values())} selector entries."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
