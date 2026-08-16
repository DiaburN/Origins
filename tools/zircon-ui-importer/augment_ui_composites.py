#!/usr/bin/env python3
"""Expand deterministic child controls of custom Zircon UI composites.

Quest custom DXTab constructors and Guild helper-built tabs are expanded into
source-backed, namespaced child controls. Runtime-created data rows/items are
never fabricated: controls are imported only when their source Parent chain
proves they belong to the tab being expanded.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

from build_ui_source_spec import (
    LIB_FILE,
    constructor_body,
    literal_indices,
    match_brace,
    named_method_body,
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


def prepare_controls(body: str, owner_name: str, source_text: str, bases: dict[str,str], sources: dict[str,Path], texts: dict[Path,str]) -> list[dict]:
    raw=parse_control_initializers(body,bases)
    snapshots=symbol_snapshots(body,parse_class_symbols(source_text),len(raw))
    prepared=[]
    for child,symbols in zip(raw,snapshots):
        defaults=component_defaults(child['sourceType'],sources,texts)
        merged=dict(defaults); merged.update(child['properties']); child['properties']=merged
        simplify_geometry(child,symbols)
        child['compositeChild']=True
        child['compositeOwner']=owner_name
        prepared.append(child)
    return prepared


def replace_known_names(expression: str, mapping: dict[str,str]) -> str:
    value=str(expression)
    for old in sorted(mapping,key=len,reverse=True):
        value=re.sub(rf'(?<!\.)\b{re.escape(old)}\b',mapping[old],value)
    return normalise(value)


def assign_names(children: list[dict], prefix: str) -> dict[str,list[tuple[int,str]]]:
    counts=Counter(child['sourceName'] for child in children)
    sequence=Counter()
    occurrences: dict[str,list[tuple[int,str]]] = defaultdict(list)
    for child in children:
        source_name=child['sourceName']; sequence[source_name]+=1
        suffix='' if counts[source_name]==1 else f'__{sequence[source_name]}'
        child['name']=f'{prefix}__{source_name}{suffix}'
        occurrences[source_name].append((int(child.get('sourceOffset',0)),child['name']))
    return occurrences


def scoped_mapping(occurrences: dict[str,list[tuple[int,str]]], offset: int, external: dict[str,str]|None=None) -> dict[str,str]:
    mapping=dict(external or {})
    for source_name,rows in occurrences.items():
        previous=[namespaced for source_offset,namespaced in rows if source_offset < offset]
        if previous:
            mapping[source_name]=previous[-1]
        elif len(rows)==1:
            mapping[source_name]=rows[0][1]
    return mapping


def namespace_children(children: list[dict], parent_name: str) -> list[dict]:
    """Namespace constructor children using C# temporal local-variable scope."""
    occurrences=assign_names(children,parent_name)
    for child in children:
        mapping=scoped_mapping(occurrences,int(child.get('sourceOffset',0)))
        props=child['properties']; parent=normalise(str(props.get('Parent','this')))
        if parent=='this':
            props['Parent']=parent_name
        elif parent in mapping:
            props['Parent']=mapping[parent]
        for key,value in list(props.items()):
            if key=='Parent': continue
            props[key]=replace_known_names(value,mapping)
        child['constructorAliasScopeResolved']=True
    return children


def namespace_helper_descendants(children: list[dict], root_source_name: str, root_instance_name: str) -> list[dict]:
    """Namespace a Guild helper and retain only proven descendants of its tab.

    In a helper method `this` is GuildDialog, not the tab, so unlike constructor
    expansion it remains the window root. The existing top-level tab instance is
    injected as an external alias. Any temporary controls without a Parent chain
    leading to that tab are discarded.
    """
    root_rows=[child for child in children if child['sourceName']==root_source_name and child['type']=='DXTab']
    root_offsets={id(child) for child in root_rows}
    candidates=[child for child in children if id(child) not in root_offsets]
    occurrences=assign_names(candidates,root_instance_name)
    external={root_source_name:root_instance_name}

    for child in candidates:
        mapping=scoped_mapping(occurrences,int(child.get('sourceOffset',0)),external)
        props=child['properties']; parent=normalise(str(props.get('Parent','this')))
        if parent in mapping:
            props['Parent']=mapping[parent]
        else:
            props['Parent']=parent
        for key,value in list(props.items()):
            if key=='Parent': continue
            props[key]=replace_known_names(value,mapping)
        child['constructorAliasScopeResolved']=True
        child['helperComposite']=True

    descendants={root_instance_name}
    changed=True
    while changed:
        changed=False
        for child in candidates:
            if child['name'] in descendants: continue
            if child.get('properties',{}).get('Parent') in descendants:
                descendants.add(child['name']); changed=True

    return [child for child in candidates if child['name'] in descendants]


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

    prepared=prepare_controls(body,instance['name'],text,bases,sources,texts)
    children=namespace_children(prepared,instance['name'])
    expanded=list(children)
    if depth<max_depth:
        for child in children:
            if child['sourceType'] in RENDER_TYPES: continue
            expanded.extend(expand_instance(child,bases,sources,texts,depth+1,max_depth))
    return expanded


