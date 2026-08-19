#!/usr/bin/env python3
"""Merge verified Crystal and Crystal-Monk numeric projections for activation.

The base Jev projection can contain legacy DB rows whose normalized names no
longer exist in the pinned Crystal source. Those rows intentionally have no
`crystalName` and status `legacy_unknown_name_not_in_current_source`; they are
audit-only and must never enter the active ORIGINS spell projection.

Named base rows use status=projected_by_name. Crystal-Monk extension rows are
projected directly from the pinned fork and use
status=projected_from_pinned_source. Both are verified name projections for the
runtime-ready overlay, so this generated merged view normalizes their status
while retaining the original status and any skipped legacy rows for auditability.
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
    skipped_legacy_unknown: list[dict] = []
    seen: dict[str, str] = {}

    for source_name, payload in (("Crystal/Jev", base), ("Crystal-Monk pinned source", extension)):
        for original in payload.get("projections", []):
            row = copy.deepcopy(original)
            name = row.get("crystalName")
            status = row.get("status")
            key = norm(name or "")

            if not key:
                if source_name == "Crystal/Jev" and status == "legacy_unknown_name_not_in_current_source":
                    skipped_legacy_unknown.append(row)
                    continue
                raise RuntimeError(
                    f"Unnamed projection is not an approved legacy-unknown row in {source_name}: {row}"
                )

            if key in seen:
                raise RuntimeError(f"Duplicate numeric projection for {name}: {seen[key]} and {source_name}")

            if status not in {"projected_by_name", "projected_from_pinned_source"}:
                raise RuntimeError(f"Unverified numeric projection for {name}: {status}")

            row["sourceProjectionStatus"] = status
            row["status"] = "projected_by_name"
            row["numericSource"] = source_name
            seen[key] = source_name
            merged.append(row)

    expected_unknown = int(base.get("counts", {}).get("legacyUnknownNames", 0))
    if len(skipped_legacy_unknown) != expected_unknown:
        raise RuntimeError(
            f"Legacy-unknown audit count mismatch: base reports {expected_unknown}, "
            f"merge skipped {len(skipped_legacy_unknown)}"
        )

    payload = {
        "schemaVersion": 2,
        "baseProjection": str(args.base_projection),
        "extensionProjection": str(args.extension_projection),
        "projectionCount": len(merged),
        "skippedLegacyUnknownCount": len(skipped_legacy_unknown),
        "skippedLegacyUnknown": skipped_legacy_unknown,
        "policy": {
            "joinKey": "normalized spell name",
            "legacyUnknownRowsEnterActiveOverlay": False,
        },
        "projections": merged,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(
        f"Merged verified magic numeric projections: {len(merged)}; "
        f"skipped legacy unknown rows: {len(skipped_legacy_unknown)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
