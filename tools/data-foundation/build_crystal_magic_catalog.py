#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

CLASS_SPELLS = {
    "Warrior": ["Fencing","Slaying","Thrusting","HalfMoon","ShoulderDash","TwinDrakeBlade","Entrapment","FlamingSword","LionRoar","CrossHalfMoon","BladeAvalanche","ProtectionField","Rage","CounterAttack","SlashingBurst","Fury","ImmortalSkin"],
    "Wizard": ["FireBall","Repulsion","ElectricShock","GreatFireBall","HellFire","ThunderBolt","Teleport","FireBang","FireWall","Lightning","FrostCrunch","ThunderStorm","MagicShield","TurnUndead","Vampirism","IceStorm","FlameDisruptor","Mirroring","FlameField","Blizzard","MagicBooster","MeteorStrike","IceThrust","FastMove","StormEscape"],
    "Taoist": ["Healing","SpiritSword","Poisoning","SoulFireBall","SummonSkeleton","Hiding","MassHiding","SoulShield","Revelation","BlessedArmour","EnergyRepulsor","TrapHexagon","Purification","MassHealing","Hallucination","UltimateEnhancer","SummonShinsu","Reincarnation","SummonHolyDeva","Curse","Plague","PoisonCloud","EnergyShield","PetEnhancer","HealingCircle"],
    "Assassin": ["FatalSword","DoubleSlash","Haste","FlashDash","LightBody","HeavenlySword","FireBurst","Trap","PoisonSword","MoonLight","MPEater","SwiftFeet","DarkBody","Hemorrhage","CrescentSlash","MoonMist","CatTongue"],
    "Archer": ["Focus","StraightShot","DoubleShot","ExplosiveTrap","DelayedExplosion","Meditation","BackStep","ElementalShot","Concentration","Stonetrap","ElementalBarrier","SummonVampire","VampireShot","SummonToad","PoisonShot","CrippleShot","SummonSnakes","NapalmShot","OneWithNature","BindingShot","MentalState"],
    "Monk": ["JiBenGunFa","LuoHanGunFa","JinGangGunFa","DaMoGunFa","XiangLongGunFa","Taunt","TianLeiZhen","LuoHanZhen","ShiBuYiSha"],
}

CLASS_IDS = {"Warrior":1,"Wizard":2,"Taoist":3,"Assassin":4,"Archer":5,"Monk":6}
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
    raw = match.group(1)
    return float(raw) if "." in raw else int(raw)


def seed_name(body: str | None):
    if not body:
        return None
    match = re.search(r"\bName\s*=\s*(?:Tr\()?\s*\"([^\"]+)\"", body)
    return match.group(1) if match else None


def initializer_spell(body: str | None):
    if not body:
        return None
    match = re.search(r"\bSpell\s*=\s*Spell\.([A-Za-z0-9_]+)", body)
    return match.group(1) if match else None


