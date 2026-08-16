#!/usr/bin/env python3
"""Promote the reference viewer to source-addressable interactive desktop mode.

Build-time only:
- removes the single-window eviction inside openWindow,
- focuses an already-open window instead of duplicating it,
- tags every rendered control with its Zircon C# name/type and stable manifest index,
- preserves each rendered control's source Parent expression as DOM metadata,
- reproduces DXNumberBox Up/Down behavior from Zircon using real 1010/1011 buttons,
- reproduces DXSoundBar mute/value/track/drag behavior from Zircon using 4740-4746.

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

NUMBERBOX_NEW = """function renderNumberBox(control,node,parent) {\n  const p = control.properties || {};\n  const scalar = (expression,fallback) => {\n    const value = String(expression ?? '').trim();\n    const match = value.match(/^\\(*\\s*(-?\\d+)\\s*\\)*$/);\n    return match ? Number(match[1]) : fallback;\n  };\n  const root = document.createElement('div');\n  root.className = 'dx-numberbox';\n  root.style.left = `${node.x}px`; root.style.top = `${node.y}px`; root.style.width = `${node.width}px`; root.style.height = `${node.height}px`;\n  parent.append(root);\n\n  const change = scalar(p.Change,10);\n  const minValue = scalar(p.MinValue,0);\n  const maxValue = Math.max(minValue,scalar(p.MaxValue,0));\n  let value = Math.max(minValue,Math.min(maxValue,scalar(p.Value,0)));\n\n  const down = image(asset('GameInter',1011),0,1,'ui-button dx-number-down',root);\n  down.style.pointerEvents = 'auto';\n  down.style.cursor = 'pointer';\n  const field = document.createElement('div');\n  field.className = 'dx-textbox dx-number-value'; field.style.left = '19px'; field.style.top = '1px'; field.style.width = '50px'; field.style.height = '20px';\n  root.append(field);\n  const up = image(asset('GameInter',1010),Math.max(0,node.width-17),1,'ui-button dx-number-up',root);\n  up.style.pointerEvents = 'auto';\n  up.style.cursor = 'pointer';\n\n  const setValue = next => {\n    value = Math.max(minValue,Math.min(maxValue,Math.trunc(next)));\n    field.textContent = value.toLocaleString('en-US');\n    root.dataset.value = String(value);\n  };\n  setValue(value);\n  down.addEventListener('click',event=>{event.preventDefault();event.stopPropagation();setValue(value-change)});\n  up.addEventListener('click',event=>{event.preventDefault();event.stopPropagation();setValue(value+change)});\n  return root;\n}\n"""

NUMBERBOX_CASE_OLD = """    case 'DXNumberBox': return renderNumberBox(node,root);\n"""
NUMBERBOX_CASE_NEW = """    case 'DXNumberBox': return renderNumberBox(control,node,root);\n"""

SOUNDBAR_OLD = """function renderSoundBar(node,parent) {\n  const root = document.createElement('div');\n  root.className = 'dx-soundbar';\n  root.style.left = `${node.x}px`; root.style.top = `${node.y}px`; root.style.width = `${node.width}px`; root.style.height = `${node.height}px`;\n  parent.append(root);\n  image(asset('GameInter',4741),0,1,'ui-button',root);\n  image(asset('GameInter',4743),20,3,'ui-img',root);\n  const inner = image(asset('GameInter',4742),22,5,'ui-img dx-sound-inner',root); inner.style.clipPath = 'inset(0 35% 0 0)';\n  image(asset('GameInter',4746),Math.max(100,node.width-18),1,'ui-button',root);\n  return root;\n}\n"""

SOUNDBAR_NEW = """function renderSoundBar(control,node,parent) {\n  const p = control.properties || {};\n  const scalar = (expression,fallback) => {\n    const raw = String(expression ?? '').trim();\n    const match = raw.match(/^\\(*\\s*(-?\\d+)\\s*\\)*$/);\n    return match ? Number(match[1]) : fallback;\n  };\n  const root = document.createElement('div');\n  root.className = 'dx-soundbar';\n  root.style.left = `${node.x}px`; root.style.top = `${node.y}px`; root.style.width = `${node.width}px`; root.style.height = `${node.height}px`;\n  parent.append(root);\n\n  // DXConfigWindow.OnVisibleChanged loads Config.*Volume into each bar. The\n  // public Zircon Config defaults all five volumes to 25 and mute=false.\n  let value = Math.max(0,Math.min(100,scalar(p.Value,25)));\n  let muted = boolFrom(p.Muted,false);\n\n  const trackHit = document.createElement('div');\n  trackHit.className = 'dx-sound-track-hit';\n  trackHit.style.position = 'absolute'; trackHit.style.left = '5px'; trackHit.style.top = '0';\n  trackHit.style.width = '195px'; trackHit.style.height = '18px'; trackHit.style.pointerEvents = 'auto';\n  root.append(trackHit);\n\n  const outer = image(asset('GameInter',4743),20,3,'ui-img dx-sound-outer',root);\n  const inner = image(asset('GameInter',4742),22,5,'ui-img dx-sound-inner',root);\n  const icon = image(asset('GameInter',muted ? 4740 : 4741),0,1,'ui-button dx-sound-icon',root);\n  icon.style.pointerEvents = 'auto'; icon.style.cursor = 'pointer';\n  const slider = image(asset('GameInter',4746),21,1,'ui-button dx-sound-slider',root);\n  slider.style.pointerEvents = 'auto'; slider.style.cursor = 'ew-resize';\n\n  const scrollWidth = 145; // DXHScrollBar: Size.Width(195) - 50.\n  const scrollLeft = 5;\n  const positionStart = 16;\n  const sliderSize = getAssetSize(sourceSpec,'GameInter',4746) || [16,16];\n\n  const setValue = next => {\n    value = Math.max(0,Math.min(100,Math.round(next)));\n    // C# UpdateScrollBar uses an int cast here, therefore truncation is exact.\n    const positionX = positionStart + Math.trunc(scrollWidth * (value / 100));\n    slider.style.left = `${scrollLeft + positionX}px`;\n    inner.style.clipPath = `inset(0 ${100-value}% 0 0)`;\n    root.dataset.value = String(value);\n  };\n  const setMuted = next => {\n    muted = Boolean(next);\n    icon.src = asset('GameInter',muted ? 4740 : 4741);\n    root.dataset.muted = String(muted);\n  };\n  setValue(value); setMuted(muted);\n\n  icon.addEventListener('click',event=>{\n    event.preventDefault(); event.stopPropagation(); setMuted(!muted);\n  });\n\n  // DXHScrollBar.OnMouseDown: round((x - (barWidth + barWidth/2))*100/145).\n  trackHit.addEventListener('pointerdown',event=>{\n    if (event.button !== 0) return;\n    const rect = trackHit.getBoundingClientRect();\n    const localX = event.clientX - rect.left;\n    const next = Math.round((localX - (sliderSize[0] + sliderSize[0] / 2)) * 100 / scrollWidth);\n    setValue(next);\n  });\n\n  slider.addEventListener('pointerdown',event=>{\n    if (event.button !== 0) return;\n    event.preventDefault(); event.stopPropagation();\n    slider.src = asset('GameInter',4745);\n    slider.setPointerCapture?.(event.pointerId);\n    const sliderRect = slider.getBoundingClientRect();\n    const grabOffset = event.clientX - sliderRect.left;\n    const rootRect = root.getBoundingClientRect();\n\n    const move = moveEvent => {\n      // DXHScrollBar.PositionBar_Moving: round((PositionBar.X-16)*100/145).\n      const desiredAbsolute = moveEvent.clientX - grabOffset - rootRect.left;\n      const positionX = Math.max(positionStart,Math.min(positionStart+scrollWidth,desiredAbsolute-scrollLeft));\n      setValue(Math.round((positionX-positionStart)*100/scrollWidth));\n    };\n    const end = endEvent => {\n      slider.releasePointerCapture?.(endEvent.pointerId);\n      slider.src = asset('GameInter',4746);\n      slider.removeEventListener('pointermove',move);\n      slider.removeEventListener('pointerup',end);\n      slider.removeEventListener('pointercancel',end);\n    };\n    slider.addEventListener('pointermove',move);\n    slider.addEventListener('pointerup',end);\n    slider.addEventListener('pointercancel',end);\n  });\n\n  outer.style.pointerEvents = 'none'; inner.style.pointerEvents = 'none';\n  return root;\n}\n"""

SOUNDBAR_CASE_OLD = """    case 'DXSoundBar': return renderSoundBar(node,root);\n"""
SOUNDBAR_CASE_NEW = """    case 'DXSoundBar': return renderSoundBar(control,node,root);\n"""


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
    text = replace_exact(text, SOUNDBAR_OLD, SOUNDBAR_NEW, "DXSoundBar renderer")
    text = replace_exact(text, SOUNDBAR_CASE_OLD, SOUNDBAR_CASE_NEW, "DXSoundBar render dispatch")
    args.app.write_text(text, encoding="utf-8")
    print("Patched openWindow for simultaneous Zircon dialogs")
    print("Tagged rendered controls with stable source indices/names/types/parents")
    print("Patched DXNumberBox with clickable 1011/1010 Change/Min/Max behavior")
    print("Patched DXSoundBar with 4740-4746 mute/value/track/drag behavior")


if __name__ == "__main__":
    main()
