#!/usr/bin/env python3
"""QA for ORIGINS MOBILE Crystal magic catalog."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data" / "magic" / "crystal_magic_manifest.json"

EXPECTED_COUNTS = {
    "Warrior": 17,
    "Wizard": 25,
    "Taoist": 25,
    "Assassin": 17,
    "Archer": 21,
    "Monk": 9,
}

EXPECTED_FLAGS = {
    "Warrior": 1,
    "Wizard": 2,
    "Taoist": 4,
    "Assassin": 8,
    "Archer": 16,
    "Monk": 32,
}

RUNTIME_FIELDS = {
    "currentMagicLevel",
    "currentExperience",
    "keybind",
    "cooldown",
    "playerUnlockState",
}


def fail(message: str) -> None:
    raise SystemExit(f"[FAIL] {message}")


def main() -> None:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    classes = data.get("classes", {})

    if set(classes) != set(EXPECTED_COUNTS):
        fail(f"Expected classes {sorted(EXPECTED_COUNTS)}, found {sorted(classes)}")

    all_records = []
    for class_name, expected_count in EXPECTED_COUNTS.items():
        class_data = classes[class_name]
        if class_data.get("requiredClassFlag") != EXPECTED_FLAGS[class_name]:
            fail(f"Bad RequiredClass flag for {class_name}")

        spells = class_data.get("spells", [])
        if len(spells) != expected_count:
            fail(f"{class_name}: expected {expected_count}, found {len(spells)}")

        for record in spells:
            if len(record) != 4:
                fail(f"{class_name}: invalid record {record}")
            spell, spell_id, icon_id, required_levels = record
            if len(required_levels) != 3:
                fail(f"{spell}: requiredLevels must contain 3 values")
            all_records.append((class_name, spell, spell_id, icon_id, required_levels))

    if len(all_records) != 114:
        fail(f"Expected 114 spells, found {len(all_records)}")

    names = [(c, s) for c, s, *_ in all_records]
    if len(names) != len(set(names)):
        fail("Duplicate class/spell name detected")

    ids = [spell_id for _, _, spell_id, _, _ in all_records]
    if len(ids) != len(set(ids)):
        fail("Duplicate spellId detected")

    unresolved = [spell for _, spell, _, icon_id, _ in all_records if icon_id is None]
    if unresolved != ["FastMove"]:
        fail(f"Unexpected unresolved icons: {unresolved}")

    fast_move = next(row for row in all_records if row[1] == "FastMove")
    if fast_move[4] != [None, None, None]:
        fail("FastMove source gap must stay null; do not invent levels")

    serialized = MANIFEST.read_text(encoding="utf-8")
    for runtime_field in RUNTIME_FIELDS:
        if f'"{runtime_field}":' in serialized:
            fail(f"Fake runtime field stored in catalog: {runtime_field}")

    counts = Counter(row[0] for row in all_records)
    print("[OK] 6 classes")
    print("[OK] 114 spells")
    print("[OK] class counts:", dict(counts))
    print("[OK] spell IDs unique")
    print("[OK] no fake runtime values")
    print("[KNOWN SOURCE GAP] FastMove icon/static MagicInfo values unresolved")


if __name__ == "__main__":
    main()
