#!/usr/bin/env python3
import json
import pathlib
import sys

EXPECTED = {
    "Warrior": 17,
    "Wizard": 25,
    "Taoist": 25,
    "Assassin": 17,
    "Archer": 21,
    "Monk": 9,
}
EXPECTED_TOTAL = 114
EXPECTED_MONK = {
    161: "JiBenGunFa",
    162: "LuoHanGunFa",
    163: "JinGangGunFa",
    164: "DaMoGunFa",
    165: "XiangLongGunFa",
    166: "Taunt",
    167: "TianLeiZhen",
    168: "LuoHanZhen",
    169: "ShiBuYiSha",
}

path = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "database/magic/crystal-playable-spells.json")
data = json.loads(path.read_text(encoding="utf-8"))
classes = data["classes"]
errors = []

for name, expected_count in EXPECTED.items():
    rows = classes.get(name)
    if rows is None:
        errors.append(f"missing class {name}")
        continue
    if len(rows) != expected_count:
        errors.append(f"{name}: expected {expected_count}, found {len(rows)}")

all_rows = [row for name in EXPECTED for row in classes.get(name, [])]
if len(all_rows) != EXPECTED_TOTAL:
    errors.append(f"playable total: expected {EXPECTED_TOTAL}, found {len(all_rows)}")

ids = [int(row["id"]) for row in all_rows]
if len(ids) != len(set(ids)):
    errors.append("duplicate playable spell IDs")

pairs = {(name, row["name"]) for name in EXPECTED for row in classes.get(name, [])}
if len(pairs) != len(all_rows):
    errors.append("duplicate spell name inside a class")

monk = {int(row["id"]): row["name"] for row in classes.get("Monk", [])}
if monk != EXPECTED_MONK:
    errors.append(f"Monk catalogue mismatch: {monk}")

scope = data.get("scope", {})
if scope.get("requiredPlayableSpellCount") != EXPECTED_TOTAL:
    errors.append("scope.requiredPlayableSpellCount must be 114")
if scope.get("includeMonk") is not True:
    errors.append("scope.includeMonk must be true")
if data.get("source", {}).get("monk") != "JevLOMCN/Crystal-Monk":
    errors.append("Crystal-Monk source is not pinned")
if not data.get("source", {}).get("monkCommit"):
    errors.append("Crystal-Monk commit is not pinned")

if errors:
    print("Crystal playable spell catalogue FAILED")
    for error in errors:
        print(f"- {error}")
    raise SystemExit(1)

print("Crystal playable spell catalogue OK")
for name, expected_count in EXPECTED.items():
    print(f"- {name}: {expected_count}")
print(f"- total: {EXPECTED_TOTAL}")
