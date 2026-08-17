#!/usr/bin/env python3
"""Promote stable viewer identity/state into a generated Zircon UI manifest.

The static viewer registry is an explicit transcription of GameScene construction
and is also the browser's canonical id/category/default-visible mapping. The
base source parser historically inferred visibility by looking past each
initializer, which can accidentally capture the next window's Visible=false.
Promoting the canonical registry values here keeps the final artifact internally
consistent while the deeper parser remains focused on C# geometry/properties.
"""
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
    rows = re.findall(
        r"\['([^']+)','([^']+)','([^']+)','([^']+)',(true|false)\]",
        registry_text,
    )
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

    sanitizer = Path(__file__).with_name("sanitize_final_viewer.py")
    app_layout = args.spec.parent / "app-layout.js"
    subprocess.run(
        [sys.executable, str(sanitizer), "--app-layout", str(app_layout)],
        check=True,
    )


if __name__ == "__main__":
    main()
