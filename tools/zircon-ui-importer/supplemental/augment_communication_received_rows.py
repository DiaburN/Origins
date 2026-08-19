#!/usr/bin/env python3
"""Expand CommunicationDialog's fixed five received-mail row composites."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


PREFIX = "deterministic-communication-mail:"


def make(name: str, type_name: str, properties: dict[str, str], *, source_type: str | None = None,
         resolved_text: str | None = None) -> dict:
    item = {
        "name": name,
        "type": type_name,
        "properties": dict(properties),
        "sourceGenerated": PREFIX + "CommunicationDialog ReceivedRows/CommunicationReceivedRow",
        "runtimePayloadInvented": False,
    }
    if source_type:
        item["sourceType"] = source_type
    if resolved_text is not None:
        item["resolvedText"] = resolved_text
    return item


def assert_source(root: Path) -> None:
    text = (root / "Client/Scenes/Views/CommunicationDialog.cs").read_text(encoding="utf-8-sig")
    needles = (
        "ReceivedRows = new CommunicationReceivedRow[5];",
        "for (int i = 0; i < 5; i++)",
        "ReceivedRows[index] = new CommunicationReceivedRow",
        "Location = new Point(18, 43 + (49 * i))",
        "Visible = false",
        "public sealed class CommunicationReceivedRow : DXControl",
        "Size = new Size(236, 49);",
        "DrawTexture = true;",
        "Icon = new DXImageControl",
        "Index = 3680",
        "Location = new Point(6, 7)",
        "SubjectLabel = new DXLabel",
        "Size = new Size(135, 20)",
        "Location = new Point(47, 5)",
        "SenderLabel = new DXLabel",
        "Size = new Size(135, 15)",
        "Location = new Point(47, 25)",
        "DateLabel = new DXLabel",
        "Size = new Size(50, 50)",
        "Location = new Point(185, 0)",
    )
    for needle in needles:
        if needle not in text:
            raise SystemExit(f"Communication received-row source changed: missing {needle!r}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--zircon-root", type=Path, required=True)
    args = parser.parse_args()

    assert_source(args.zircon_root)
    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    window = next((w for w in spec.get("windows", []) if w.get("field") == "CommunicationBox"), None)
    if window is None:
        raise SystemExit("CommunicationBox missing")
    controls = [
        control for control in window.get("controls", [])
        if not str(control.get("sourceGenerated") or "").startswith(PREFIX)
    ]
    generated: list[dict] = []
    for i in range(5):
        row = f"CommunicationReceivedRowSource{i + 1:02d}"
        generated.append(make(row, "DXControl", {
            "Parent": "ReceivedTab",
            "Location": f"new Point(18, {43 + 49 * i})",
            "Size": "new Size(236, 49)",
            "Visible": "false",
            "DrawTexture": "true",
            "BackColour": "Color.Empty",
            "RuntimeMail": "ClientMailInfo; null in neutral reference",
        }, source_type="CommunicationReceivedRow"))
        generated.append(make(f"{row}Icon", "DXImageControl", {
            "Parent": row,
            "LibraryFile": "LibraryFile.GameInter",
            "Index": "3680",
            "IsControl": "false",
            "Location": "new Point(6, 7)",
            "RuntimeOpenedState": "ClientMailInfo.Opened; absent",
        }))
        generated.append(make(f"{row}SubjectLabel", "DXLabel", {
            "Parent": row,
            "AutoSize": "false",
            "Size": "new Size(135, 20)",
            "Location": "new Point(47, 5)",
            "ForeColour": "Color.White",
            "DrawFormat": "TextFormatFlags.VerticalCenter | TextFormatFlags.Left",
            "IsControl": "false",
            "Text": '""',
        }, resolved_text=""))
        generated.append(make(f"{row}SenderLabel", "DXLabel", {
            "Parent": row,
            "AutoSize": "false",
            "Size": "new Size(135, 15)",
            "Location": "new Point(47, 25)",
            "ForeColour": "Color.White",
            "DrawFormat": "TextFormatFlags.VerticalCenter | TextFormatFlags.Left",
            "IsControl": "false",
            "Text": '""',
        }, resolved_text=""))
        generated.append(make(f"{row}DateLabel", "DXLabel", {
            "Parent": row,
            "AutoSize": "false",
            "Size": "new Size(50, 50)",
            "Location": "new Point(185, 0)",
            "Border": "true",
            "ForeColour": "Color.White",
            "DrawFormat": "TextFormatFlags.VerticalCenter | TextFormatFlags.HorizontalCenter | TextFormatFlags.WordBreak",
            "IsControl": "false",
            "Text": '""',
        }, resolved_text=""))

    if len(generated) != 25:
        raise SystemExit(f"Communication deterministic row count internal error: {len(generated)}")
    window["controls"] = generated + controls
    window["deterministicCommunicationReceivedRows"] = {
        "passed": True,
        "rows": 5,
        "controlsAdded": 25,
        "rowSize": [236, 49],
        "rowStep": 49,
        "neutralVisible": False,
        "runtimeMailInvented": False,
        "runtimeSenderInvented": False,
        "runtimeSubjectInvented": False,
        "runtimeDateInvented": False,
    }
    args.spec.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("Communication received rows expanded: 5 neutral rows / 25 controls")


if __name__ == "__main__":
    main()
