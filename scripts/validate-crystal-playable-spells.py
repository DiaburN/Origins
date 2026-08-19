#!/usr/bin/env python3
import json
import pathlib
import sys

EXPECTED = {
    "Warrior": 21,
    "Wizard": 28,
    "Taoist": 27,
    "Assassin": 19,
    "Archer": 24,
    "Monk": 9,
}
EXPECTED_TOTAL = 128
EXPECTED_EXTENSION = {
    "Warrior": {18:"CounterAttack1",19:"ProtectionField1",20:"EntrapSwordSecret",21:"ImmortalSkin1"},
    "Wizard": {56:"GreateFireBallSecret",57:"Bisul",58:"StormEscape1"},
    "Taoist": {87:"HealingCircle2",88:"Healing2"},
    "Assassin": {108:"FlashDash2",109:"MoonMist2"},
    "Archer": {142:"ElementalBarrier1",143:"DelayedExplosion2",144:"NapalmShot2"},
    "Monk": {161:"JiBenGunFa",162:"LuoHanGunFa",163:"JinGangGunFa",164:"DaMoGunFa",165:"XiangLongGunFa",166:"Taunt",167:"TianLeiZhen",168:"ShiBuYiSha",169:"LuoHanZhen"},
}
EXPECTED_SOURCE_STUBS = {
    ("Wizard", 54, "FastMove", "stub_no_magicinfo_no_server_handler"),
}
APPROVED_EXTENSION_COMMIT = "381e589e3d7ee736cdf0583c8315c0d144ab058f"

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

for class_name, expected in EXPECTED_EXTENSION.items():
    rows = {int(row["id"]): row["name"] for row in classes.get(class_name, []) if row.get("source") == "Crystal-Monk"}
    if rows != expected:
        errors.append(f"Crystal-Monk extension mismatch for {class_name}: {rows}")

source_stubs = {
    (class_name, int(row["id"]), row["name"], row["sourceStatus"])
    for class_name in EXPECTED
    for row in classes.get(class_name, [])
    if row.get("sourceStatus")
}
if source_stubs != EXPECTED_SOURCE_STUBS:
    errors.append(f"source stub set mismatch: {sorted(source_stubs)}")

scope = data.get("scope", {})
if scope.get("requiredPlayableSpellCount") != EXPECTED_TOTAL:
    errors.append("scope.requiredPlayableSpellCount must be 128")
if scope.get("sourceStubCount") != len(EXPECTED_SOURCE_STUBS):
    errors.append("scope.sourceStubCount must match the verified source-stub set")
if scope.get("includeMonk") is not True:
    errors.append("scope.includeMonk must be true")
if scope.get("includeCrystalMonkSecretSkills") is not True:
    errors.append("scope.includeCrystalMonkSecretSkills must be true")
source = data.get("source", {})
if source.get("extension") != "JevLOMCN/Crystal-Monk":
    errors.append("Crystal-Monk extension source is not pinned")
if source.get("extensionCommit") != APPROVED_EXTENSION_COMMIT:
    errors.append("Crystal-Monk extension commit is not pinned to the approved revision")

if errors:
    print("Crystal playable spell catalogue FAILED")
    for error in errors:
        print(f"- {error}")
    raise SystemExit(1)

print("Crystal playable spell catalogue OK")
for name, expected_count in EXPECTED.items():
    print(f"- {name}: {expected_count}")
print(f"- total: {EXPECTED_TOTAL}")
print("- source stubs: Wizard.FastMove only (upstream enum identity; no MagicInfo/server handler)")
