#!/usr/bin/env python3
"""Compatibility source gate for the superseded Consignment composite pass.

The original supplemental implementation materialised Consignment UI assuming
ItemType ended at Reel (34 enum members including Nothing). Current Zircon has
additional deterministic ItemType values through SocketGem. The complete UI is
now emitted by augment_consignment_deterministic_composites.py, which also
recovers the constructor's CreateHeaderLabel controls.

This compatibility pass deliberately emits no controls so the modern pass has a
single identity owner. It still gates the upstream source shape and current enum
extent; removing it would weaken regression coverage.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from augment_combo_options import parse_enum


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--zircon-root", type=Path, required=True)
    args = parser.parse_args()

    # Ensure the manifest is readable without changing it in this legacy pass.
    json.loads(args.spec.read_text(encoding="utf-8"))

    source = (args.zircon_root / "Client/Scenes/Views/ConsignmentDialog.cs").read_text(encoding="utf-8-sig")
    needles = (
        "public const int VisibleRowCount = 6;",
        "ItemTypeMenu = new ConsignmentItemTypeMenu",
        "SearchRows = new ConsignmentSearchRow[VisibleRowCount];",
        "ConsignRows = new ConsignmentListRow[VisibleRowCount];",
        "foreach (ItemType itemType in Enum.GetValues(enumType))",
        "if (itemType == ItemType.Nothing) continue;",
        "button.Index = selected ? 830 : 831;",
        "public sealed class ConsignmentSearchRow : DXControl",
        "public sealed class ConsignmentListRow : DXControl",
        "SortLabel = CreateHeaderLabel(",
        "ConsignDateLabel = CreateHeaderLabel(",
    )
    for needle in needles:
        if needle not in source:
            raise SystemExit(f"Legacy Consignment compatibility source changed: missing {needle!r}")

    members = parse_enum(args.zircon_root, "ItemType")
    if len(members) != 38 or members[0].get("name") != "Nothing" or members[-1].get("name") != "SocketGem":
        raise SystemExit(
            "Current ItemType source contract changed: "
            f"count={len(members)} first={members[:1]} last={members[-1:]}"
        )

    print(
        "Legacy Consignment compatibility gate: PASS -> current ItemType has 38 members; "
        "modern deterministic pass owns emitted controls"
    )


if __name__ == "__main__":
    main()
