#!/usr/bin/env python3
"""Materialise FilterDropDialog's deterministic ten-row constructor loop.

The lightweight constructor parser sees one lexical loop template. Zircon
actually creates ten DXLabel + ten DXTextBox controls. Replace exactly that
single template pair with the ten source-backed iterations; do not invent the
saved Config.HighlightedItems payload.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

COUNT = 10
LABEL_HEIGHT = 16
PREFIX = "FilterDropGenerated"
SOURCE_TAG = "FilterDropDialog constructor for-loop"


def make(name: str, type_name: str, properties: dict[str, str], **extra) -> dict:
    control = {
        "name": name,
        "type": type_name,
        "properties": dict(properties),
        "sourceGenerated": SOURCE_TAG,
        "runtimePayloadInvented": False,
    }
    control.update(extra)
    return control


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--zircon-root", type=Path, required=True)
    args = parser.parse_args()

    source_path = args.zircon_root / "Client/Scenes/Views/FilterDropDialog.cs"
    source = source_path.read_text(encoding="utf-8-sig")
    needles = (
        "SetClientSize(new Size(266, 371));",
        "for (int i = 0; i < 10; i++)",
        "DXLabel filterLabel = new DXLabel",
        "Text = string.Format(CEnvir.Language.FilterDialogFilterLabel, (i + 1))",
        "filterLabel.Location = new Point(20, 50 + (10 + filterLabel.Size.Height) * i);",
        "DropFiltersMap[i] = new DXTextBox",
        "Border = true,",
        "BorderColour = Constants.PrimaryColour,",
        "Location = new Point(90, filterLabel.Location.Y),",
        "Size = new Size(150, 18)",
        "Config.HighlightedItems = String.Join(\",\", dropItems);",
    )
    for needle in needles:
        if needle not in source:
            raise SystemExit(f"FilterDrop source changed: missing {needle!r}")

    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    window = next((w for w in spec.get("windows", []) if w.get("field") == "FilterDropBox"), None)
    if window is None:
        raise SystemExit("FilterDropBox missing from manifest")

    original = [c for c in window.get("controls", []) if not str(c.get("name") or "").startswith(PREFIX)]
    label_templates = [
        c for c in original
        if c.get("type") == "DXLabel" and str(c.get("sourceName") or c.get("name") or "") == "filterLabel"
    ]
    textbox_templates = [c for c in original if c.get("type") == "DXTextBox"]
    if len(label_templates) != 1 or len(textbox_templates) != 1:
        raise SystemExit(
            "FilterDrop loop template drifted before expansion: "
            f"labels={[(c.get('name'), c.get('type')) for c in label_templates]} "
            f"textboxes={[(c.get('name'), c.get('type')) for c in textbox_templates]}"
        )

    remove_ids = {id(label_templates[0]), id(textbox_templates[0])}
    controls = [c for c in original if id(c) not in remove_ids]
    english = (spec.get("language") or {}).get("English") or {}
    template = str(english.get("FilterDialogFilterLabel") or "Filter {0}")
    generated: list[dict] = []

    for i in range(COUNT):
        number = i + 1
        y = 50 + (10 + LABEL_HEIGHT) * i
        try:
            resolved = template.format(number)
        except (IndexError, KeyError, ValueError):
            resolved = f"Filter {number}"
        source_text = f"string.Format(CEnvir.Language.FilterDialogFilterLabel, {number})"
        generated.append(make(
            f"{PREFIX}Label{number:02d}",
            "DXLabel",
            {
                "Parent": "this",
                "Location": f"new Point(20, {y})",
                "Text": json.dumps(resolved, ensure_ascii=False),
            },
            resolvedText=resolved,
            resolvedLanguageKey="FilterDialogFilterLabel",
            sourceTextExpression=source_text,
            sourceLocationExpression=f"new Point(20, 50 + (10 + filterLabel.Size.Height) * {i})",
            sourceLoopIteration=i,
        ))
        generated.append(make(
            f"{PREFIX}TextBox{number:02d}",
            "DXTextBox",
            {
                "Parent": "this",
                "Border": "true",
                "BorderColour": "Constants.PrimaryColour",
                "Location": f"new Point(90, {y})",
                "Size": "new Size(150, 18)",
            },
            sourceLocationExpression="new Point(90, filterLabel.Location.Y)",
            sourceLoopIteration=i,
        ))

    if len(generated) != 20:
        raise SystemExit(f"FilterDrop loop expansion count drifted: {len(generated)}")
    window["controls"] = generated + controls
    window["filterDropSourceLoop"] = {
        "passed": True,
        "count": COUNT,
        "labels": COUNT,
        "textBoxes": COUNT,
        "controlsMaterialized": 20,
        "templateControlsRemoved": 2,
        "netControlsAdded": 18,
        "labelDefaultReferenceHeight": LABEL_HEIGHT,
        "textBoxX": 90,
        "textBoxSize": [150, 18],
        "border": True,
        "borderColour": "Constants.PrimaryColour",
        "checkedInConfigHighlightedItems": "",
        "runtimeHighlightedItemsInvented": False,
        "source": "Client/Scenes/Views/FilterDropDialog.cs constructor for (int i = 0; i < 10; i++)",
    }
    args.spec.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("FilterDrop source loop expanded: 10 labels + 10 text boxes; parser template pair replaced; net +18")


if __name__ == "__main__":
    main()
