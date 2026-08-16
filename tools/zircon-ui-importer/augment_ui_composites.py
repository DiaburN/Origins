#!/usr/bin/env python3
"""Expand deterministic child controls of custom Zircon UI composites.

Phase 1 intentionally targets QuestBox custom DXTab instances. Each custom tab
constructor is expanded into source-backed, namespaced child controls so Current,
Available, Milestone and the retained hidden tabs are not empty shells.

Runtime-created data rows/items are NOT fabricated. Tabs with no parameterless
constructor-defined controls are explicitly recorded as runtime-only instead of
being filled with guessed UI.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path

from build_ui_source_spec import (
    LIB_FILE,
    constructor_body,
    literal_indices,
    match_brace,
    simple_assignments,
    split_top_level,
)
from augment_ui_symbols import parse_class_symbols, simplify_geometry, symbol_snapshots

RENDER_TYPES = {
    'DXAnimatedControl','DXButton','DXCheckBox','DXColourControl','DXComboBox',
    'DXConfigTab','DXControl','DXImageControl','DXItemCell','DXItemGrid',
    'DXKeyBindWindow','DXLabel','DXListBox','DXNumberBox','DXNumberTextBox',
    'DXSoundBar','DXTab','DXTabControl','DXTextBox','DXTreeControl','DXVScrollBar',
}
CONTROL_ROOT_KEYS = {
    'LibraryFile','Index','BaseIndex','Size','Location','Visible','BackColour',
    'Border','BorderColour','DrawTexture','AutoSize','Text','Font','ForeColour',
    'IsControl','GridSize','ButtonType','LabelStyle','MinimumTabWidth','Opacity',
    'ReadOnly','FixedSize','Outline','OutlineColour','Parent','Checked',
}
CLASS_RE = re.compile(r'\bclass\s+([A-Za-z_][A-Za-z0-9_]*)\s*:\s*([A-Za-z_][A-Za-z0-9_]*)')
GENERIC_INIT_RE = re.compile(
    r'(?:(?:[A-Za-z_][A-Za-z0-9_<>]*\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*)'
    r'new\s+([A-Za-z_][A-Za-z0-9_]*)\s*\{'
)
CTOR_DECL_RE = re.compile(r'\bpublic\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(([^)]*)\)')


def normalise(value: str) -> str:
    return ' '.join(value.strip().split())


def build_class_index(zircon_root: Path):
    bases: dict[str,str] = {}
    sources: dict[str,Path] = {}
    texts: dict[Path,str] = {}
    for path in (zircon_root/'Client').rglob('*.cs'):
        try:
            text=path.read_text(encoding='utf-8-sig')
        except UnicodeDecodeError:
            continue
        texts[path]=text
        for name,base in CLASS_RE.findall(text):
            bases[name]=base
            sources[name]=path
    return bases,sources,texts


def nearest_render_type(source_type: str, bases: dict[str,str]) -> str|None:
    current=source_type; seen=set()
    while current and current not in seen:
        if current in RENDER_TYPES:
            return current
        seen.add(current); current=bases.get(current,'')
    return None


def constructor_parameterless(text: str, class_name: str) -> bool:
    for name,params in CTOR_DECL_RE.findall(text):
        if name==class_name:
            return not params.strip()
    return False


def parse_control_initializers(body: str, bases: dict[str,str]) -> list[dict]:
    out=[]
    for match in GENERIC_INIT_RE.finditer(body):
        name,source_type=match.groups()
        render_type=nearest_render_type(source_type,bases)
        if not render_type:
            continue
        opening=body.find('{',match.start())
        try: closing=match_brace(body,opening)
        except ValueError: continue
        chunk=body[opening+1:closing]; props={}
        for entry in split_top_level(chunk,','):
            prop=re.match(r'\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.+?)\s*$',entry,re.S)
            if prop: props[prop.group(1)]=normalise(prop.group(2))
        out.append({
            'sourceName':name,'sourceType':source_type,'type':render_type,
            'properties':props,'sourceOffset':match.start(),
        })
    return out


def component_defaults(source_type: str, sources: dict[str,Path], texts: dict[Path,str]) -> dict:
    path=sources.get(source_type)
    if not path: return {}
    text=texts[path]; body=constructor_body(text,source_type)
    if not body: return {}
    return simple_assignments(body,CONTROL_ROOT_KEYS)


def replace_known_names(expression: str, mapping: dict[str,str]) -> str:
    value=str(expression)
    for old in sorted(mapping,key=len,reverse=True):
        value=re.sub(rf'(?<!\.)\b{re.escape(old)}\b',mapping[old],value)
    return normalise(value)


def namespace_children(children: list[dict], parent_name: str) -> list[dict]:
    counts=Counter(child['sourceName'] for child in children)
    sequence=Counter(); unique_map={}
    for child in children:
        source_name=child['sourceName']; sequence[source_name]+=1
        suffix='' if counts[source_name]==1 else f'__{sequence[source_name]}'
        child['name']=f'{parent_name}__{source_name}{suffix}'
        if counts[source_name]==1:
            unique_map[source_name]=child['name']

    for child in children:
        props=child['properties']; parent=normalise(str(props.get('Parent','this')))
        if parent=='this':
            props['Parent']=parent_name
        elif parent in unique_map:
            props['Parent']=unique_map[parent]
        for key,value in list(props.items()):
            if key=='Parent': continue
            props[key]=replace_known_names(value,unique_map)
    return children


def add_asset_refs(spec: dict, controls: list[dict]) -> None:
    refs=spec.setdefault('assetRefs',{})
    for control in controls:
        props=control.get('properties',{})
        libs=LIB_FILE.findall(str(props.get('LibraryFile','')))
        ids=literal_indices(props.get('Index'))
        base_ids=literal_indices(props.get('BaseIndex'))
        for lib in libs:
            bucket={int(v) for v in refs.get(lib,[])}
            bucket.update(ids); bucket.update(base_ids)
            refs[lib]=sorted(bucket)


def expand_instance(instance: dict, bases: dict[str,str], sources: dict[str,Path], texts: dict[Path,str], depth: int, max_depth: int) -> list[dict]:
    source_type=instance.get('sourceType')
    path=sources.get(source_type)
    if not path or depth>max_depth: return []
    text=texts[path]
    if not constructor_parameterless(text,source_type): return []
    body=constructor_body(text,source_type)
    if not body: return []

    raw=parse_control_initializers(body,bases)
    snapshots=symbol_snapshots(body,parse_class_symbols(text),len(raw))
    prepared=[]
    for child,symbols in zip(raw,snapshots):
        defaults=component_defaults(child['sourceType'],sources,texts)
        merged=dict(defaults); merged.update(child['properties']); child['properties']=merged
        simplify_geometry(child,symbols)
        child['compositeChild']=True
        child['compositeOwner']=instance['name']
        prepared.append(child)

    children=namespace_children(prepared,instance['name'])
    expanded=list(children)
    if depth<max_depth:
        for child in children:
            if child['sourceType'] in RENDER_TYPES: continue
            expanded.extend(expand_instance(child,bases,sources,texts,depth+1,max_depth))
    return expanded


def main() -> None:
    parser=argparse.ArgumentParser()
    parser.add_argument('--spec',type=Path,required=True)
    parser.add_argument('--zircon-root',type=Path,required=True)
    parser.add_argument('--max-depth',type=int,default=2)
    args=parser.parse_args()

    spec=json.loads(args.spec.read_text(encoding='utf-8'))
    bases,sources,texts=build_class_index(args.zircon_root)
    total=0; by_tab={}; runtime_only=[]

    quest=next((w for w in spec.get('windows',[]) if w.get('field')=='QuestBox'),None)
    if quest:
        additions=[]
        for tab in [c for c in quest.get('controls',[]) if c.get('customTab') and c.get('sourceType')]:
            children=expand_instance(tab,bases,sources,texts,1,args.max_depth)
            by_tab[tab['name']]=len(children)
            if not children:
                runtime_only.append(tab['name'])
                tab['compositeRuntimeOnly']=True
            additions.extend(children)
        quest['controls'].extend(additions)
        quest['compositeExpansion']={
            'sourceBacked':True,
            'scope':'constructor-defined Quest custom tab children only',
            'maxDepth':args.max_depth,
            'childrenByTab':by_tab,
            'runtimeOnlyTabs':runtime_only,
            'runtimeRowsInvented':False,
        }
        add_asset_refs(spec,additions)
        total=len(additions)

    spec['compositePass']={
        'sourceBacked':True,
        'questChildrenAdded':total,
        'childrenByTab':by_tab,
        'questRuntimeOnlyTabs':runtime_only,
        'runtimeRowsInvented':False,
    }
    args.spec.write_text(json.dumps(spec,indent=2,ensure_ascii=False),encoding='utf-8')
    print('Quest composite children added:',total)
    print('Quest children by tab:',by_tab)
    print('Quest runtime-only tabs:',runtime_only)


if __name__=='__main__':
    main()
