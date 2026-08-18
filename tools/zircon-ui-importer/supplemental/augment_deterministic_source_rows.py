#!/usr/bin/env python3
"""Expand deterministic row/composite arrays created by Zircon source.

These controls exist even before server/player data arrives but are hidden or
empty in the neutral reference.  We materialise only their source chrome and
geometry; RankInfo, InstanceInfo, ItemInfo, map/NPC/monster data remain absent.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def make(name: str, type_name: str, properties: dict[str, str], *, parent: str | None = None,
         resolved_text: str | None = None, source: str) -> dict:
    props = dict(properties)
    if parent is not None:
        props["Parent"] = parent
    item = {"name": name, "type": type_name, "properties": props, "sourceGenerated": source}
    if resolved_text is not None:
        item["resolvedText"] = resolved_text
    return item


def window(spec: dict, field: str) -> dict:
    result = next((item for item in spec.get("windows", []) if item.get("field") == field), None)
    if result is None:
        raise SystemExit(f"{field} missing from generated manifest")
    return result


def remove_generated(controls: list[dict], prefix: str) -> list[dict]:
    return [item for item in controls if not str(item.get("sourceGenerated", "")).startswith(prefix)]


def english(spec: dict, key: str, fallback: str = "") -> str:
    return str(((spec.get("language") or {}).get("English") or {}).get(key) or fallback)


def assert_source(root: Path) -> None:
    checks = {
        "Client/Scenes/Views/RankingDialog.cs": [
            "Lines = new RankingLine[11];",
            "SearchLine = new RankingLine",
            "Location = new Point(12, 16 + (23 * i))",
            "Size = new Size(288, 22);",
            "OnlineImage = new DXImageControl",
        ],
        "Client/Scenes/Views/DungeonFinderDialog.cs": [
            "DungeonRows = new DungeonRow[9];",
            "Location = new Point(10, 46 + i * 43)",
            "Size = new Size(515, 40);",
            "FavouriteImage = new DXButton",
        ],
        "Client/Scenes/Views/FortuneCheckerDialog.cs": [
            "SearchRows = new FortuneCheckerRow[9];",
            "i * 58",
            "Size = new Size(465, 55);",
            "Visible = false;",
            "CheckButton = new DXButton",
        ],
        "Client/Scenes/Views/BigMapDialog.cs": [
            "private const int MaximumVisibleRows = 24;",
            "BigMapListRow[] rows = new BigMapListRow[MaximumVisibleRows];",
            "Visible = false,",
            "NameLabel = new DXLabel",
            "NPCRows = CreateRows(NPCTab);",
            "MonsterRows = CreateRows(MonsterTab);",
        ],
    }
    for relative, needles in checks.items():
        text = (root / relative).read_text(encoding="utf-8-sig")
        for needle in needles:
            if needle not in text:
                raise SystemExit(f"Deterministic row source changed: {relative}: missing {needle!r}")


def ranking_rows(spec: dict) -> int:
    w = window(spec, "RankingBox")
    controls = remove_generated(w.get("controls", []), "deterministic-rows:Ranking")
    generated: list[dict] = []
    source = "deterministic-rows:RankingDialog RankingLine constructor"

    def add_row(name: str, parent: str, location: str, visible: bool) -> None:
        generated.append(make(name, "DXControl", {
            "Location": location, "Size": "new Size(288, 22)", "DrawTexture": "false",
            "CacheInParent": "false", "BackColour": "Color.Empty", "Visible": str(visible).lower(),
            "RuntimeRank": "RankInfo; null in neutral reference",
        }, parent=parent, source=source))
        generated.append(make(f"{name}OnlineImage", "DXImageControl", {
            "LibraryFile": "LibraryFile.GameInter", "Index": "3624", "Location": "new Point(2, 6)",
            "IsControl": "false", "Visible": "false", "RuntimeOnline": "RankInfo.Online",
        }, parent=name, source=source))
        generated.append(make(f"{name}RankLabel", "DXLabel", {
            "AutoSize": "false", "Location": "new Point(10, 0)", "Size": "new Size(31, 22)",
            "ForeColour": "Color.White", "DrawFormat": "TextFormatFlags.HorizontalCenter | TextFormatFlags.VerticalCenter",
            "IsControl": "false", "Text": '""',
        }, parent=name, resolved_text="", source=source))
        generated.append(make(f"{name}LevelLabel", "DXLabel", {
            "AutoSize": "false", "Location": "new Point(40, 0)", "Size": "new Size(43, 22)",
            "ForeColour": "Color.White", "DrawFormat": "TextFormatFlags.HorizontalCenter | TextFormatFlags.VerticalCenter",
            "IsControl": "false", "Text": '""',
        }, parent=name, resolved_text="", source=source))
        generated.append(make(f"{name}NameLabel", "DXLabel", {
            "AutoSize": "false", "Location": "new Point(82, 0)", "Size": "new Size(168, 22)",
            "ForeColour": "Color.White", "DrawFormat": "TextFormatFlags.HorizontalCenter | TextFormatFlags.VerticalCenter",
            "IsControl": "false", "Text": '""',
        }, parent=name, resolved_text="", source=source))
        generated.append(make(f"{name}ChangeLabel", "DXLabel", {
            "AutoSize": "false", "Location": "new Point(249, 0)", "Size": "new Size(40, 22)",
            "ForeColour": "Color.White", "DrawFormat": "TextFormatFlags.HorizontalCenter | TextFormatFlags.VerticalCenter",
            "IsControl": "false", "Text": '""',
        }, parent=name, resolved_text="", source=source))

    # SearchLine is source-created and initially visible but contains no RankInfo.
    add_row("RankingSearchLineSource", "RankPanel", "new Point(12, 90)", True)
    for i in range(11):
        add_row(f"RankingLineSource{i + 1:02d}", "RankPanelList", f"new Point(12, {16 + 23 * i})", False)

    w["controls"] = generated + controls
    w["deterministicRankingRows"] = {
        "searchRows": 1, "rankingRows": 11, "rowSize": [288, 22], "rowStep": 23,
        "regularRowsVisible": False, "runtimeRankInfoInvented": False,
    }
    return len(generated)


def dungeon_rows(spec: dict) -> int:
    w = window(spec, "DungeonFinderBox")
    controls = remove_generated(w.get("controls", []), "deterministic-rows:Dungeon")
    generated: list[dict] = []
    source = "deterministic-rows:DungeonFinderDialog DungeonRow constructor"
    for i in range(9):
        row = f"DungeonRowSource{i + 1:02d}"
        generated.append(make(row, "DXControl", {
            "Location": f"new Point(10, {46 + i * 43})", "Size": "new Size(515, 40)",
            "DrawTexture": "true", "BackColour": "Constants.RowBackColour", "Visible": "false",
            "RuntimeInstanceInfo": "InstanceInfo; absent in neutral reference",
            "NeutralVisibilityReason": "OnVisibleChanged -> DungeonSearch -> empty source-runtime InstanceInfo list -> RefreshDungeonList hides row",
        }, parent="DungeonTab", source=source))
        for suffix, x in (("NameLabel", 20), ("TypeLabel", 150), ("LevelLabel", 250), ("CountLabel", 350)):
            generated.append(make(f"{row}{suffix}", "DXLabel", {
                "Location": f"new Point({x}, 12)", "IsControl": "false", "Text": '""',
            }, parent=row, resolved_text="", source=source))
        generated.append(make(f"{row}FavouriteImage", "DXButton", {
            "LibraryFile": "LibraryFile.GameInter", "Index": "6570", "Enabled": "false", "Visible": "false",
            "Hint": '"Favourite (NOT YET ENABLED)"', "Location": "new Point(Size.Width - FavouriteImage.Size.Width - 10, (Size.Height - FavouriteImage.Size.Height) / 2)",
        }, parent=row, source=source))
    w["controls"] = generated + controls
    w["deterministicDungeonRows"] = {
        "rowCount": 9, "rowSize": [515, 40], "rowStep": 43, "neutralVisible": False,
        "scrollVisibleSize": 9, "scrollChange": 3, "runtimeInstanceInfoInvented": False,
    }
    return len(generated)


def fortune_rows(spec: dict) -> int:
    w = window(spec, "FortuneCheckerBox")
    controls = remove_generated(w.get("controls", []), "deterministic-rows:Fortune")
    generated: list[dict] = []
    source = "deterministic-rows:FortuneCheckerDialog FortuneCheckerRow constructor"
    labels = {
        "CountLabelLabel": english(spec, "FortuneCheckerRowCountLabel", "Count"),
        "ProgressLabelLabel": english(spec, "FortuneCheckerRowProgressLabel", "Progress"),
        "DateLabelLabel": english(spec, "FortuneCheckerRowDateLabel", "Date"),
        "CheckButton": english(spec, "FortuneCheckerRowCheckButtonLabel", "Check"),
    }
    for i in range(9):
        row = f"FortuneRowSource{i + 1:02d}"
        generated.append(make(row, "DXControl", {
            "Location": f"new Point(ClientArea.X, ClientArea.Y + filterPanel.Size.Height + 5 + {i} * 58)",
            "Size": "new Size(465, 55)", "DrawTexture": "true", "BackColour": "Constants.RowBackColour",
            "Visible": "false", "RuntimeItemInfo": "ItemInfo; null in neutral reference",
            "RuntimeFortune": "ClientFortuneInfo; null in neutral reference",
        }, parent="this", source=source))
        generated.append(make(f"{row}ItemCell", "DXItemCell", {
            "Location": "new Point(10, 10)", "FixedBorder": "true", "Border": "true", "ReadOnly": "true",
            "Slot": "0", "FixedBorderColour": "true", "RuntimeItem": "ItemInfo -> ClientUserItem; absent",
        }, parent=row, source=source))
        generated.append(make(f"{row}NameLabel", "DXLabel", {
            "Location": "new Point(46, 22)", "IsControl": "false", "Text": '""',
        }, parent=row, resolved_text="", source=source))
        generated.append(make(f"{row}CountLabelLabel", "DXLabel", {
            "Location": "new Point(320 - CountLabelLabel.Size.Width, 5)", "ForeColour": "Color.White",
            "IsControl": "false", "Text": "CEnvir.Language.FortuneCheckerRowCountLabel",
        }, parent=row, resolved_text=labels["CountLabelLabel"], source=source))
        generated.append(make(f"{row}CountLabel", "DXLabel", {
            "Location": "new Point(320, 5)", "IsControl": "false", "Text": '""',
        }, parent=row, resolved_text="", source=source))
        generated.append(make(f"{row}ProgressLabelLabel", "DXLabel", {
            "Location": "new Point(320 - ProgressLabelLabel.Size.Width, 20)", "ForeColour": "Color.White",
            "IsControl": "false", "Text": "CEnvir.Language.FortuneCheckerRowProgressLabel",
        }, parent=row, resolved_text=labels["ProgressLabelLabel"], source=source))
        generated.append(make(f"{row}ProgressLabel", "DXLabel", {
            "Location": "new Point(320, 20)", "IsControl": "false", "Text": '""',
        }, parent=row, resolved_text="", source=source))
        generated.append(make(f"{row}DateLabelLabel", "DXLabel", {
            "Location": "new Point(320 - DateLabelLabel.Size.Width, 35)", "ForeColour": "Color.White",
            "IsControl": "false", "Text": "CEnvir.Language.FortuneCheckerRowDateLabel",
        }, parent=row, resolved_text=labels["DateLabelLabel"], source=source))
        generated.append(make(f"{row}DateLabel", "DXLabel", {
            "Location": "new Point(320, 35)", "IsControl": "false", "Text": '""',
        }, parent=row, resolved_text="", source=source))
        generated.append(make(f"{row}CheckButton", "DXButton", {
            "ButtonType": "ButtonType.SmallButton", "Size": "new Size(50, SmallButtonHeight)",
            "Location": "new Point(Size.Width - 55, 34)", "Label": "CEnvir.Language.FortuneCheckerRowCheckButtonLabel",
            "Enabled": "false", "RuntimeAction": "C.FortuneCheck requires real ItemInfo and confirmation",
        }, parent=row, resolved_text=labels["CheckButton"], source=source))
    w["controls"] = generated + controls
    w["deterministicFortuneRows"] = {
        "rowCount": 9, "rowSize": [465, 55], "rowStep": 58, "neutralVisible": False,
        "scrollVisibleSize": 9, "scrollChange": 3, "runtimeItemInfoInvented": False, "runtimeFortuneInvented": False,
    }
    return len(generated)


def bigmap_rows(spec: dict) -> int:
    w = window(spec, "BigMapBox")
    controls = remove_generated(w.get("controls", []), "deterministic-rows:BigMap")
    generated: list[dict] = []
    source = "deterministic-rows:BigMapDialog CreateRows/CreateScrollBar + BigMapListRow constructor"
    for prefix, parent in (("BigMapNPCRowSource", "NPCTab"), ("BigMapMonsterRowSource", "MonsterTab")):
        for i in range(24):
            row = f"{prefix}{i + 1:02d}"
            generated.append(make(row, "DXControl", {
                "Location": "Point.Empty", "Size": "Size.Empty", "DrawTexture": "true",
                "BackColour": "Constants.RowBackColour", "Visible": "false",
                "RuntimeEntry": "BigMapNPCListEntry/MonsterInfo; absent in neutral reference",
                "RuntimeLayout": "LayoutList after SelectedInfo/map size",
            }, parent=parent, source=source))
            generated.append(make(f"{row}NameLabel", "DXLabel", {
                "Location": "new Point(10, 3)", "IsControl": "false", "Text": '""',
                "ForeColour": "Constants.PrimaryColour",
            }, parent=row, resolved_text="", source=source))

    existing = {item.get("name") for item in controls}
    for name, parent in (("NPCScrollBar", "NPCTab"), ("MonsterScrollBar", "MonsterTab")):
        if name in existing:
            continue
        generated.append(make(name, "DXVScrollBar", {
            "Location": "Point.Empty", "Size": "Size.Empty", "Change": "1", "MinValue": "0",
            "VisibleSize": "1", "HideWhenNoScroll": "true", "BackColour": "Color.Empty", "Border": "false",
            "UpButton.Index": "61", "UpButton.LibraryFile": "LibraryFile.Interface",
            "DownButton.Index": "62", "DownButton.LibraryFile": "LibraryFile.Interface",
            "PositionBar.Index": "60", "PositionBar.LibraryFile": "LibraryFile.Interface",
            "ShowBackgroundSlider": "true", "RuntimeLayout": "LayoutList after SelectedInfo/map size",
        }, parent=parent, source=source))

    w["controls"] = generated + controls
    w["deterministicBigMapRows"] = {
        "npcRows": 24, "monsterRows": 24, "neutralVisible": False, "rowHeight": 22,
        "scrollChange": 1, "runtimeMapInfoInvented": False, "runtimeNPCsInvented": False, "runtimeMonstersInvented": False,
    }
    return len(generated)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--zircon-root", type=Path, required=True)
    args = parser.parse_args()
    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    assert_source(args.zircon_root)

    counts = {
        "RankingBox": ranking_rows(spec),
        "DungeonFinderBox": dungeon_rows(spec),
        "FortuneCheckerBox": fortune_rows(spec),
        "BigMapBox": bigmap_rows(spec),
    }
    total = sum(counts.values())
    spec["deterministicSourceRowPass"] = {
        "windows": counts,
        "controlsAdded": total,
        "runtimePayloadsInvented": False,
        "source": "current Zircon deterministic constructor/helper row arrays",
    }
    args.spec.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Deterministic Zircon row composites expanded: {total} controls -> {counts}")


if __name__ == "__main__":
    main()
