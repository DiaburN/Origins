#!/usr/bin/env python3
"""Inventory manual Zircon draw hooks for every reconstructed source window.

A normal DX control is covered by the shared renderer. Hooks such as root Draw,
BeforeChildrenDraw, OnAfterDraw and child BeforeDraw can bypass that renderer and
must be classified as either deterministic source artwork or runtime-only data.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

HOOKS = {
    "OVERRIDE_DRAW": re.compile(r"\boverride\s+void\s+Draw\s*\("),
    "OVERRIDE_BEFORE_CHILDREN": re.compile(r"\boverride\s+void\s+BeforeChildrenDraw\s*\("),
    "OVERRIDE_ON_AFTER_DRAW": re.compile(r"\boverride\s+void\s+OnAfterDraw\s*\("),
    "BEFORE_CHILDREN_EVENT": re.compile(r"\bBeforeChildrenDraw\s*\+="),
    "BEFORE_DRAW_EVENT": re.compile(r"\bBeforeDraw\s*\+="),
    "AFTER_DRAW_EVENT": re.compile(r"\bAfterDraw\s*\+="),
}

POLICIES = {
    "MainPanel": ("MIXED_RUNTIME_HUD", "player HP/MP/FP/focus/stats runtime; indexed HUD chrome deterministic"),
    "MiniMapDialog": ("RUNTIME_MAP_DRAW", "map texture, player/NPC/object markers depend on current map runtime"),
    "BigMapDialog": ("RUNTIME_MAP_DRAW", "selected map texture, NPC/monster markers and current-map title depend on runtime"),
    "CharacterDialog": ("MIXED_PLAYER_PREVIEW", "ProgUse base/anchor deterministic; hair/equipment/player layers runtime"),
    "InspectDialog": ("MIXED_PLAYER_PREVIEW", "inspection body base deterministic; inspected equipment/player layers runtime"),
    "EditCharacterDialog": ("MIXED_PLAYER_PREVIEW", "ProgUse base and local hair/gender state are source-backed; armour image is read from the current GameScene CharacterBox equipment grid"),
    "NewCharacterDialog": ("LOCAL_CHARACTER_CREATION_PREVIEW", "preview is driven only by local class/gender/hair/colour controls with fixed source indices; no server/player payload is pre-created"),
    "GuildDialog": ("MIXED_GUILD_RUNTIME", "window chrome deterministic; guild crest/style/member data runtime"),
    "RankingDialog": ("RUNTIME_RANKING_DRAW", "ranking rows/inspect preview and values depend on ranking runtime data"),
    "InventoryDialog": ("RUNTIME_INVENTORY_FILL", "bag grid chrome deterministic; weight bar fill/currency/item data runtime"),
    "MonsterDialog": ("RUNTIME_MONSTER_HEALTH_DRAW", "manual health fill depends on Monster ObjectID, companion state and GameScene DataDictionary health values"),
    "GroupDialog": ("RUNTIME_GROUP_DRAW", "group rows/health/runtime group membership drive manual child drawing"),
    "GroupHealthDialog": ("RUNTIME_GROUP_HEALTH", "health rows and member state are created/updated from current group runtime"),
    "SelectDialog": ("RUNTIME_CHARACTER_SELECT_PREVIEW", "selected character body/equipment preview comes from select-scene runtime data"),
    "NPCDialog": ("DETERMINISTIC_CUSTOM_FRAME", "GameInter 380/381/382 custom frame reconstructed; page rows runtime"),
    "NPCAdoptCompanionDialog": ("RUNTIME_COMPANION_MODEL_DRAW", "OnAfterDraw renders CompanionDisplay shadow/body only when a runtime MonsterObject companion display exists"),
    "NPCCompanionStorageDialog": ("RUNTIME_NPC_COMPANION_BARS", "selected companion experience/hunger fills and values depend on runtime companion data"),
    "NPCWeddingRingDialog": ("DETERMINISTIC_EMPTY_CELL_HINT", "empty linked ring cell draws Interface #31 at 20% opacity; linked item runtime"),
    "NPCAccessoryResetDialog": ("DETERMINISTIC_EMPTY_CELL_HINT", "empty linked accessory cell draws Interface #31 at 20% opacity; linked item runtime"),
    "CompanionDialog": ("MIXED_COMPANION_DRAW", "Interface 99-102 empty-slot hints deterministic; model/bars/values runtime"),
    "NPCSocketDialog": ("RUNTIME_LINKED_ITEM_DRAW", "target inventory item and socket state runtime; animations source-indexed"),
    "FishingDialog": ("RUNTIME_FISHING_DRAW", "cast/fish state and line/catch runtime"),
    "FishingCatchDialog": ("RUNTIME_FISHING_DRAW", "pointer visibility/position and fish state runtime; neutral hidden contract"),
    "DXColourPicker": ("DETERMINISTIC_LOCAL_PALETTE", "AfterDraw presents the client-generated colour palette texture; selection is local UI state and carries no server/runtime payload"),
}


def matching_brace(text: str, opening: int) -> int:
    depth = 0; in_string = False; in_char = False; escaped = False; line_comment = False; block_comment = False
    i = opening
    while i < len(text):
        c = text[i]; n = text[i + 1] if i + 1 < len(text) else ""
        if line_comment:
            if c == "\n": line_comment = False
            i += 1; continue
        if block_comment:
            if c == "*" and n == "/": block_comment = False; i += 2; continue
            i += 1; continue
        if in_char:
            if escaped: escaped = False
            elif c == "\\": escaped = True
            elif c == "'": in_char = False
            i += 1; continue
        if in_string:
            if escaped: escaped = False
            elif c == "\\": escaped = True
            elif c == '"': in_string = False
            i += 1; continue
        if c == "/" and n == "/": line_comment = True; i += 2; continue
        if c == "/" and n == "*": block_comment = True; i += 2; continue
        if c == '"': in_string = True; i += 1; continue
        if c == "'": in_char = True; i += 1; continue
        if c == "{": depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0: return i
        i += 1
    raise ValueError("unbalanced class body")


def class_body(text: str, class_name: str) -> str:
    match = re.search(rf"\bclass\s+{re.escape(class_name)}\b[^{{]*\{{", text)
    if not match:
        return ""
    opening = text.find("{", match.start())
    return text[opening + 1:matching_brace(text, opening)]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--zircon-root", type=Path, required=True)
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()

    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    entries = []
    unclassified = []
    missing_source_body = []

    for item in [*(spec.get("windows") or []), *(spec.get("nestedWindows") or [])]:
        source_path = item.get("sourcePath")
        class_name = item.get("class") or item.get("sourceClass")
        if not source_path or not class_name:
            continue
        path = args.zircon_root / source_path
        if not path.exists():
            continue
        body = class_body(path.read_text(encoding="utf-8-sig"), str(class_name))
        if not body:
            missing_source_body.append((item.get("field") or item.get("id"), class_name, source_path))
            continue
        hooks = sorted(name for name, pattern in HOOKS.items() if pattern.search(body))
        if not hooks:
            continue
        policy = POLICIES.get(str(class_name))
        row = {
            "id": item.get("id"),
            "field": item.get("field"),
            "sourceClass": class_name,
            "sourcePath": source_path,
            "hooks": hooks,
            "policy": policy[0] if policy else None,
            "reason": policy[1] if policy else None,
        }
        entries.append(row)
        if not policy:
            unclassified.append(row)

    spec["customDrawAudit"] = {
        "windowCountWithManualDrawHooks": len(entries),
        "entries": entries,
        "unclassified": unclassified,
        "missingSourceBodies": missing_source_body,
        "policy": "every source window with manual draw hooks must be classified",
    }
    args.spec.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print("Custom-draw windows:", len(entries))
    for row in entries:
        print("CUSTOM_DRAW", row["sourceClass"], ",".join(row["hooks"]), "=>", row["policy"] or "UNCLASSIFIED")
    print("Unclassified custom-draw windows:", len(unclassified))
    if missing_source_body:
        print("Missing exact class bodies:", missing_source_body)
    if args.strict and unclassified:
        raise SystemExit("Unclassified Zircon custom-draw windows: " + ", ".join(sorted({str(r['sourceClass']) for r in unclassified})))


if __name__ == "__main__":
    main()