def entry(spell: str, spell_id: int, body: str | None, repo: str, sha: str):
    icon = number(body, "Icon")
    levels = [number(body, f"Level{i}") for i in (1, 2, 3)]
    needs = [number(body, f"Need{i}") for i in (1, 2, 3)]
    assigned = initializer_spell(body)
    matches = assigned == spell if assigned is not None else False
    implemented = body is not None and matches and icon is not None and levels[0] is not None

    result = {
        "spell": spell,
        "spellId": spell_id,
        "sourceSeedName": seed_name(body),
        "sourceInitializerSpell": assigned,
        "sourceInitializerMatches": matches,
        "sourceImplemented": implemented,
        "iconId": int(icon) if icon is not None and implemented else None,
        "iconFrameNormal": int(icon) * 2 if icon is not None and implemented else None,
        "iconFramePressed": int(icon) * 2 + 1 if icon is not None and implemented else None,
        "requiredLevels": levels if implemented else [None, None, None],
        "experienceNeeds": needs if implemented else [None, None, None],
        "baseCost": number(body, "BaseCost") if implemented else None,
        "levelCost": number(body, "LevelCost") if implemented else None,
        "range": number(body, "Range") if implemented else None,
        "delayBase": number(body, "DelayBase") if implemented else None,
        "delayReduction": number(body, "DelayReduction") if implemented else None,
        "minBasePower": number(body, "MinBasePower") if implemented else None,
        "maxBasePower": number(body, "MaxBasePower") if implemented else None,
        "minLevelPower": number(body, "MinLevelPower") if implemented else None,
        "maxLevelPower": number(body, "MaxLevelPower") if implemented else None,
        "source": {"repo": repo, "path": "Server/MirEnvir/Envir.cs", "commit": sha},
    }
    if not implemented:
        reasons = []
        if body is None:
            reasons.append("MagicInfo seed is absent")
        if assigned is not None and assigned != spell:
            reasons.append(f"initializer assigns Spell.{assigned} instead of Spell.{spell}")
        if icon is None:
            reasons.append("Icon is not defined")
        if levels[0] is None:
            reasons.append("required levels are not defined")
        result["sourceIssue"] = "; ".join(reasons) + ". No missing value is invented."
    return result


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--crystal-enums", required=True, type=Path)
    ap.add_argument("--crystal-envir", required=True, type=Path)
    ap.add_argument("--monk-common", required=True, type=Path)
    ap.add_argument("--monk-envir", required=True, type=Path)
    ap.add_argument("--crystal-sha", required=True)
    ap.add_argument("--monk-sha", required=True)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()

    crystal_enum = parse_enum(read(args.crystal_enums))
    monk_enum = parse_enum(read(args.monk_common))
    crystal_blocks = parse_seed_blocks(read(args.crystal_envir))
    monk_blocks = parse_seed_blocks(read(args.monk_envir))

    classes = {}
    seen_ids = set()
    for class_name, spell_names in CLASS_SPELLS.items():
        is_monk = class_name == "Monk"
        enum = monk_enum if is_monk else crystal_enum
        blocks = monk_blocks if is_monk else crystal_blocks
        repo = "JevLOMCN/Crystal-Monk" if is_monk else "Suprcode/Crystal"
        sha = args.monk_sha if is_monk else args.crystal_sha
        spells = []
        for spell in spell_names:
            if spell not in enum:
                raise SystemExit(f"{class_name}.{spell}: missing from canonical Spell enum")
            spell_id = enum[spell]
            if spell_id in seen_ids:
                raise SystemExit(f"duplicate Spell id {spell_id}: {class_name}.{spell}")
            seen_ids.add(spell_id)
            spells.append(entry(spell, spell_id, blocks.get(spell), repo, sha))
        classes[class_name] = {
            "classId": CLASS_IDS[class_name],
            "requiredClassFlag": CLASS_FLAGS[class_name],
            "sourceRepo": repo,
            "spells": spells,
        }

    catalog = {
        "schemaVersion": 1,
        "authority": {
            "baseClasses": {"repo": "Suprcode/Crystal", "commit": args.crystal_sha},
            "monk": {"repo": "JevLOMCN/Crystal-Monk", "commit": args.monk_sha},
        },
        "iconContract": {"library": "MagIcon2.Lib", "normalFrame": "iconId * 2", "pressedFrame": "iconId * 2 + 1"},
        "classes": classes,
    }

    total = sum(len(value["spells"]) for value in classes.values())
    implemented = sum(1 for value in classes.values() for spell in value["spells"] if spell["sourceImplemented"])
    if total != 114:
        raise SystemExit(f"expected 114 spells, got {total}")
    if implemented != 113:
        raise SystemExit(f"expected 113 source-implemented spells, got {implemented}")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(catalog, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {args.out}: {total} spells / {implemented} source-implemented")


if __name__ == "__main__":
    main()
