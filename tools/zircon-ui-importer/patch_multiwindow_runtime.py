#!/usr/bin/env python3
"""Promote the reference viewer to source-addressable multi-window mode.

Build-time only:
- removes the single-window eviction inside openWindow,
- focuses an already-open window instead of duplicating it,
- tags every rendered control with its original Zircon C# control name/type,
- preserves each rendered control's source Parent expression as DOM metadata for
  tab/content hierarchy runtimes.

Close-all/reset still use removeTransientWindows().
"""
from __future__ import annotations

import argparse
from pathlib import Path

OPEN_OLD = """  removeTransientWindows();\n  const item = itemById(id);\n"""
OPEN_NEW = """  const existing = windows.get(id);\n  if (existing?.isConnected) {\n    existing.dispatchEvent(new CustomEvent('origins:focus', {bubbles:true}));\n    document.querySelector(`[data-window-id=\\\"${id}\\\"]`)?.classList.add('active');\n    return;\n  }\n  const item = itemById(id);\n"""

RENDER_OLD = """  for (const node of layout.nodes) renderControl(node,root);\n"""
RENDER_NEW = """  for (const node of layout.nodes) {\n    const rendered = renderControl(node,root);\n    if (rendered) {\n      rendered.dataset.controlName = node.control.name;\n      rendered.dataset.controlType = node.control.type;\n      const sourceParent = node.control.properties?.Parent;\n      if (sourceParent !== undefined) rendered.dataset.parentControl = String(sourceParent);\n    }\n  }\n"""


def replace_exact(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"Expected exactly one {label}, found {count}")
    return text.replace(old, new, 1)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("app", type=Path)
    args = parser.parse_args()

    text = args.app.read_text(encoding="utf-8")
    text = replace_exact(text, OPEN_OLD, OPEN_NEW, "single-window openWindow eviction")
    text = replace_exact(text, RENDER_OLD, RENDER_NEW, "source control render loop")
    args.app.write_text(text, encoding="utf-8")
    print("Patched openWindow for simultaneous Zircon dialogs")
    print("Tagged rendered controls with source C# names/types/parents")


if __name__ == "__main__":
    main()
