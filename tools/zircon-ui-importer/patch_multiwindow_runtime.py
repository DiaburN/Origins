#!/usr/bin/env python3
"""Promote the reference viewer from single-dialog mode to Zircon multi-window mode.

The source renderer remains unchanged; this build-time transform removes only the
single-window eviction inside openWindow and adds focus handling for an already
open dialog. Close-all/reset continue to use removeTransientWindows().
"""
from __future__ import annotations

import argparse
from pathlib import Path

OLD = """  removeTransientWindows();\n  const item = itemById(id);\n"""
NEW = """  const existing = windows.get(id);\n  if (existing?.isConnected) {\n    existing.dispatchEvent(new CustomEvent('origins:focus', {bubbles:true}));\n    document.querySelector(`[data-window-id=\\\"${id}\\\"]`)?.classList.add('active');\n    return;\n  }\n  const item = itemById(id);\n"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("app", type=Path)
    args = parser.parse_args()

    text = args.app.read_text(encoding="utf-8")
    count = text.count(OLD)
    if count != 1:
        raise SystemExit(f"Expected exactly one single-window openWindow eviction, found {count}")
    text = text.replace(OLD, NEW, 1)
    args.app.write_text(text, encoding="utf-8")
    print("Patched openWindow for simultaneous Zircon dialogs")


if __name__ == "__main__":
    main()
