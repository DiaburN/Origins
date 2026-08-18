#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

CLASS_SPELLS = {
    "Warrior": [
        "Fencing","Slaying","Thrusting","HalfMoon","ShoulderDash","TwinDrakeBlade","Entrapment","FlamingSword","LionRoar","CrossHalfMoon","BladeAvalanche","ProtectionField","Rage","CounterAttack","SlashingBurst","Fury","ImmortalSkin"
    ],
    "Wizard": [
        "FireBall","Repulsion","ElectricShock","GreatFireBall","HellFire","ThunderBolt","Teleport","FireBang","FireWall","Lightning","FrostCrunch","ThunderStorm","MagicShield","TurnUndead","Vampirism","IceStorm","FlameDisruptor","Mirroring","FlameField","Blizzard","MagicBooster","MeteorStrike","IceThrust","FastMove","StormEscape"
    ],
    "Taoist": [
        "Healing","SpiritSword","Poisoning","SoulFireBall","SummonSkeleton","Hiding","MassHiding","SoulShield","Revelation","BlessedArmour","EnergyRepulsor","TrapHexagon","Purification","MassHealing","Hallucination","UltimateEnhancer","SummonShinsu","Reincarnation","SummonHolyDeva","Curse","Plague","PoisonCloud","EnergyShield","PetEnhancer","HealingCircle"
    ],
    "Assassin": [
        "FatalSword","DoubleSlash","Haste","FlashDash","LightBody","HeavenlySword","FireBurst","Trap","PoisonSword","MoonLight","MPEater","SwiftFeet","DarkBody","Hemorrhage","CrescentSlash","MoonMist","CatTongue"
    ],
    "Archer": [
        "Focus","StraightShot","DoubleShot","ExplosiveTrap","DelayedExplosion","Meditation","BackStep","ElementalShot","Concentration","Stonetrap","ElementalBarrier","SummonVampire","VampireShot","SummonToad","PoisonShot","CrippleShot","SummonSnakes","NapalmShot","OneWithNature","BindingShot","MentalState"
    ],
    "Monk": [
        "JiBenGunFa","LuoHanGunFa","JinGangGunFa","DaMoGunFa","XiangLongGunFa","Taunt","TianLeiZhen","LuoHanZhen","ShiBuYiSha"
    ],
}

CLASS_FLAGS = {"Warrior":1,"Wizard":2,"Taoist":4,"Assassin":8,"Archer":16,"Monk":32}


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig", errors="replace")


