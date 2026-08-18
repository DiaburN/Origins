#!/usr/bin/env python3
"""Promote Zircon's exact empty-text DXLabel autosize semantics.

DXLabel.AutoSize defaults to true and DXLabel.GetSize returns Size.Empty when
Text is null or empty.  The browser layout fallback must therefore not invent
geometry from a control identifier for neutral/runtime-bound labels that have
no constructor text yet.

This pass derives only Size.Empty for labels whose final neutral text is known
empty.  It adds no controls and does not invent runtime/player/server text.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


EMPTY_TEXT_EXPRESSIONS = {'""', 'string.Empty', 'String.Empty'}


def source_contract(zircon_root: Path) -> None:
    path = zircon_root / "Client/Controls/DXLabel.cs"
    text = path.read_text(encoding="utf-8-sig")
    required = [
        "public static Size GetSize(string text, Font font, bool outline, int paddingBottom = 0)",
        "if (string.IsNullOrEmpty(text))",
        "return Size.Empty;",
        "AutoSize = true;",
        "Size = GetSize(Text, Font, Outline, PaddingBottom);",
    ]
    missing = [needle for needle in required if needle not in text]
    if missing:
        raise SystemExit(f"DXLabel empty autosize source contract changed: missing {missing}")


def neutral_text_is_empty(control: dict) -> bool:
    props = control.get("properties") or {}
    if "resolvedText" in control:
        return str(control.get("resolvedText") or "") == ""
    if "Text" not in props:
        # DXControl.Text defaults to string.Empty; DXLabel constructor does not
        # assign a non-empty value unless the source initializer/post-assignment
        # supplies one, which the parser promotes into properties.Text.
        return True
    return str(props.get("Text") or "").strip() in EMPTY_TEXT_EXPRESSIONS


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--zircon-root", type=Path, required=True)
    args = parser.parse_args()

    source_contract(args.zircon_root)
    spec = json.loads(args.spec.read_text(encoding="utf-8"))

    changed = 0
    fields: list[str] = []
    for item in [*(spec.get("windows") or []), *(spec.get("nestedWindows") or [])]:
        for control in item.get("controls") or []:
            if control.get("type") != "DXLabel":
                continue
            props = control.get("properties") or {}
            if "Size" in props:
                continue
            if str(props.get("AutoSize") or "").strip().lower() == "false":
                continue
            if not neutral_text_is_empty(control):
                continue

            props["Size"] = "Size.Empty"
            control["sourceDerivedEmptyTextSize"] = True
            control["sourceDerivedEmptyTextSizeContract"] = "DXLabel.GetSize: empty Text => Size.Empty"
            changed += 1
            fields.append(f"{item.get('field') or item.get('id')}:{control.get('name')}")

    spec["emptyAutoSizeLabelPass"] = {
        "passed": True,
        "labelsResolvedToSizeEmpty": changed,
        "sourceContract": "Client/Controls/DXLabel.cs GetSize + AutoSize default",
        "controlsAdded": 0,
        "controlsRemoved": 0,
        "runtimeTextInvented": False,
        "runtimePayloadsInvented": False,
        "examples": fields[:12],
    }
    args.spec.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Empty DXLabel autosize geometry: PASS -> {changed} neutral labels use Size.Empty; controls +0")


if __name__ == "__main__":
    main()
