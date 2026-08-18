#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def sql(value):
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    if isinstance(value, (int, float)):
        return str(value)
    return "'" + str(value).replace("'", "''") + "'"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--catalog", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()

    catalog = json.loads(args.catalog.read_text(encoding="utf-8"))
    rows = []
    for class_name, class_data in catalog["classes"].items():
        class_id = int(class_data["classId"])
        for spell in class_data["spells"]:
            source = spell["source"]
            source_system = "Crystal-Monk" if source["repo"] == "JevLOMCN/Crystal-Monk" else "Crystal"
            game_key = f"{class_name.lower()}.{spell['spell'].lower()}"
            required = spell.get("requiredLevels") or [None, None, None]
            needs = spell.get("experienceNeeds") or [None, None, None]
            metadata = {
                "requiredClassFlag": class_data["requiredClassFlag"],
                "sourceSeedName": spell.get("sourceSeedName"),
                "sourceInitializerSpell": spell.get("sourceInitializerSpell"),
                "sourceInitializerMatches": spell.get("sourceInitializerMatches"),
            }
            values = [
                game_key,
                spell["spell"],
                class_id,
                source_system,
                spell.get("spellId"),
                spell["spell"],
                "MagIcon2.Lib" if spell.get("iconId") is not None else None,
                spell.get("iconId"),
                spell.get("iconFrameNormal"),
                spell.get("iconFramePressed"),
                spell.get("minBasePower"),
                spell.get("maxBasePower"),
                spell.get("minLevelPower"),
                spell.get("maxLevelPower"),
                spell.get("baseCost"),
                spell.get("levelCost"),
                required[0], required[1], required[2],
                needs[0], needs[1], needs[2],
                spell.get("delayBase"),
                spell.get("delayReduction"),
                spell.get("range"),
                bool(spell.get("sourceImplemented")),
                spell.get("sourceIssue"),
                source["repo"],
                source["path"],
                source.get("commit"),
                json.dumps(metadata, ensure_ascii=False, separators=(",", ":")),
            ]
            rows.append("(" + ", ".join(sql(value) for value in values) + ")")

    if len(rows) != 114:
        raise SystemExit(f"expected 114 magic rows, got {len(rows)}")

    columns = [
        "game_key","name","class_id","source_system","source_spell_id","magic_type",
        "icon_library","icon_index","icon_frame_normal","icon_frame_pressed",
        "min_base_power","max_base_power","min_level_power","max_level_power",
        "base_cost","level_cost","need_level_1","need_level_2","need_level_3",
        "experience_1","experience_2","experience_3","delay_base_ms","delay_reduction_ms",
        "range_cells","source_implemented","source_issue","source_repo","source_path","source_commit","metadata"
    ]

    body = "BEGIN;\n\nINSERT INTO content.magic_definitions (\n    " + ",\n    ".join(columns) + "\n) VALUES\n    "
    body += ",\n    ".join(rows)
    body += "\nON CONFLICT (game_key) DO UPDATE SET\n"
    body += ",\n".join(f"    {column} = EXCLUDED.{column}" for column in columns if column != "game_key")
    body += ";\n\nCOMMIT;\n"

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(body, encoding="utf-8")
    print(f"Wrote {args.out}: {len(rows)} magic rows")


if __name__ == "__main__":
    main()