def parse_enum(source: str) -> dict[str, int]:
    match = re.search(r"public\s+enum\s+Spell\s*:\s*byte\s*\{(?P<body>.*?)\n\}", source, re.S)
    if not match:
        raise SystemExit("Spell enum not found")
    result: dict[str, int] = {}
    for name, value in re.findall(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(\d+)\s*,?", match.group("body"), re.M):
        result[name] = int(value)
    return result


def parse_seed_blocks(source: str) -> dict[str, str]:
    # Each Crystal seed is one MagicExists guard followed by one MagicInfo initializer.
    pattern = re.compile(
        r"if\s*\(\s*!MagicExists\(Spell\.(?P<spell>[A-Za-z0-9_]+)\)\s*\)\s*"
        r"MagicInfoList\.Add\(new\s+MagicInfo\s*\{(?P<body>.*?)\}\s*\)\s*;",
        re.S,
    )
    blocks: dict[str, str] = {}
    for match in pattern.finditer(source):
        blocks.setdefault(match.group("spell"), match.group("body"))
    return blocks


def number(body: str | None, field: str):
    if not body:
        return None
    match = re.search(rf"\b{re.escape(field)}\s*=\s*(-?\d+(?:\.\d+)?)(?:[fFdDmM])?\b", body)
    if not match:
        return None
    value = match.group(1)
    return float(value) if "." in value else int(value)


def seed_name(body: str | None):
    if not body:
        return None
    match = re.search(r"\bName\s*=\s*(?:Tr\()?\s*\"([^\"]+)\"", body)
    return match.group(1) if match else None


def build_entry(spell: str, spell_id: int, body: str | None, repo: str, source_path: str):
    icon = number(body, "Icon")
    levels = [number(body, f"Level{i}") for i in (1,2,3)]
    needs = [number(body, f"Need{i}") for i in (1,2,3)]
    implemented = body is not None and icon is not None and levels[0] is not None
    entry = {
        "spell": spell,
        "spellId": spell_id,
        "displayKey": spell,
        "sourceSeedName": seed_name(body),
        "sourceImplemented": implemented,
        "iconId": int(icon) if icon is not None else None,
        "iconFrameNormal": int(icon) * 2 if icon is not None else None,
        "iconFramePressed": int(icon) * 2 + 1 if icon is not None else None,
        "requiredLevels": levels,
        "experienceNeeds": needs,
        "baseCost": number(body, "BaseCost"),
        "levelCost": number(body, "LevelCost"),
        "range": number(body, "Range"),
        "source": {"repo": repo, "path": source_path},
    }
    if not implemented:
        entry["sourceIssue"] = "Spell exists in the canonical enum but no complete MagicInfo seed is implemented in the audited source. No icon, level or runtime value is invented."
    return entry


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--crystal-enums", required=True, type=Path)
    ap.add_argument("--crystal-envir", required=True, type=Path)
    ap.add_argument("--monk-common", required=True, type=Path)
    ap.add_argument("--monk-envir", required=True, type=Path)
    ap.add_argument("--crystal-sha", required=True)
    ap.add_argument("--monk-sha", required=True)
    ap.add_argument("--zircon-sha", required=True)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()

    crystal_enum = parse_enum(read(args.crystal_enums))
    monk_enum = parse_enum(read(args.monk_common))
    crystal_blocks = parse_seed_blocks(read(args.crystal_envir))
    monk_blocks = parse_seed_blocks(read(args.monk_envir))

    classes = {}
    all_ids = set()
    for class_name, spell_names in CLASS_SPELLS.items():
        monk = class_name == "Monk"
        enum = monk_enum if monk else crystal_enum
        blocks = monk_blocks if monk else crystal_blocks
        repo = "JevLOMCN/Crystal-Monk" if monk else "Suprcode/Crystal"
        path = "Server/MirEnvir/Envir.cs"
        entries = []
        for spell in spell_names:
            if spell not in enum:
                raise SystemExit(f"{class_name}.{spell}: missing from canonical Spell enum")
            spell_id = enum[spell]
            if spell_id in all_ids:
                raise SystemExit(f"Duplicate spell id {spell_id}: {class_name}.{spell}")
            all_ids.add(spell_id)
            entries.append(build_entry(spell, spell_id, blocks.get(spell), repo, path))
        classes[class_name] = {
            "requiredClassFlag": CLASS_FLAGS[class_name],
            "sourceRepo": repo,
            "spells": entries,
        }

    catalog = {
        "schemaVersion": 2,
        "sources": {
            "zircon": {"repo":"Suprcode/Zircon","sha":args.zircon_sha,"magicDialog":"Client/Scenes/Views/MagicDialog.cs"},
            "crystal": {"repo":"Suprcode/Crystal","sha":args.crystal_sha,"spellEnum":"Shared/Enums.cs","magicInfo":"Server/MirEnvir/Envir.cs"},
            "monk": {"repo":"JevLOMCN/Crystal-Monk","sha":args.monk_sha,"spellEnum":"Common.cs","magicInfo":"Server/MirEnvir/Envir.cs"},
        },
        "uiContract": {
            "shell":"Zircon MagicDialog",
            "size":[419,511],
            "body":{"library":"Interface","index":164,"location":[0,66]},
            "cell":{"size":[369,54],"background":{"library":"Interface","index":165},"iconLocation":[9,9]},
            "scroll":{"library":"Interface","thumb":60,"up":61,"down":62},
            "classHeaders":{"Warrior":160,"Wizard":161,"Taoist":162,"Assassin":163,"Archer":None,"Monk":None},
            "classTabs":{"selected":[56,58,57],"deselected":[53,55,54]},
        },
        "iconContract": {
            "library":"MagIcon2.Lib",
            "normalFrame":"iconId * 2",
            "pressedFrame":"iconId * 2 + 1",
        },
        "runtimeFields": ["currentMagicLevel","currentExperience","keybind","cooldown","playerUnlockState"],
        "classes": classes,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(catalog, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {args.out}: {sum(len(v['spells']) for v in classes.values())} spells")


if __name__ == "__main__":
    main()
