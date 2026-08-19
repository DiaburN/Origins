#!/usr/bin/env python3
"""Patch built nested/transient runtime to honour source-indexed artwork."""
from __future__ import annotations
import argparse
from pathlib import Path

HELPER_MARKER="const asset = (library,index) => `assets/${library}/${pad(index)}.png`;\n"
HELPER_INSERT=HELPER_MARKER+"""
function nestedLibraryFrom(raw) {
  const match=String(raw??'').match(/LibraryFile\.([A-Za-z0-9_]+)/);
  return match?match[1]:null;
}
function nestedIndexFrom(raw) {
  const match=String(raw??'').trim().match(/^-?\d+$/);
  return match?Number(match[0]):null;
}
"""
BUTTON_OLD="""function renderNestedButton(control,node,root) {
  const width=node.width||80,height=node.height||20;
  const button=document.createElement('div'); button.className='dx-generated-button dx-button-Default';
"""
BUTTON_NEW="""function renderNestedButton(control,node,root) {
  const p=control.properties||{};
  const width=node.width||80,height=node.height||20;
  const sourceLibrary=nestedLibraryFrom(p.LibraryFile),sourceIndex=nestedIndexFrom(p.Index);
  if(sourceLibrary && sourceIndex!==null && sourceIndex>=0) {
    const button=img(sourceLibrary,sourceIndex,node.x,node.y,root,'ui-button nested-indexed-button');
    button.style.width=`${width}px`;button.style.height=`${height}px`;
    button.style.pointerEvents='auto';button.style.cursor='pointer';
    button.dataset.controlName=control.name;button.dataset.controlType=control.type;
    button.dataset.sourceLibrary=sourceLibrary;button.dataset.sourceIndex=String(sourceIndex);
    if(/CancelButton$|CloseButton$|OKButton$|NoButton$|YesButton$|SelectButton$/.test(control.name)) button.addEventListener('click',()=>root.remove());
    return button;
  }
  const button=document.createElement('div'); button.className='dx-generated-button dx-button-Default';
"""
CONTROL_MARKER="""  if(control.type==='DXButton') return renderNestedButton(control,node,root);
  if(control.type==='DXLabel') {
"""
CONTROL_INSERT="""  if(control.type==='DXButton') return renderNestedButton(control,node,root);
  if(control.type==='DXImageControl'||control.type==='DXAnimatedControl') {
    const sourceLibrary=nestedLibraryFrom(p.LibraryFile),sourceIndex=nestedIndexFrom(p.Index);
    if(sourceLibrary && sourceIndex!==null && sourceIndex>=0) {
      const el=img(sourceLibrary,sourceIndex,node.x,node.y,root,'ui-img nested-indexed-image');
      el.style.width=`${node.width}px`;el.style.height=`${node.height}px`;el.style.pointerEvents='none';
      el.dataset.sourceLibrary=sourceLibrary;el.dataset.sourceIndex=String(sourceIndex);return el;
    }
    const el=document.createElement('div');el.className='dx-structural-control nested-image-structural';
    el.style.position='absolute';el.style.left=`${node.x}px`;el.style.top=`${node.y}px`;el.style.width=`${node.width}px`;el.style.height=`${node.height}px`;
    if(boolValue(p.Border,false))el.style.border='1px solid rgb(93,70,37)';
    el.style.background=sourceColour(p.BackColour,'transparent');root.append(el);return el;
  }
  if(control.type==='DXLabel') {
"""

def replace_once(text,old,new,label):
    count=text.count(old)
    if count!=1: raise SystemExit(f'Expected one {label}, found {count}')
    return text.replace(old,new,1)

def main():
    p=argparse.ArgumentParser();p.add_argument('runtime',type=Path);args=p.parse_args()
    text=args.runtime.read_text(encoding='utf-8')
    text=replace_once(text,HELPER_MARKER,HELPER_INSERT,'asset helper marker')
    text=replace_once(text,BUTTON_OLD,BUTTON_NEW,'nested button renderer')
    text=replace_once(text,CONTROL_MARKER,CONTROL_INSERT,'nested control dispatch')
    args.runtime.write_text(text,encoding='utf-8')
    print('Patched nested indexed DXButton/DXImageControl source artwork handling')

if __name__=='__main__': main()
