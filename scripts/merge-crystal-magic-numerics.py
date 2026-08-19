#!/usr/bin/env python3
"""Merge base Crystal and Crystal-Monk numeric projections for runtime activation.

The base Jev projection already uses status=projected_by_name. Crystal-Monk
extension rows are projected directly from the pinned source and therefore use
status=projected_from_pinned_source. For the runtime-ready overlay both are
verified name projections, so this generated merged view normalizes the status
while retaining the original status for auditability.
"""
from __future__ import annotations

import argparse
import copy
import json
import pathlib
import re


def norm(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (value or "").lower())


def load(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("base_projection", type=pathlib.Path)
    parser.add_argument("extension_projection", type=pathlib.Path)
    parser.add_argument("output", type=pathlib.Path)
    args = parser.parse_args()

    base = load(args.base_projection)
    extension = load(args.extension_projection)
    merged: list[dict] = []
    seen: dict[str, str] = {}

    for source_name, payload in (("Crystal/Jev", base), ("Crystal-Monk pinned source", extension)):
        for original in payload.get("projections", []):
            row = copy.deepcopy(original)
            name = row.get("crystalName")
            key = norm(name or "")
            if not key:
                raise RuntimeError(f"Projection without crystalName in {source_name}")
            if key in seen:
                raise RuntimeError(f"Duplicate numeric projection for {name}: {seen[key]} and {source_name}")

            status = row.get("status")
            if status not in {"projected_by_name", "projected_from_pinned_source"}:
                raise RuntimeError(f"Unverified numeric projection for {name}: {status}")

            row["sourceProjectionStatus"] = status
            row["status"] = "projected_by_name"
            row["numericSource"] = source_name
            seen[key] = source_name
            merged.append(row)

    payload = {
        "schemaVersion": 1,
        "baseProjection": str(args.base_projection),
        "extensionProjection": str(args.extension_projection),
        "projectionCount": len(merged),
        "projections": merged,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Merged verified magic numeric projections: {len(merged)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
