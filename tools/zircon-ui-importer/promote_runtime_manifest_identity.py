#!/usr/bin/env python3
"""Promote stable viewer IDs into a generated Zircon UI source manifest."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def kebab(name: str) -> str:
    return re.sub(r"(?<!^)(?=[A-Z])", "-", name).lower()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--registry", type=Path, required=True)
    args = parser.parse_args()

    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    registry = args.registry.read_text(encoding="utf-8")
    pairs = re.findall(r"\['([^']+)','([^']+)'\s*,", registry)
    id_by_field = {field: window_id for window_id, field in pairs}
    if len(id_by_field) < 65:
        raise SystemExit(f"GameScene registry ID parse incomplete: {len(id_by_field)}")

    assigned = 0
    for item in spec.get("windows", []):
        window_id = id_by_field.get(item.get("field"))
        if not window_id:
            raise SystemExit(f"No stable viewer ID for GameScene field {item.get('field')}")
        item["id"] = window_id
        assigned += 1

    nested_assigned = 0
    for item in spec.get("nestedWindows", []):
        source_class = item.get("sourceClass") or item.get("class") or item.get("field")
        if not source_class:
            raise SystemExit(f"Nested window without source identity: {item}")
        item["id"] = item.get("id") or f"nested-{kebab(str(source_class))}"
        nested_assigned += 1

    all_ids = [item.get("id") for item in [*(spec.get("windows") or []), *(spec.get("nestedWindows") or [])]]
    if len(all_ids) != len(set(all_ids)):
        duplicates = sorted({value for value in all_ids if all_ids.count(value) > 1})
        raise SystemExit(f"Duplicate viewer IDs after promotion: {duplicates}")
    if assigned != 65 or nested_assigned != 15:
        raise SystemExit(f"Unexpected identity coverage: GameScene={assigned}, nested={nested_assigned}")

    spec["runtimeIdentityPass"] = {
        "gameSceneIdsAssigned": assigned,
        "nestedIdsAssigned": nested_assigned,
        "allIdsUnique": True,
        "source": "apps/zircon-ui-reference/game-scene-windows.js + nested sourceClass",
    }
    args.spec.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Stable runtime IDs promoted: {assigned} GameScene + {nested_assigned} nested")


if __name__ == "__main__":
    main()
