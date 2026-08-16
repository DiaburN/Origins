#!/usr/bin/env python3
"""Promote the reference viewer to source-addressable interactive desktop mode.

Build-time only:
- removes the single-window eviction inside openWindow,
- focuses an already-open window instead of duplicating it,
- tags every rendered control with its Zircon C# name/type and stable manifest index,
- preserves each rendered control's source Parent expression as DOM metadata,
- reproduces DXNumberBox Up/Down behavior from Zircon using the real 1010/1011 buttons.

Close-all/reset still use removeTransientWindows().
"""
from __future__ import annotations

import argparse
from pathlib import Path

OPEN_OLD = """  removeTransientWindows();\n  const item = itemById(id);\n"""
OPEN_NEW = """  const existing = windows.get(id);\n  if (existing?.isConnected) {\n    existing.dispatchEvent(new CustomEvent('origins:focus', {bubbles:true}));\n    document.querySelector(`[data-window-id=\\\"${id}\\\"]`)?.classList.add('active');\n    return;\n  }\n  const item = itemById(id);\n"""

RENDER_OLD = """  for (const node of layout.nodes) renderControl(node,root);\n"""
RENDER_NEW = """  for (let controlIndex = 0; controlIndex < layout.nodes.length; controlIndex++) {\n    const node = layout.nodes[controlIndex];\n    const rendered = renderControl(node,root);\n    if (rendered) {\n      rendered.dataset.controlIndex = String(controlIndex);\n      rendered.dataset.controlName = node.control.name;\n      rendered.dataset.controlType = node.control.type;\n      const sourceParent = node.control.properties?.Parent;\n      if (sourceParent !== undefined) rendered.dataset.parentControl = String(sourceParent);\n    }\n  }\n"""

NUMBERBOX_OLD = """function renderNumberBox(node,parent) {\n  const root = document.createElement('div');\n  root.className = 'dx-numberbox';\n  root.style.left = `${node.x}px`; root.style.top = `${node.y}px`; root.style.width = `${node.width}px`; root.style.height = `${node.height}px`;\n  parent.append(root);\n  image(asset('GameInter',1011),0,1,'ui-button',root);\n  const field = document.createElement('div');\n  field.className = 'dx-textbox'; field.style.left = '19px'; field.style.top = '1px'; field.style.width = '50px'; field.style.height = '20px'; field.textContent = '0';\n  root.append(field);\n  image(asset('GameInter',1010),Math.max(0,node.width-17),1,'ui-button',root);\n  return root;\n}\n"""

NUMBERBOX_NEW = """function renderNumberBox(control,node,parent) {\n  const p = control.properties || {};\n  const scalar = (expression,fallback) => {\n    const value = String(expression ?? '').trim();\n    const match = value.match(/^\\(*\\s*(-?\\d+)\\s*\\)*$/);\n    return match ? Number(match[1]) : fallback;\n  };\n  const root = document.createElement('div');\n  root.className = 'dx-numberbox';\n  root.style.left = `${node.x}px`; root.style.top = `${node.y}px`; root.style.width = `${node.width}px`; root.style.height = `${node.height}px`;\n  parent.append(root);\n\n  const change = scalar(p.Change,10);\n  const minValue = scalar(p.MinValue,0);\n  const maxValue = Math.max(minValue,scalar(p.MaxValue,0));\n  let value = Math.max(minValue,Math.min(maxValue,scalar(p.Value,0)));\n\n  const down = image(asset('GameInter',1011),0,1,'ui-button dx-number-down',root);\n  const field = document.createElement('div');\n  field.className = 'dx-textbox dx-number-value'; field.style.left = '19px'; field.style.top = '1px'; field.style.width = '50px'; field.style.height = '20px';\n  root.append(field);\n  const up = image(asset('GameInter',1010),Math.max(0,node.width-17),1,'ui-button dx-number-up',root);\n\n  const setValue = next => {\n    value = Math.max(minValue,Math.min(maxValue,Math.trunc(next)));\n    field.textContent = value.toLocaleString('en-US');\n    root.dataset.value = String(value);\n  };\n  setValue(value);\n  down.addEventListener('click',event=>{event.stopPropagation();setValue(value-change)});\n  up.addEventListener('click',event=>{event.stopPropagation();setValue(value+change)});\n  return root;\n}\n"""

NUMBERBOX_CASE_OLD = """    case 'DXNumberBox': return renderNumberBox(node,root);\n"""
NUMBERBOX_CASE_NEW = """    case 'DXNumberBox': return renderNumberBox(control,node,root);\n"""


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
    text = replace_exact(text, NUMBERBOX_OLD, NUMBERBOX_NEW, "DXNumberBox renderer")
    text = replace_exact(text, NUMBERBOX_CASE_OLD, NUMBERBOX_CASE_NEW, "DXNumberBox render dispatch")
    args.app.write_text(text, encoding="utf-8")
    print("Patched openWindow for simultaneous Zircon dialogs")
    print("Tagged rendered controls with stable source indices/names/types/parents")
    print("Patched DXNumberBox with Zircon Change/Min/Max clamped Up/Down behavior")


if __name__ == "__main__":
    main()
