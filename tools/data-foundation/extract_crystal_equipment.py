#!/usr/bin/env python3
"""Extract class-specific Crystal equipment from Server.MirDB.

The importer deliberately keeps Crystal identity/balance simple:
- original item name;
- original requirement;
- original class mask;
- flat core stats (AC/MAC/DC/MC/SC, Accuracy, Agility, HP, MP);
- all remaining source stats preserved in metadata for later opt-in.

Runtime item behaviour is ORIGINS/Zircon-style and is not inferred from Crystal.
"""
from __future__ import annotations

import argparse
import json
import re
import struct
from collections import defaultdict
from pathlib import Path

CLASS_BITS = {
    1: (1, "warrior"),
    2: (2, "wizard"),
    4: (3, "taoist"),
    8: (4, "assassin"),
    16: (5, "archer"),
    32: (6, "monk"),
}

# Crystal ItemType values used by wearable equipment.
ITEM_TYPES = {
    1: ("Weapon", "weapon", ("weapon",)),
    2: ("Armour", "armour", ("armour",)),
    4: ("Helmet", "helmet", ("helmet",)),
    5: ("Necklace", "necklace", ("necklace",)),
    6: ("Bracelet", "bracelet", ("bracelet_left", "bracelet_right")),
    7: ("Ring", "ring", ("ring_left", "ring_right")),
    8: ("Amulet", "amulet", ("amulet",)),
    9: ("Belt", "belt", ("belt",)),
    10: ("Boots", "boots", ("shoes",)),
    12: ("Torch", "torch", ("torch",)),
}

STAT_NAMES = {
    0: "MinAC", 1: "MaxAC", 2: "MinMAC", 3: "MaxMAC",
    4: "MinDC", 5: "MaxDC", 6: "MinMC", 7: "MaxMC",
    8: "MinSC", 9: "MaxSC", 10: "Accuracy", 11: "Agility",
    12: "HP", 13: "MP", 14: "AttackSpeed", 15: "Luck",
    16: "BagWeight", 17: "HandWeight", 18: "WearWeight",
    19: "Reflect", 20: "Strong", 21: "Holy", 22: "Freezing",
    23: "PoisonAttack", 30: "MagicResist", 31: "PoisonResist",
    32: "HealthRecovery", 33: "SpellRecovery", 34: "PoisonRecovery",
    35: "CriticalRate", 36: "CriticalDamage", 40: "MaxACRatePercent",
    41: "MaxMACRatePercent", 42: "MaxDCRatePercent", 43: "MaxMCRatePercent",
    44: "MaxSCRatePercent", 45: "AttackSpeedRatePercent", 46: "HPRatePercent",
    47: "MPRatePercent", 48: "HPDrainRatePercent", 100: "ExpRatePercent",
    101: "ItemDropRatePercent", 102: "GoldDropRatePercent", 103: "MineRatePercent",
    104: "GemRatePercent", 105: "FishRatePercent", 106: "CraftRatePercent",
    107: "SkillGainMultiplier", 108: "AttackBonus", 120: "LoverExpRatePercent",
    121: "MentorDamageRatePercent", 123: "MentorExpRatePercent",
    124: "DamageReductionPercent", 125: "EnergyShieldPercent",
    126: "EnergyShieldHPGain", 127: "ManaPenaltyPercent",
    128: "TeleportManaPenaltyPercent", 129: "Hero",
}

# User requested the first imported progression to stay flat/simple. Extra source
# stats remain preserved in metadata and can be enabled later without re-reading DB.
CORE_STAT_IDS = set(range(0, 14))


