#!/usr/bin/env python3
"""Sanitize/fix inspection-only fallbacks in the final source viewer.

The catalog/QA shell may use technical names, but the reconstructed game stage
must not render C# field/control names as game text. Image controls also need a
strict distinction between a real literal source index, an animated BaseIndex,
and runtime-only data (Index=-1 / symbolic runtime index).
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

    old_index_parser = """function indexFrom(expression) {\n  const match = String(expression ?? '').match(/\\b(\\d+)\\b/);\n  return match ? Number(match[1]) : null;\n}\n"""
    new_index_parser = """function indexFrom(expression) {\n  const value = String(expression ?? '').trim();\n  return /^-?\\d+$/.test(value) ? Number(value) : null;\n}\n"""
    text = replace_once(text, old_index_parser, new_index_parser, "literal image-index parser")

    old_image_block = """  if ((control.type === 'DXImageControl' || control.type === 'DXAnimatedControl') && library && index !== null) {\n    const element = image(asset(library,index),node.x,node.y,'ui-img',root);\n    element.style.width = `${node.width}px`; element.style.height = `${node.height}px`;\n    element.title = `${control.name}: ${control.type}`;\n    return element;\n  }\n"""
    new_image_block = """  if (control.type === 'DXImageControl' || control.type === 'DXAnimatedControl') {\n    const baseIndex = indexFrom(p.BaseIndex);\n    const resolvedImageIndex = index !== null && index >= 0 ? index : (baseIndex !== null && baseIndex >= 0 ? baseIndex : null);\n    if (library && resolvedImageIndex !== null) {\n      const element = image(asset(library,resolvedImageIndex),node.x,node.y,'ui-img',root);\n      element.style.width = `${node.width}px`; element.style.height = `${node.height}px`;\n      element.dataset.sourceIndexOrigin = index !== null && index >= 0 ? 'Index' : 'BaseIndex';\n      return element;\n    }\n    if (boolFrom(p.DrawTexture,false) || boolFrom(p.Border,false) || p.BackColour !== undefined)\n      return renderStructuralControl(control,node,root);\n    return null;\n  }\n"""
    text = replace_once(text, old_image_block, new_image_block, "DXImageControl/DXAnimatedControl neutral-index renderer")

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
            "        element.style.width = `${node.width}px`; element.style.height = `${node.height}px`; element.title = `${control.name}: DXButton`;\n",
            "        element.style.width = `${node.width}px`; element.style.height = `${node.height}px`;\n",
            "indexed button technical tooltip",
        ),
        (
            "      element.style.left = `${node.x}px`; element.style.top = `${node.y}px`; element.style.width = `${node.width}px`; element.style.height = `${node.height}px`; element.title = control.name;\n",
            "      element.style.left = `${node.x}px`; element.style.top = `${node.y}px`; element.style.width = `${node.width}px`; element.style.height = `${node.height}px`;\n",
            "item-cell technical tooltip",
        ),
        (
            "      if (library && index !== null) {",
            "      if (library && index !== null && index >= 0) {",
            "DXButton negative-index guard",
        ),
        (
            "  if (rootLibrary && rootIndex !== null) {",
            "  if (rootLibrary && rootIndex !== null && rootIndex >= 0) {",
            "root image negative-index guard",
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
        "match(/\\b(\\d+)\\b/)",
    ]
    leaked = [value for value in forbidden_stage_fallbacks if value in text]
    if leaked:
        raise SystemExit(f"Technical/unsafe stage fallback survived sanitization: {leaked}")

    args.app_layout.write_text(text, encoding="utf-8")

    animated_path = args.app_layout.parent / "animated-control-runtime.js"
    if not animated_path.exists():
        raise SystemExit(f"Animated runtime missing before sanitization: {animated_path}")
    animated = animated_path.read_text(encoding="utf-8")
    animated = replace_once(
        animated,
        "const p=control.properties||{},library=libraryFrom(p.LibraryFile),base=intFrom(p.BaseIndex),count=intFrom(p.FrameCount);",
        "const p=control.properties||{},library=libraryFrom(p.LibraryFile),base=intFrom(p.BaseIndex) ?? intFrom(p.Index),count=intFrom(p.FrameCount);",
        "DXAnimatedControl BaseIndex/Index base selection",
    )
    animated_path.write_text(animated, encoding="utf-8")

    print("Final viewer sanitized: literal indices only; runtime images neutral; index-driven animations supported")


if __name__ == "__main__":
    main()
