#!/usr/bin/env python3
import json
import pathlib
import sys

EXPECTED_ACTIVE = {
    "Warrior": 21,
    "Wizard": 28,
    "Taoist": 27,
    "Assassin": 19,
    "Archer": 24,
}
EXPECTED_ACTIVE_TOTAL = 119
EXPECTED_DEFERRED_MONK_COUNT = 9
EXPECTED_SOURCE_TOTAL = 128
EXPECTED_ACTIVE_EXTENSION = {
    "Warrior": {18:"CounterAttack1",19:"ProtectionField1",20:"EntrapSwordSecret",21:"ImmortalSkin1"},
    "Wizard": {56:"GreateFireBallSecret",57:"Bisul",58:"StormEscape1"},
    "Taoist": {87:"HealingCircle2",88:"Healing2"},
    "Assassin": {108:"FlashDash2",109:"MoonMist2"},
    "Archer": {142:"ElementalBarrier1",143:"DelayedExplosion2",144:"NapalmShot2"},
}
EXPECTED_DEFERRED_MONK = {
    161:"JiBenGunFa",162:"LuoHanGunFa",163:"JinGangGunFa",164:"DaMoGunFa",165:"XiangLongGunFa",
    166:"Taunt",167:"TianLeiZhen",168:"ShiBuYiSha",169:"LuoHanZhen",
}
EXPECTED_SOURCE_STUBS = {
    ("Wizard", 54, "FastMove", "stub_no_magicinfo_no_server_handler"),
}
APPROVED_EXTENSION_COMMIT = "381e589e3d7ee736cdf0583c8315c0d144ab058f"

path = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "database/magic/crystal-playable-spells.json")
data = json.loads(path.read_text(encoding="utf-8"))
classes = data.get("classes", {})
errors = []

unexpected_active_classes = sorted(set(classes) - set(EXPECTED_ACTIVE))
if unexpected_active_classes:
    errors.append(f"unexpected active classes: {unexpected_active_classes}")

for name, expected_count in EXPECTED_ACTIVE.items():
    rows = classes.get(name)
    if rows is None:
        errors.append(f"missing active class {name}")
        continue
    if len(rows) != expected_count:
        errors.append(f"{name}: expected {expected_count}, found {len(rows)}")

all_active_rows = [row for name in EXPECTED_ACTIVE for row in classes.get(name, [])]
if len(all_active_rows) != EXPECTED_ACTIVE_TOTAL:
    errors.append(f"active playable total: expected {EXPECTED_ACTIVE_TOTAL}, found {len(all_active_rows)}")

active_ids = [int(row["id"]) for row in all_active_rows]
if len(active_ids) != len(set(active_ids)):
    errors.append("duplicate active playable spell IDs")

active_pairs = {(name, row["name"]) for name in EXPECTED_ACTIVE for row in classes.get(name, [])}
if len(active_pairs) != len(all_active_rows):
    errors.append("duplicate active spell name inside a class")

for class_name, expected in EXPECTED_ACTIVE_EXTENSION.items():
    rows = {
        int(row["id"]): row["name"]
        for row in classes.get(class_name, [])
        if row.get("source") == "Crystal-Monk"
    }
    if rows != expected:
        errors.append(f"Crystal-Monk active extension mismatch for {class_name}: {rows}")

source_stubs = {
    (class_name, int(row["id"]), row["name"], row["sourceStatus"])
    for class_name in EXPECTED_ACTIVE
    for row in classes.get(class_name, [])
    if row.get("sourceStatus")
}
if source_stubs != EXPECTED_SOURCE_STUBS:
    errors.append(f"source stub set mismatch: {sorted(source_stubs)}")

deferred = data.get("deferredClasses", {})
monk = deferred.get("Monk")
if not isinstance(monk, dict):
    errors.append("deferredClasses.Monk must exist")
    monk_rows = []
else:
    monk_rows = monk.get("spells", [])

if len(monk_rows) != EXPECTED_DEFERRED_MONK_COUNT:
    errors.append(
        f"deferred Monk total: expected {EXPECTED_DEFERRED_MONK_COUNT}, found {len(monk_rows)}"
    )

deferred_monk_map = {int(row["id"]): row["name"] for row in monk_rows}
if deferred_monk_map != EXPECTED_DEFERRED_MONK:
    errors.append(f"deferred Monk spell set mismatch: {deferred_monk_map}")

all_source_ids = active_ids + [int(row["id"]) for row in monk_rows]
if len(all_source_ids) != len(set(all_source_ids)):
    errors.append("duplicate spell IDs across active catalogue and deferred Monk")
if len(all_source_ids) != EXPECTED_SOURCE_TOTAL:
    errors.append(f"source catalogue total: expected {EXPECTED_SOURCE_TOTAL}, found {len(all_source_ids)}")

scope = data.get("scope", {})
if scope.get("activePlayableSpellCount") != EXPECTED_ACTIVE_TOTAL:
    errors.append("scope.activePlayableSpellCount must be 119")
if scope.get("deferredMonkSpellCount") != EXPECTED_DEFERRED_MONK_COUNT:
    errors.append("scope.deferredMonkSpellCount must be 9")
if scope.get("sourceCatalogTotalWithDeferredMonk") != EXPECTED_SOURCE_TOTAL:
    errors.append("scope.sourceCatalogTotalWithDeferredMonk must be 128")
if scope.get("sourceStubCount") != len(EXPECTED_SOURCE_STUBS):
    errors.append("scope.sourceStubCount must match the verified source-stub set")
if scope.get("includeMonk") is not False:
    errors.append("scope.includeMonk must be false")
if scope.get("includeCrystalMonkSecretSkillsForActiveClasses") is not True:
    errors.append("scope.includeCrystalMonkSecretSkillsForActiveClasses must be true")

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
for name, expected_count in EXPECTED_ACTIVE.items():
    print(f"- {name}: {expected_count}")
print(f"- active total: {EXPECTED_ACTIVE_TOTAL}")
print(f"- deferred Monk: {EXPECTED_DEFERRED_MONK_COUNT}")
print(f"- source total with deferred Monk: {EXPECTED_SOURCE_TOTAL}")
print("- source stubs: Wizard.FastMove only (upstream enum identity; no MagicInfo/server handler)")
