#!/usr/bin/env python3
"""Sanitize inspection-only fallbacks from the final source reference viewer.

The catalog/QA shell may use technical names, but the reconstructed game stage
must never render a C# field/control name just because source-visible text is
absent.  Image-backed root controls also do not own the synthetic title/close
chrome that the early viewer added for navigation convenience.
"""
from __future__ import annotations

import argparse
from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"Generated viewer contract changed for {label}: expected 1 occurrence, got {count}")
    return text.replace(old, new, 1)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--app-layout", type=Path, required=True)
    args = parser.parse_args()

    text = args.app_layout.read_text(encoding="utf-8")

    replacements = [
        (
            "sourceText(p.TabButton || p.Label || p.Text, control.name.replace(/Tab$/,''))",
            "sourceText(p.TabButton || p.Label || p.Text, '')",
            "tab internal-name fallback",
        ),
        (
            "sourceText(p.Label || p.Text,control.name)",
            "sourceText(p.Label || p.Text,'')",
            "generated button internal-name fallback",
        ),
        (
            "sourceText(p.Text,control.name)",
            "sourceText(p.Text,'')",
            "DXLabel internal-name fallback",
        ),
        (
            "sourceText(p.Label || p.Text, control.name)",
            "sourceText(p.Label || p.Text, '')",
            "DXCheckBox internal-name fallback",
        ),
        (
            "    element.title = `${control.name}: ${control.type}`;\n",
            "",
            "indexed image technical tooltip",
        ),
        (
            "        element.style.width = `${node.width}px`; element.style.height = `${node.height}px`; element.title = `${control.name}: DXButton`;\n",
            "        element.style.width = `${node.width}px`; element.style.height = `${node.height}px`;\n",
            "indexed button technical tooltip",
        ),
        (
            "      element.style.left = `${node.x}px`; element.style.top = `${node.y}px`; element.style.width = `${node.width}px`; element.style.height = `${node.height}px`; element.title = control.name;\n",
            "      element.style.left = `${node.x}px`; element.style.top = `${node.y}px`; element.style.width = `${node.width}px`; element.style.height = `${node.height}px`;\n",
            "item-cell technical tooltip",
        ),
    ]
    for old, new, label in replacements:
        text = replace_once(text, old, new, label)

    image_window_chrome = """  const close = image(asset('Interface',15), Math.max(0,width-24), 3, 'close', root);\n  close.addEventListener('click', () => root.remove());\n  const heading = document.createElement('div');\n  heading.className = 'window-title';\n  heading.textContent = title;\n  root.append(heading);\n"""
    text = replace_once(text, image_window_chrome, "", "synthetic DXImageControl root title/close")

    forbidden_stage_fallbacks = [
        "sourceText(p.Text,control.name)",
        "sourceText(p.Label || p.Text,control.name)",
        "sourceText(p.Label || p.Text, control.name)",
        "control.name.replace(/Tab$/,'')",
        "`${control.name}: DXButton`",
        "`${control.name}: ${control.type}`",
        "element.title = control.name",
        "className = 'window-title'",
    ]
    leaked = [value for value in forbidden_stage_fallbacks if value in text]
    if leaked:
        raise SystemExit(f"Technical stage fallback survived sanitization: {leaked}")

    args.app_layout.write_text(text, encoding="utf-8")
    print("Final viewer sanitized: no control-name fallbacks, debug tooltips or synthetic image-root chrome")


if __name__ == "__main__":
    main()
