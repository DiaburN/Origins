#!/usr/bin/env python3
"""Materialise GroupDialog's five deterministic LFG row composites."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


PREFIX = "deterministic-group-lfg:"


def make(name: str, type_name: str, properties: dict[str, str], *, source_type: str | None = None) -> dict:
    item = {
        "name": name,
        "type": type_name,
        "properties": dict(properties),
        "sourceGenerated": PREFIX + "GroupDialog LFGRows/GroupLFGRow",
        "runtimePayloadInvented": False,
    }
    if source_type:
        item["sourceType"] = source_type
    if type_name == "DXLabel":
        item["resolvedText"] = ""
    return item


def assert_source(root: Path) -> None:
    text = (root / "Client/Scenes/Views/GroupDialog.cs").read_text(encoding="utf-8-sig")
    needles = (
        "LFGRows = new GroupLFGRow[5];",
        "Location = new Point(13, 293 + (i * 21))",
        "Size = new Size(194, 19)",
        "Visible = false",
        "UpdateList(new List<ClientLookingForGroup>());",
        "public sealed class GroupLFGRow : DXControl",
        "NameLabel = new DXLabel",
        "Location = new Point(0, 0)",
        "Size = new Size(100, 20)",
        "StatusLabel = new DXLabel",
        "Location = new Point(101, 0)",
        "Size = new Size(50, 20)",
        "TypeLabel = new DXLabel",
        "Location = new Point(151, 0)",
        "Size = new Size(42, 20)",
        "if (Info == null)",
        "NameLabel.Text = \"\";",
        "StatusLabel.Text = \"\";",
        "TypeLabel.Text = \"\";",
    )
    for needle in needles:
        if needle not in text:
            raise SystemExit(f"Group LFG row source changed: missing {needle!r}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--zircon-root", type=Path, required=True)
    args = parser.parse_args()

    assert_source(args.zircon_root)
    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    group = next((w for w in spec.get("windows", []) if w.get("field") == "GroupBox"), None)
    if group is None:
        raise SystemExit("GroupBox missing from manifest")
    controls = [
        control for control in group.get("controls", [])
        if not str(control.get("sourceGenerated") or "").startswith(PREFIX)
    ]
    generated: list[dict] = []
    for i in range(5):
        row = f"GroupLFGRowSource{i + 1:02d}"
        generated.append(make(row, "DXControl", {
            "Parent": "this",
            "Location": f"new Point(13, {293 + i * 21})",
            "Size": "new Size(194, 19)",
            "Visible": "false",
            "HintPosition": "HintPosition.Fluid",
            "Selected": "false",
            "RuntimeInfo": "ClientLookingForGroup; null in neutral reference",
        }, source_type="GroupLFGRow"))
        generated.append(make(f"{row}NameLabel", "DXLabel", {
            "Parent": row,
            "Text": '""',
            "ForeColour": "Color.White",
            "Location": "new Point(0, 0)",
            "Size": "new Size(100, 20)",
            "AutoSize": "false",
            "DrawFormat": "TextFormatFlags.VerticalCenter | TextFormatFlags.HorizontalCenter | TextFormatFlags.WordEllipsis",
            "IsControl": "false",
        }))
        generated.append(make(f"{row}StatusLabel", "DXLabel", {
            "Parent": row,
            "Text": '""',
            "ForeColour": "Color.Lime",
            "Location": "new Point(101, 0)",
            "Size": "new Size(50, 20)",
            "AutoSize": "false",
            "DrawFormat": "TextFormatFlags.VerticalCenter | TextFormatFlags.HorizontalCenter",
            "IsControl": "false",
        }))
        generated.append(make(f"{row}TypeLabel", "DXLabel", {
            "Parent": row,
            "Text": '""',
            "ForeColour": "Color.Lime",
            "Location": "new Point(151, 0)",
            "Size": "new Size(42, 20)",
            "AutoSize": "false",
            "DrawFormat": "TextFormatFlags.VerticalCenter | TextFormatFlags.HorizontalCenter",
            "IsControl": "false",
        }))

    if len(generated) != 20:
        raise SystemExit(f"Group LFG deterministic count internal error: {len(generated)}")
    group["controls"] = generated + controls
    group["deterministicGroupLFGRows"] = {
        "passed": True,
        "rows": 5,
        "controlsAdded": 20,
        "rowSize": [194, 19],
        "rowStep": 21,
        "neutralVisible": False,
        "runtimeLfgInvented": False,
        "runtimeGroupNamesInvented": False,
        "runtimeCountsInvented": False,
        "runtimeTypesInvented": False,
    }
    args.spec.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("Group LFG rows expanded: 5 neutral rows / 20 controls")


if __name__ == "__main__":
    main()
