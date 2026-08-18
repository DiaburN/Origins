#!/usr/bin/env python3
"""Promote stable viewer identity/state into a generated Zircon UI manifest."""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path


def kebab(name: str) -> str:
    return re.sub(r"(?<!^)(?=[A-Z])", "-", name).lower()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--registry", type=Path, required=True)
    args = parser.parse_args()

    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    registry_text = args.registry.read_text(encoding="utf-8")
    rows = re.findall(r"\['([^']+)','([^']+)','([^']+)','([^']+)',(true|false)\]", registry_text)
    registry = {
        field: {
            "id": window_id,
            "field": field,
            "sourceClass": source_class,
            "category": category,
            "defaultVisible": visible == "true",
        }
        for window_id, field, source_class, category, visible in rows
    }
    if len(registry) != 65:
        raise SystemExit(f"GameScene registry parse incomplete: {len(registry)}")

    assigned = 0
    visibility_corrected = 0
    for item in spec.get("windows", []):
        canonical = registry.get(item.get("field"))
        if not canonical:
            raise SystemExit(f"No stable viewer registry row for GameScene field {item.get('field')}")
        item["id"] = canonical["id"]
        item["category"] = canonical["category"]
        if item.get("defaultVisible") != canonical["defaultVisible"]:
            visibility_corrected += 1
        item["defaultVisible"] = canonical["defaultVisible"]
        assigned += 1

    nested_assigned = 0
    for item in spec.get("nestedWindows", []):
        source_class = item.get("sourceClass") or item.get("class") or item.get("field")
        if not source_class:
            raise SystemExit(f"Nested window without source identity: {item}")
        item["id"] = item.get("id") or f"nested-{kebab(str(source_class))}"
        nested_assigned += 1

    all_items = [*(spec.get("windows") or []), *(spec.get("nestedWindows") or [])]
    all_ids = [item.get("id") for item in all_items]
    if not all(all_ids):
        raise SystemExit("A final source window is missing its stable runtime id")
    if len(all_ids) != len(set(all_ids)):
        duplicates = sorted({value for value in all_ids if all_ids.count(value) > 1})
        raise SystemExit(f"Duplicate viewer IDs after promotion: {duplicates}")
    if assigned != 65 or nested_assigned != 15:
        raise SystemExit(f"Unexpected identity coverage: GameScene={assigned}, nested={nested_assigned}")

    visible_ids = {item["id"] for item in spec.get("windows", []) if item.get("defaultVisible")}
    expected_visible = {"main-panel", "belt", "minimap", "group-health", "buffs", "timer"}
    if visible_ids != expected_visible:
        raise SystemExit(f"GameScene startup visibility drifted: {sorted(visible_ids)}")

    spec["runtimeIdentityPass"] = {
        "gameSceneIdsAssigned": assigned,
        "nestedIdsAssigned": nested_assigned,
        "allIdsUnique": True,
        "startupVisibilityCorrections": visibility_corrected,
        "startupVisibleIds": sorted(visible_ids),
        "source": "apps/zircon-ui-reference/game-scene-windows.js + nested sourceClass",
    }
    args.spec.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(
        f"Stable runtime identity promoted: {assigned} GameScene + {nested_assigned} nested; "
        f"startup visibility corrected on {visibility_corrected} windows"
    )

    here = Path(__file__).resolve().parent
    zircon_root = here.parents[1] / ".source" / "Zircon"
    for helper in (
        "augment_constructor_final_states.py",
        "augment_group_health_reference.py",
        "augment_buff_reference.py",
        "augment_magic_bar_reference.py",
        "augment_auto_potion_reference.py",
        "augment_overflow_contracts.py",
        "augment_companion_reference.py",
    ):
        subprocess.run([sys.executable, str(here / helper), "--spec", str(args.spec)], check=True)
    for helper in ("augment_combo_options.py", "augment_combo_enum_values.py", "augment_config_defaults.py"):
        subprocess.run([
            sys.executable,
            str(here / helper),
            "--spec", str(args.spec),
            "--zircon-root", str(zircon_root),
        ], check=True)
    subprocess.run([
        sys.executable,
        str(here / "audit_complex_action_contracts.py"),
        "--spec", str(args.spec),
        "--zircon-root", str(zircon_root),
    ], check=True)
    subprocess.run([
        sys.executable,
        str(here / "audit_custom_draw_contracts.py"),
        "--spec", str(args.spec),
        "--zircon-root", str(zircon_root),
        "--strict",
    ], check=True)
    subprocess.run(
        [sys.executable, str(here / "sanitize_final_viewer.py"), "--app-layout", str(args.spec.parent / "app-layout.js")],
        check=True,
    )


if __name__ == "__main__":
    main()