class Reader:
    def __init__(self, data: bytes):
        self.data = data
        self.pos = 0

    def _read(self, n: int) -> bytes:
        out = self.data[self.pos:self.pos + n]
        if len(out) != n:
            raise EOFError(f"Unexpected EOF at {self.pos}, wanted {n} bytes")
        self.pos += n
        return out

    def unpack(self, fmt: str):
        size = struct.calcsize(fmt)
        return struct.unpack(fmt, self._read(size))[0]

    def i16(self): return self.unpack("<h")
    def u16(self): return self.unpack("<H")
    def i32(self): return self.unpack("<i")
    def u32(self): return self.unpack("<I")
    def u8(self): return self.unpack("<B")
    def bool(self): return self.u8() != 0

    def seven_bit_int(self) -> int:
        value = 0
        shift = 0
        while True:
            b = self.u8()
            value |= (b & 0x7F) << shift
            if not (b & 0x80):
                return value
            shift += 7
            if shift >= 35:
                raise ValueError("Invalid .NET 7-bit encoded integer")

    def string(self) -> str:
        n = self.seven_bit_int()
        return self._read(n).decode("utf-8", errors="strict")


def skip_safe_zone(r: Reader):
    r.i32(); r.i32(); r.u16(); r.bool()


def skip_respawn(r: Reader, version: int):
    r.i32(); r.i32(); r.i32(); r.u16(); r.u16(); r.u16(); r.u8(); r.string()
    if version > 67:
        r.u16(); r.i32(); r.bool(); r.u16()


def skip_movement(r: Reader, version: int):
    r.i32(); r.i32(); r.i32(); r.i32(); r.i32(); r.bool(); r.bool()
    if version >= 69:
        r.i32()
    if version >= 95:
        r.bool(); r.i32()


def skip_mine_zone(r: Reader):
    r.i32(); r.i32(); r.u16(); r.u8()


def skip_map(r: Reader, version: int):
    r.i32(); r.string(); r.string(); r.u16(); r.u8(); r.u16()
    for _ in range(r.i32()): skip_safe_zone(r)
    for _ in range(r.i32()): skip_respawn(r, version)
    for _ in range(r.i32()): skip_movement(r, version)

    r.bool(); r.bool(); r.string()  # teleport/reconnect/reconnect map
    for _ in range(10): r.bool()    # random..names
    r.bool()                        # Fight
    r.bool(); r.i32()               # Fire/damage
    r.bool(); r.i32()               # Lightning/damage
    r.u8()                          # MapDarkLight
    for _ in range(r.i32()): skip_mine_zone(r)
    r.u8()                          # MineIndex
    r.bool(); r.bool(); r.bool()    # NoMount, NeedBridle, NoFight
    r.u16()                         # Music
    if version >= 78: r.bool()      # NoTownTeleport
    if version >= 79: r.bool()      # NoReincarnation
    if version >= 110: r.u16()      # WeatherParticles
    if version >= 111:
        r.bool(); r.u8()            # GT, GTIndex
    if version >= 114:
        r.bool(); r.bool(); r.bool(); r.bool(); r.bool()
        r.i32(); r.bool(); r.bool(); r.i32()


def read_stats(r: Reader, version: int):
    if version <= 84:
        raise ValueError("This importer intentionally supports modern Crystal DB versions (>84) only")
    count = r.i32()
    if count < 0 or count > 10000:
        raise ValueError(f"Invalid Stats count {count} at {r.pos}")
    out = {}
    for _ in range(count):
        sid = r.u8(); amount = r.i32()
        out[sid] = amount
    return out


def read_item(r: Reader, version: int):
    item = {
        "index": r.i32(),
        "name": r.string(),
        "type": r.u8(),
        "grade": r.u8(),
        "required_type": r.u8(),
        "required_class": r.u8(),
        "required_gender": r.u8(),
        "set_id": r.u8(),
        "shape": r.i16(),
        "weight": r.u8(),
        "light": r.u8(),
        "required_amount": r.u8(),
        "image": r.u16(),
        "durability": r.u16(),
    }
    if version <= 84:
        item["stack_size"] = r.u32()
    else:
        item["stack_size"] = r.u16()
    item["price"] = r.u32()

    if version <= 84:
        raise ValueError("Modern DB required; legacy item stats are not imported by this tool")

    item["start_item"] = r.bool()
    item["effect"] = r.u8()
    item["flags"] = r.u8()
    item["bind"] = r.i16()
    item["unique"] = r.i16()
    item["random_stats_id"] = r.u8()
    item["can_fast_run"] = r.bool()
    item["can_awakening"] = r.bool()
    item["slots"] = r.u8() if version > 83 else 0
    item["stats"] = read_stats(r, version)
    has_tooltip = r.bool()
    item["tooltip"] = r.string() if has_tooltip else ""
    return item


