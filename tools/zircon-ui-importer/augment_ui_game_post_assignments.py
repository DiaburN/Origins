#!/usr/bin/env python3
"""Correct GameScene constructor post-initializer assignments with C# temporal scope.

The first-generation flat parser enriched controls through a dictionary keyed by
local variable name. Zircon often reuses locals such as `label`, `button` and
`cell`; a dictionary therefore attached later `label.Location = ...` assignments
to the final label instead of the label alive at that source point.

This pass reparses only the original constructor controls, restores initializer
values for properties the flat parser may have enriched, and then applies
constructor top-level assignments to the latest matching initializer exactly as
C# executes them. Composite/synthetic controls appended by later passes are left
untouched.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict, deque
from pathlib import Path

from build_ui_source_spec import constructor_body, match_brace, split_top_level, strip_leading_comments, top_level_statements

INIT_RE = re.compile(
    r"(?:(?:[A-Za-z_][A-Za-z0-9_<>]*\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*)"
    r"new\s+(DX[A-Za-z_][A-Za-z0-9_]*)\s*\{"
)
STATEMENT_INIT_RE = re.compile(
    r"^(?:(?:[A-Za-z_][A-Za-z0-9_<>]*\s+)?)([A-Za-z_][A-Za-z0-9_]*)\s*=\s*new\s+(DX[A-Za-z_][A-Za-z0-9_]*)\s*\{",
    re.S,
)
POST_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)\.([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.+)$", re.S)
# Properties which the old flat parser could have assigned to the wrong reused local.
RESETTABLE = {'Location','Size','Index','Visible','LibraryFile','Opacity','ButtonType','Checked'}
POST_PROPERTIES = RESETTABLE | {
    'Enabled','Text','Parent','BackColour','Border','DrawTexture','AutoSize','MaxValue','MinValue','Change','Value',
    'ReadOnly','FixedSize','KeepFocus','ForeColour','Outline','OutlineColour','GridSize','Slot','GridType','FixedBorder',
}


def normalise(value: object) -> str:
    return ' '.join(str(value).strip().split())


def parse_occurrences(body: str) -> list[dict]:
    out=[]
    for match in INIT_RE.finditer(body):
        name,ctype=match.groups(); opening=body.find('{',match.start())
        try: closing=match_brace(body,opening)
        except ValueError: continue
        props={}
        for entry in split_top_level(body[opening+1:closing],','):
            m=re.match(r"\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.+?)\s*$",entry,re.S)
            if m: props[m.group(1)]=normalise(m.group(2))
        out.append({'name':name,'type':ctype,'properties':props,'offset':match.start()})
    return out


def eligible_base_controls(window: dict) -> list[dict]:
    # Original build_ui_source_spec controls do not carry any of these derived markers.
    result=[]
    for control in window.get('controls',[]):
        if control.get('customTab') or control.get('compositeChild') or control.get('syntheticSourceControl'):
            continue
        if control.get('sourceType') is not None:
            continue
        result.append(control)
    return result


def pair_occurrences(occurrences: list[dict], controls: list[dict]) -> list[tuple[dict,dict]]:
    queues: dict[tuple[str,str],deque] = defaultdict(deque)
    for control in controls:
        queues[(str(control.get('name')),str(control.get('type')))].append(control)
    pairs=[]
    for occ in occurrences:
        key=(occ['name'],occ['type'])
        if queues[key]: pairs.append((occ,queues[key].popleft()))
    return pairs


def replace_current_refs(expression: str, current: dict[str,dict]) -> str:
    value=str(expression)
    for source_name, control in sorted(current.items(),key=lambda row:len(row[0]),reverse=True):
        value=re.sub(rf"\b{re.escape(source_name)}\b",str(control.get('name')),value)
    return normalise(value)


def apply_window(window: dict, zircon_root: Path) -> dict:
    source_path=window.get('sourcePath'); class_name=window.get('class')
    if not source_path or not class_name: return {'paired':0,'assignments':0,'locationsAdded':0}
    path=zircon_root/source_path
    if not path.exists(): return {'paired':0,'assignments':0,'locationsAdded':0}
    text=path.read_text(encoding='utf-8-sig'); body=constructor_body(text,class_name)
    if not body: return {'paired':0,'assignments':0,'locationsAdded':0}

    occurrences=parse_occurrences(body); controls=eligible_base_controls(window); pairs=pair_occurrences(occurrences,controls)
    # Attach internal identity used only by this pass.
    occ_to_control={id(occ):control for occ,control in pairs}
    by_key: dict[tuple[str,str],deque]=defaultdict(deque)
    for occ,control in pairs: by_key[(occ['name'],occ['type'])].append((occ,control))

    # Restore initializer truth for properties the old name dictionary may have overwritten.
    for occ,control in pairs:
        props=control.setdefault('properties',{})
        for prop in RESETTABLE:
            if prop in occ['properties']:
                props[prop]=occ['properties'][prop]
            else:
                props.pop(prop,None)
        control['sourceInitializerOffset']=occ['offset']

    live_queues={key:deque(rows) for key,rows in by_key.items()}
    current: dict[str,dict]={}; assignments=0; locations_added=0
    for raw in top_level_statements(body):
        statement=normalise(strip_leading_comments(raw)).rstrip(';').strip()
        init=STATEMENT_INIT_RE.match(statement)
        if init:
            key=(init.group(1),init.group(2))
            if live_queues.get(key):
                _,control=live_queues[key].popleft(); current[init.group(1)]=control
            continue
        post=POST_RE.match(statement)
        if not post: continue
        name,prop,expression=post.groups()
        if prop not in POST_PROPERTIES or name not in current: continue
        control=current[name]; props=control.setdefault('properties',{}); before=props.get(prop)
        value=replace_current_refs(expression,current)
        if before is not None and normalise(before)!=value:
            control.setdefault('sourceInitializerBeforeTemporalPost',{})[prop]=before
        control.setdefault('sourceTemporalPostAssignments',{})[prop]=value
        if prop=='Location' and 'Location' not in props: locations_added+=1
        props[prop]=value; assignments+=1

    return {'paired':len(pairs),'assignments':assignments,'locationsAdded':locations_added,'occurrences':len(occurrences)}


def apply(spec: dict, zircon_root: Path) -> dict:
    totals={'windowsChanged':0,'paired':0,'assignments':0,'locationsAdded':0,'occurrences':0}
    by_window={}
    for window in spec.get('windows',[]):
        result=apply_window(window,zircon_root); by_window[window.get('field')]=result
        for key in ('paired','assignments','locationsAdded','occurrences'): totals[key]+=result.get(key,0)
        if result.get('assignments'): totals['windowsChanged']+=1
    report={
        'sourceBacked':True,
        'scope':'original GameScene constructor controls; temporal reused-local semantics',
        **totals,
        'byWindow':by_window,
        'compositeControlsUntouched':True,
        'runtimeEventAssignmentsIgnored':True,
    }
    spec['gameTemporalPostAssignments']=report
    return report


def main():
    p=argparse.ArgumentParser();p.add_argument('--spec',type=Path,required=True);p.add_argument('--zircon-root',type=Path,required=True);args=p.parse_args()
    spec=json.loads(args.spec.read_text(encoding='utf-8'));report=apply(spec,args.zircon_root)
    args.spec.write_text(json.dumps(spec,indent=2,ensure_ascii=False),encoding='utf-8')
    print('GameScene temporal post-assignment windows:',report['windowsChanged'])
    print('GameScene base controls paired:',report['paired'])
    print('GameScene temporal post assignments:',report['assignments'])
    print('GameScene Locations recovered:',report['locationsAdded'])

if __name__=='__main__': main()
