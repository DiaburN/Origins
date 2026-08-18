#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

EXPECTED = {"Warrior":17,"Wizard":25,"Taoist":25,"Assassin":17,"Archer":21,"Monk":9}
RUNTIME_FORBIDDEN = {"currentMagicLevel","currentExperience","keybind","cooldown","playerUnlockState"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--catalog", required=True, type=Path)
    ap.add_argument("--icons", type=Path)
    args = ap.parse_args()

    catalog = json.loads(args.catalog.read_text(encoding="utf-8"))
    classes = catalog.get("classes", {})
    if set(classes) != set(EXPECTED):
        raise SystemExit(f"Class set mismatch: {sorted(classes)}")

    ids = set()
    total = 0
    incomplete = []
    for class_name, expected_count in EXPECTED.items():
        spells = classes[class_name].get("spells", [])
        if len(spells) != expected_count:
            raise SystemExit(f"{class_name}: expected {expected_count}, got {len(spells)}")
        total += len(spells)
        names = set()
        for spell in spells:
            name = spell["spell"]
            if name in names:
                raise SystemExit(f"{class_name}: duplicate spell name {name}")
            names.add(name)
            spell_id = spell["spellId"]
            if spell_id in ids:
                raise SystemExit(f"Duplicate spellId {spell_id}")
            ids.add(spell_id)
            if any(field in spell for field in RUNTIME_FORBIDDEN):
                raise SystemExit(f"{class_name}.{name}: runtime state leaked into static catalog")
            if not spell.get("sourceImplemented"):
                incomplete.append(f"{class_name}.{name}")
                if spell.get("iconId") is not None:
                    raise SystemExit(f"{class_name}.{name}: incomplete source cannot have invented icon")
            else:
                icon = spell.get("iconId")
                if icon is None:
                    raise SystemExit(f"{class_name}.{name}: implemented spell has no iconId")
                if spell.get("iconFrameNormal") != icon * 2 or spell.get("iconFramePressed") != icon * 2 + 1:
                    raise SystemExit(f"{class_name}.{name}: MagIcon2 frame mapping broken")
                if not all(isinstance(v, int) for v in spell.get("requiredLevels", [])):
                    raise SystemExit(f"{class_name}.{name}: required levels missing")
                if args.icons:
                    for frame in (spell["iconFrameNormal"], spell["iconFramePressed"]):
                        path = args.icons / f"{frame:05d}.png"
                        if not path.is_file() or path.stat().st_size <= 0:
                            raise SystemExit(f"{class_name}.{name}: missing extracted real icon frame {frame}")

    if total != 114:
        raise SystemExit(f"Expected 114 spells, got {total}")
    if incomplete != ["Wizard.FastMove"]:
        raise SystemExit(f"Unexpected source-incomplete spells: {incomplete}")

    monk = {s["spell"]:s for s in classes["Monk"]["spells"]}
    for name in ("JiBenGunFa","LuoHanGunFa","JinGangGunFa","DaMoGunFa","XiangLongGunFa","Taunt","TianLeiZhen"):
        if monk[name]["iconId"] != 42:
            raise SystemExit(f"Monk source icon reuse changed for {name}")
    for name in ("LuoHanZhen","ShiBuYiSha"):
        if monk[name]["iconId"] != 23:
            raise SystemExit(f"Monk source icon reuse changed for {name}")

    print("MAGIC QA PASS")
    print("classes=6 spells=114 implemented=113 sourceIncomplete=Wizard.FastMove")


if __name__ == "__main__":
    main()
