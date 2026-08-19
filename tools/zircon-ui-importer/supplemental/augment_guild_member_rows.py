#!/usr/bin/env python3
"""Materialise GuildDialog's deterministic 17-member row array.

GuildDialog.CreateMemberTab() always creates one GuildMemberRow header plus
MemberRows = new GuildMemberRow[17]. The rows exist before GuildInfo arrives,
but the 17 data rows begin hidden with MemberInfo == null. Expand the fixed row
and label structure only; never invent guild members, ranks or online state.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


PREFIX = "deterministic-guild-members:"
LABELS = (
    ("NameLabel", 10, "GuildMemberRowNameLabel"),
    ("RankLabel", 110, "GuildMemberRowRankLabel"),
    ("TotalLabel", 210, "GuildMemberRowTotalLabel"),
    ("DailyLabel", 310, "GuildMemberRowDailyLabel"),
    ("OnlineLabel", 400, "GuildMemberRowOnlineLabel"),
)


def make(name: str, type_name: str, properties: dict[str, str], *, source: str,
         source_type: str | None = None, resolved_text: str | None = None) -> dict:
    item = {
        "name": name,
        "type": type_name,
        "properties": dict(properties),
        "sourceGenerated": source,
    }
    if source_type:
        item["sourceType"] = source_type
    if resolved_text is not None:
        item["resolvedText"] = resolved_text
    return item


def language(spec: dict, key: str) -> str:
    return str(((spec.get("language") or {}).get("English") or {}).get(key) or "")


def assert_source(root: Path) -> None:
    path = root / "Client/Scenes/Views/GuildDialog.cs"
    text = path.read_text(encoding="utf-8-sig")
    needles = (
        "MemberRows = new GuildMemberRow[17];",
        "for (int i = 0; i < MemberRows.Length; i++)",
        "MemberRows[i] = new GuildMemberRow",
        "Location = new Point(16, 11 + i * 23 + 23),",
        "Visible = false",
        "public sealed class GuildMemberRow : DXControl",
        "Size = new Size(402, 20);",
        "NameLabel = new DXLabel",
        "Location = new Point(10, 2)",
        "RankLabel = new DXLabel",
        "Location = new Point(110, 2)",
        "TotalLabel = new DXLabel",
        "Location = new Point(210, 2)",
        "DailyLabel = new DXLabel",
        "Location = new Point(310, 2)",
        "OnlineLabel = new DXLabel",
        "Location = new Point(400, 2)",
    )
    for needle in needles:
        if needle not in text:
            raise SystemExit(f"Guild member deterministic-row source changed: missing {needle!r}")


def add_labels(spec: dict, generated: list[dict], row_name: str, *, header: bool) -> None:
    source = PREFIX + "GuildMemberRow constructor/IsHeader"
    for suffix, x, language_key in LABELS:
        text = language(spec, language_key) if header else ""
        props = {
            "Parent": row_name,
            "IsControl": "false",
            "Location": f"new Point({x}, 2)",
            "ForeColour": "Constants.PrimaryColour" if header else "Color.White",
            "Text": f"CEnvir.Language.{language_key}" if header else '""',
            "RuntimeMemberInfo": "none for header" if header else "ClientGuildMemberInfo; null in neutral reference",
        }
        generated.append(make(
            f"{row_name}{suffix}", "DXLabel", props, source=source,
            resolved_text=text,
        ))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--zircon-root", type=Path, required=True)
    args = parser.parse_args()

    assert_source(args.zircon_root)
    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    guild = next((w for w in spec.get("windows", []) if w.get("field") == "GuildBox"), None)
    if guild is None:
        raise SystemExit("GuildBox missing from final manifest")

    controls = []
    removed_base_header = 0
    for control in guild.get("controls", []):
        generated = str(control.get("sourceGenerated") or "")
        props = control.get("properties") or {}
        if generated.startswith(PREFIX):
            continue
        # augment_ui_composites currently preserves the source header itself as
        # one GuildMemberRow/DXControl but cannot expand its constructor children.
        # Replace that incomplete composite with the complete source row once.
        if (control.get("sourceType") == "GuildMemberRow"
                and control.get("compositeChild")
                and props.get("Parent") == "MemberTab"):
            removed_base_header += 1
            continue
        controls.append(control)

    generated: list[dict] = []
    row_source = PREFIX + "GuildDialog.CreateMemberTab fixed array"

    header = "GuildMemberHeaderSource"
    generated.append(make(header, "DXControl", {
        "Parent": "MemberTab",
        "Location": "new Point(7, 9)",
        "Size": "new Size(402, 20)",
        "DrawTexture": "false",
        "BackColour": "Constants.RowBackColour",
        "Visible": "true",
        "IsHeader": "true",
        "RuntimeMemberInfo": "not applicable; source header",
    }, source=row_source, source_type="GuildMemberRow"))
    add_labels(spec, generated, header, header=True)

    for i in range(17):
        row = f"GuildMemberRowSource{i + 1:02d}"
        generated.append(make(row, "DXControl", {
            "Parent": "MemberTab",
            "Location": f"new Point(16, {34 + i * 23})",
            "Size": "new Size(402, 20)",
            "DrawTexture": "true",
            "BackColour": "Constants.RowBackColour",
            "Visible": "false",
            "RuntimeMemberInfo": "ClientGuildMemberInfo; null in neutral reference",
        }, source=row_source, source_type="GuildMemberRow"))
        add_labels(spec, generated, row, header=False)

    guild["controls"] = generated + controls
    guild["deterministicGuildMemberRows"] = {
        "headerRows": 1,
        "memberRows": 17,
        "rowSize": [402, 20],
        "rowStep": 23,
        "regularRowsVisible": False,
        "memberInfoInvented": False,
        "generatedControls": len(generated),
        "replacedIncompleteCompositeControls": removed_base_header,
        "netControlsAdded": len(generated) - removed_base_header,
        "source": "GuildDialog.CreateMemberTab + GuildMemberRow constructor",
    }
    args.spec.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(
        "Guild deterministic member rows expanded: "
        f"1 header + 17 rows -> {len(generated)} controls; "
        f"replaced base composite={removed_base_header}; net={len(generated) - removed_base_header}"
    )


if __name__ == "__main__":
    main()