def expand_guild_helper(tab: dict, guild_source: str, bases: dict[str,str], sources: dict[str,Path], texts: dict[Path,str]) -> list[dict]:
    marker=str(tab.get('customTabSource',''))
    if not marker.startswith('helper:'): return []
    helper=marker.split(':',1)[1]
    body=named_method_body(guild_source,helper)
    if not body: return []
    prepared=prepare_controls(body,tab['name'],guild_source,bases,sources,texts)
    return namespace_helper_descendants(prepared,tab['name'],tab['name'])


def main() -> None:
    parser=argparse.ArgumentParser()
    parser.add_argument('--spec',type=Path,required=True)
    parser.add_argument('--zircon-root',type=Path,required=True)
    parser.add_argument('--max-depth',type=int,default=2)
    args=parser.parse_args()

    spec=json.loads(args.spec.read_text(encoding='utf-8'))
    bases,sources,texts=build_class_index(args.zircon_root)

    quest_total=0; quest_by_tab={}; quest_runtime_only=[]
    quest=next((w for w in spec.get('windows',[]) if w.get('field')=='QuestBox'),None)
    if quest:
        additions=[]
        for tab in [c for c in quest.get('controls',[]) if c.get('customTab') and c.get('sourceType')]:
            children=expand_instance(tab,bases,sources,texts,1,args.max_depth)
            quest_by_tab[tab['name']]=len(children)
            if not children:
                quest_runtime_only.append(tab['name']); tab['compositeRuntimeOnly']=True
            additions.extend(children)
        quest['controls'].extend(additions)
        quest['compositeExpansion']={
            'sourceBacked':True,
            'scope':'constructor-defined Quest custom tab children only',
            'maxDepth':args.max_depth,
            'childrenByTab':quest_by_tab,
            'runtimeOnlyTabs':quest_runtime_only,
            'constructorAliasScope':'source-ordered latest assignment',
            'runtimeRowsInvented':False,
        }
        add_asset_refs(spec,additions); quest_total=len(additions)

    guild_total=0; guild_by_tab={}; guild_runtime_only=[]
    guild=next((w for w in spec.get('windows',[]) if w.get('field')=='GuildBox'),None)
    if guild and guild.get('sourcePath'):
        guild_source=(args.zircon_root/guild['sourcePath']).read_text(encoding='utf-8-sig')
        additions=[]
        tabs=[c for c in guild.get('controls',[]) if c.get('customTab') and str(c.get('customTabSource','')).startswith('helper:')]
        for tab in tabs:
            children=expand_guild_helper(tab,guild_source,bases,sources,texts)
            guild_by_tab[tab['name']]=len(children)
            if not children:
                guild_runtime_only.append(tab['name']); tab['compositeRuntimeOnly']=True
            additions.extend(children)
        guild['controls'].extend(additions)
        guild['compositeExpansion']={
            'sourceBacked':True,
            'scope':'Guild Create*Tab helper controls whose Parent chain reaches the tab',
            'childrenByTab':guild_by_tab,
            'runtimeOnlyTabs':guild_runtime_only,
            'constructorAliasScope':'source-ordered latest assignment',
            'runtimeRowsInvented':False,
        }
        add_asset_refs(spec,additions); guild_total=len(additions)

    spec['compositePass']={
        'sourceBacked':True,
        'questChildrenAdded':quest_total,
        'questChildrenByTab':quest_by_tab,
        'questRuntimeOnlyTabs':quest_runtime_only,
        'guildChildrenAdded':guild_total,
        'guildChildrenByTab':guild_by_tab,
        'guildRuntimeOnlyTabs':guild_runtime_only,
        'constructorAliasScope':'source-ordered latest assignment',
        'runtimeRowsInvented':False,
    }
    args.spec.write_text(json.dumps(spec,indent=2,ensure_ascii=False),encoding='utf-8')
    print('Quest composite children added:',quest_total)
    print('Quest children by tab:',quest_by_tab)
    print('Quest runtime-only tabs:',quest_runtime_only)
    print('Guild composite children added:',guild_total)
    print('Guild children by tab:',guild_by_tab)
    print('Guild runtime-only tabs:',guild_runtime_only)
    print('Constructor alias scope: source-ordered latest assignment')


if __name__=='__main__':
    main()