def parse_enum_names(path: Path, enum_name: str):
    text = path.read_text(encoding="utf-8-sig", errors="replace")
    m = re.search(rf"public\s+enum\s+{re.escape(enum_name)}(?:\s*:\s*\w+)?\s*\{{(.*?)\n\}}", text, re.S)
    if not m:
        return {}
    result = {}
    current = -1
    for raw in m.group(1).splitlines():
        line = raw.split("//", 1)[0].strip().rstrip(",")
        if not line or line.startswith("["):
            continue
        if "=" in line:
            name, value = [x.strip() for x in line.split("=", 1)]
            try:
                current = int(value, 0)
            except ValueError:
                continue
        else:
            name = line.strip()
            current += 1
        if re.match(r"^[A-Za-z_]\w*$", name):
            result[current] = name
    return result


def sql_quote(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def classes_for_mask(mask: int):
    # Standard Crystal uses 31 for all five built-in classes. 0 is also treated
    # as unrestricted by several forks. Those generic items are intentionally
    # excluded from this first *class-set/progression* import.
    if mask in (0, 31, 63):
        return []
    return [v for bit, v in CLASS_BITS.items() if mask & bit]


def parse_db(db: Path):
    r = Reader(db.read_bytes())
    version = r.i32(); custom = r.i32()
    if version <= 84:
        raise ValueError(f"Server.MirDB v{version} is too old for this importer")
    # Server DB counters
    header = {
        "version": version, "custom_version": custom,
        "map_index": r.i32(), "item_index": r.i32(), "monster_index": r.i32(),
        "npc_index": r.i32(), "quest_index": r.i32(),
    }
    if version >= 63: header["gameshop_index"] = r.i32()
    if version >= 66: header["conquest_index"] = r.i32()
    if version > 67: header["respawn_index"] = r.i32()

    map_count = r.i32()
    for _ in range(map_count): skip_map(r, version)

    item_count = r.i32()
    items = [read_item(r, version) for _ in range(item_count)]
    header["map_count"] = map_count
    header["item_count"] = item_count
    header["items_end_offset"] = r.pos
    return header, items


def build_equipment(items, enum_names):
    equipment = []
    for item in items:
        type_info = ITEM_TYPES.get(item["type"])
        if not type_info:
            continue
        classes = classes_for_mask(item["required_class"])
        if not classes:
            continue  # generic/non-class item stays in Zircon catalogue phase
        type_name, family, equip_slots = type_info
        all_stats = {STAT_NAMES.get(k, f"Stat{k}"): v for k, v in item["stats"].items() if v != 0}
        core_stats = {STAT_NAMES.get(k, f"Stat{k}"): v for k, v in item["stats"].items() if k in CORE_STAT_IDS and v != 0}
        extra_stats = {STAT_NAMES.get(k, f"Stat{k}"): v for k, v in item["stats"].items() if k not in CORE_STAT_IDS and v != 0}
        item = dict(item)
        item.update({
            "type_name": type_name,
            "family": family,
            "equip_slots": list(equip_slots),
            "classes": [{"id": cid, "code": code} for cid, code in classes],
            "required_type_name": enum_names.get("RequiredType", {}).get(item["required_type"], f"RequiredType{item['required_type']}"),
            "grade_name": enum_names.get("ItemGrade", {}).get(item["grade"], f"Grade{item['grade']}"),
            "set_name": enum_names.get("ItemSet", {}).get(item["set_id"], f"Set{item['set_id']}"),
            "core_stats": core_stats,
            "extra_stats_preserved": extra_stats,
            "all_stats": all_stats,
        })
        equipment.append(item)
    return equipment


def build_report(header, equipment):
    by_class = defaultdict(lambda: {"items": 0, "families": defaultdict(int), "max_level": None, "level_items": 0})
    monk_items = 0
    for item in equipment:
        for cls in item["classes"]:
            rec = by_class[cls["code"]]
            rec["items"] += 1
            rec["families"][item["family"]] += 1
            if item["required_type_name"].lower() == "level":
                rec["level_items"] += 1
                rec["max_level"] = max(rec["max_level"] or 0, item["required_amount"])
            if cls["code"] == "monk": monk_items += 1
    serial = {}
    for code in ("warrior", "wizard", "taoist", "assassin", "archer", "monk"):
        rec = by_class[code]
        serial[code] = {
            "items": rec["items"],
            "level_items": rec["level_items"],
            "max_required_level": rec["max_level"],
            "families": dict(sorted(rec["families"].items())),
        }
    return {
        "database": header,
        "class_specific_equipment_items": len(equipment),
        "monk_items_detected_in_source_db": monk_items,
        "classes": serial,
        "policy": {
            "identity": "Crystal original names/requirements",
            "runtime": "Zircon-style ORIGINS item system",
            "imported_stats": "flat core source stats only",
            "extra_source_stats": "preserved in metadata for later opt-in",
            "generic_items": "not imported here; Zircon catalogue phase",
        },
    }


def build_sql(equipment, source_commit: str):
    lines = ["BEGIN;", ""]
    source_repo = "Suprcode/Crystal.Database"
    source_path = "Jev/Server.MirDB"

    for item in equipment:
        key = f"crystal.item.{item['index']}"
        metadata = {
            "crystal_grade": item["grade_name"],
            "crystal_set_id": item["set_id"],
            "crystal_set_name": item["set_name"],
            "crystal_effect": item["effect"],
            "crystal_bind": item["bind"],
            "crystal_unique": item["unique"],
            "crystal_light": item["light"],
            "crystal_random_stats_id": item["random_stats_id"],
            "crystal_slots": item["slots"],
            "crystal_tooltip": item["tooltip"],
            "source_stats_all": item["all_stats"],
            "extra_stats_preserved": item["extra_stats_preserved"],
        }
        lines.append(
            "INSERT INTO content.item_definitions "
            "(game_key,item_name,item_type,required_class_mask,required_gender,required_type,required_amount,shape,image_index,durability,price,weight,stack_size,start_item,rarity,source_system,source_item_id,source_repo,source_path,source_commit,class_restriction_mode,runtime_source,metadata) VALUES (" +
            ",".join([
                sql_quote(key), sql_quote(item["name"]), sql_quote(item["type_name"]), str(item["required_class"]),
                str(item["required_gender"]), sql_quote(item["required_type_name"]), str(item["required_amount"]),
                str(item["shape"]), str(item["image"]), str(item["durability"]), str(item["price"]), str(item["weight"]),
                str(item["stack_size"]), "true" if item["start_item"] else "false", sql_quote(item["grade_name"]),
                sql_quote("crystal"), str(item["index"]), sql_quote(source_repo), sql_quote(source_path), sql_quote(source_commit),
                sql_quote("restricted"), sql_quote("zircon"), sql_quote(json.dumps(metadata, ensure_ascii=False, separators=(",", ":"))) + "::jsonb"
            ]) +
            ") ON CONFLICT (game_key) DO NOTHING;"
        )
        for stat, amount in sorted(item["core_stats"].items()):
            lines.append(
                "INSERT INTO content.item_stats(item_definition_id,stat_code,amount) "
                f"SELECT id,{sql_quote(stat)},{int(amount)} FROM content.item_definitions WHERE game_key={sql_quote(key)} "
                "ON CONFLICT (item_definition_id,stat_code) DO UPDATE SET amount=EXCLUDED.amount;"
            )
        for cls in item["classes"]:
            lines.append(
                "INSERT INTO content.item_allowed_classes(item_definition_id,class_id,source_system,source_item_id,source_repo,source_path,source_commit) "
                f"SELECT id,{cls['id']},'crystal',{item['index']},{sql_quote(source_repo)},{sql_quote(source_path)},{sql_quote(source_commit)} "
                f"FROM content.item_definitions WHERE game_key={sql_quote(key)} ON CONFLICT DO NOTHING;"
            )
        for slot in item["equip_slots"]:
            lines.append(
                "INSERT INTO content.item_equip_slots(item_definition_id,slot_code) "
                f"SELECT id,{sql_quote(slot)} FROM content.item_definitions WHERE game_key={sql_quote(key)} ON CONFLICT DO NOTHING;"
            )
        lines.append("")

    # Progression tiers are deterministic per class/family: requirement amount,
    # then source item id. This is data organisation, not stat modification.
    grouped = defaultdict(list)
    for item in equipment:
        for cls in item["classes"]:
            grouped[(cls["id"], cls["code"], item["family"])].append(item)
    for (class_id, _, family), items in sorted(grouped.items()):
        items.sort(key=lambda x: (0 if x["required_type_name"].lower() == "level" else 1, x["required_amount"], x["index"]))
        for tier, item in enumerate(items, start=1):
            key = f"crystal.item.{item['index']}"
            lines.append(
                "INSERT INTO content.equipment_progression "
                "(class_id,equipment_family,tier_order,item_definition_id,original_name,required_type,required_amount,source_system,source_item_id,source_set_id,source_repo,source_path,source_commit) "
                f"SELECT {class_id},{sql_quote(family)},{tier},id,{sql_quote(item['name'])},{sql_quote(item['required_type_name'])},{item['required_amount']},'crystal',{item['index']},{item['set_id']},{sql_quote(source_repo)},{sql_quote(source_path)},{sql_quote(source_commit)} "
                f"FROM content.item_definitions WHERE game_key={sql_quote(key)} ON CONFLICT DO NOTHING;"
            )

    # Preserve Crystal ItemSet membership when set_id != 0. Set names come from
    # the source enum; no invented set bonuses are created.
    set_items = defaultdict(list)
    for item in equipment:
        if item["set_id"]:
            set_items[(item["set_id"], item["set_name"])].append(item)
    for (set_id, set_name), items in sorted(set_items.items()):
        set_key = f"crystal.set.{set_id}"
        lines.append(
            "INSERT INTO content.item_set_definitions(game_key,set_name,source_system,source_set_id,source_repo,source_path,source_commit) VALUES (" +
            ",".join([sql_quote(set_key),sql_quote(set_name),"'crystal'",str(set_id),sql_quote(source_repo),sql_quote(source_path),sql_quote(source_commit)]) +
            ") ON CONFLICT (game_key) DO NOTHING;"
        )
        for item in items:
            item_key = f"crystal.item.{item['index']}"
            lines.append(
                "INSERT INTO content.item_set_members(item_set_id,item_definition_id) "
                f"SELECT s.id,i.id FROM content.item_set_definitions s,content.item_definitions i "
                f"WHERE s.game_key={sql_quote(set_key)} AND i.game_key={sql_quote(item_key)} ON CONFLICT DO NOTHING;"
            )

    lines.extend(["", "COMMIT;", ""])
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", type=Path, required=True)
    ap.add_argument("--enums", type=Path, required=True)
    ap.add_argument("--source-commit", required=True)
    ap.add_argument("--out-json", type=Path, required=True)
    ap.add_argument("--out-sql", type=Path, required=True)
    args = ap.parse_args()

    header, items = parse_db(args.db)
    enum_names = {
        name: parse_enum_names(args.enums, name)
        for name in ("RequiredType", "ItemGrade", "ItemSet")
    }
    equipment = build_equipment(items, enum_names)
    report = build_report(header, equipment)
    report["items"] = equipment

    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_sql.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    args.out_sql.write_text(build_sql(equipment, args.source_commit), encoding="utf-8")

    print(json.dumps({
        "db_version": header["version"],
        "source_items": header["item_count"],
        "class_equipment": len(equipment),
        "classes": report["classes"],
        "monk_items_detected": report["monk_items_detected_in_source_db"],
    }, indent=2))


if __name__ == "__main__":
    main()
