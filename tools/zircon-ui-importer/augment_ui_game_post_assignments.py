#!/usr/bin/env python3
"""Correct GameScene constructor post-initializer assignments with C# temporal scope.

The first-generation flat parser enriched controls through a dictionary keyed by
local variable name. Zircon often reuses locals such as `label`, `button` and
`cell`; a dictionary therefore attached later assignments to the wrong object.

This pass reparses original constructor controls and executes deterministic local
symbol state in source order. Geometry assigned after an initializer is resolved
at the exact statement where Zircon executes it, including inline mutations such
as `y += rowSpacing`. C# preprocessor directives are removed before statement
matching because they are not executable tokens and must never hide locals such
as `int xOffset = 40` after a `#region` marker.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict, deque
from pathlib import Path

from build_ui_source_spec import constructor_body, match_brace, split_top_level, strip_leading_comments, top_level_statements
from augment_ui_symbols import parse_class_symbols, resolve_inline_geometry_side_effects, substitute_symbols, update_local_symbols

INIT_RE = re.compile(
    r"(?:(?:[A-Za-z_][A-Za-z0-9_<>]*\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*)"
    r"new\s+(DX[A-Za-z_][A-Za-z0-9_]*)\s*\{"
)
STATEMENT_INIT_RE = re.compile(
    r"^(?:(?:[A-Za-z_][A-Za-z0-9_<>]*\s+)?)([A-Za-z_][A-Za-z0-9_]*)\s*=\s*new\s+(DX[A-Za-z_][A-Za-z0-9_]*)\s*\{", re.S,
)
POST_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)\.([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.+)$", re.S)
PREPROCESSOR_RE = re.compile(r"(?m)^\s*#(?:region|endregion|if|elif|else|endif|define|undef|warning|error|line|pragma)\b[^\n\r]*")
RESETTABLE = {'Location','Size','Index','Visible','LibraryFile','Opacity','ButtonType','Checked'}
POST_PROPERTIES = RESETTABLE | {
    'Enabled','Text','Parent','BackColour','Border','DrawTexture','AutoSize','MaxValue','MinValue','Change','Value',
    'ReadOnly','FixedSize','KeepFocus','ForeColour','Outline','OutlineColour','GridSize','Slot','GridType','FixedBorder',
}
GEOMETRY_PROPERTIES={'Location','Size','GridSize'}


def normalise(value: object) -> str:
    return ' '.join(str(value).strip().split())


def clean_statement(raw: str) -> str:
    value=strip_leading_comments(raw)
    value=PREPROCESSOR_RE.sub('',value)
    return normalise(value).rstrip(';').strip()


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
    result=[]
    for control in window.get('controls',[]):
        if control.get('customTab') or control.get('compositeChild') or control.get('syntheticSourceControl'): continue
        if control.get('sourceType') is not None: continue
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


def resolve_post_value(prop: str, expression: str, symbols: dict[str,str], current: dict[str,dict]) -> str:
    expression=normalise(expression)
    if prop in GEOMETRY_PROPERTIES:
        value=resolve_inline_geometry_side_effects(expression,symbols)
    else:
        value=substitute_symbols(expression,symbols)
    return replace_current_refs(value,current)


def apply_window(window: dict, zircon_root: Path) -> dict:
    source_path=window.get('sourcePath'); class_name=window.get('class')
    if not source_path or not class_name: return {'paired':0,'assignments':0,'locationsAdded':0}
    path=zircon_root/source_path
    if not path.exists(): return {'paired':0,'assignments':0,'locationsAdded':0}
    text=path.read_text(encoding='utf-8-sig'); body=constructor_body(text,class_name)
    if not body: return {'paired':0,'assignments':0,'locationsAdded':0}

    occurrences=parse_occurrences(body); controls=eligible_base_controls(window); pairs=pair_occurrences(occurrences,controls)
    by_key: dict[tuple[str,str],deque]=defaultdict(deque)
    for occ,control in pairs: by_key[(occ['name'],occ['type'])].append((occ,control))

    for occ,control in pairs:
        props=control.setdefault('properties',{})
        for prop in RESETTABLE:
            if prop in occ['properties']: props[prop]=occ['properties'][prop]
            else: props.pop(prop,None)
        control['sourceInitializerOffset']=occ['offset']

    live_queues={key:deque(rows) for key,rows in by_key.items()}
    current: dict[str,dict]={}
    symbols=parse_class_symbols(text)
    assignments=0; locations_added=0; geometry_resolved=0

    for raw in top_level_statements(body):
        statement=clean_statement(raw)
        if not statement:
            continue
        init=STATEMENT_INIT_RE.match(statement)
        if init:
            key=(init.group(1),init.group(2))
            if live_queues.get(key):
                _,control=live_queues[key].popleft(); current[init.group(1)]=control
            continue

        post=POST_RE.match(statement)
        if post:
            name,prop,expression=post.groups()
            if prop in POST_PROPERTIES and name in current:
                control=current[name]; props=control.setdefault('properties',{}); before=props.get(prop)
                value=resolve_post_value(prop,expression,symbols,current)
                if before is not None and normalise(before)!=value:
                    control.setdefault('sourceInitializerBeforeTemporalPost',{})[prop]=before
                control.setdefault('sourceTemporalPostAssignments',{})[prop]=normalise(expression)
                control.setdefault('resolvedTemporalPostAssignments',{})[prop]=value
                if prop=='Location' and 'Location' not in props: locations_added+=1
                if prop in GEOMETRY_PROPERTIES and value!=normalise(expression): geometry_resolved+=1
                props[prop]=value; assignments+=1
                continue

        update_local_symbols(statement,symbols)

    return {
        'paired':len(pairs),'assignments':assignments,'locationsAdded':locations_added,
        'geometryResolvedAtExecution':geometry_resolved,'occurrences':len(occurrences)
    }


def apply(spec: dict, zircon_root: Path) -> dict:
    totals={'windowsChanged':0,'paired':0,'assignments':0,'locationsAdded':0,'geometryResolvedAtExecution':0,'occurrences':0}
    by_window={}
    for window in spec.get('windows',[]):
        result=apply_window(window,zircon_root); by_window[window.get('field')]=result
        for key in ('paired','assignments','locationsAdded','geometryResolvedAtExecution','occurrences'): totals[key]+=result.get(key,0)
        if result.get('assignments'): totals['windowsChanged']+=1
    report={
        'sourceBacked':True,
        'scope':'original GameScene constructor controls; temporal reused-local semantics with source-time symbol execution',
        **totals,
        'byWindow':by_window,
        'compositeControlsUntouched':True,
        'runtimeEventAssignmentsIgnored':True,
        'inlineCompoundAssignmentsExecuted':True,
        'preprocessorDirectivesIgnoredAsNonExecutable':True,
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
    print('GameScene post geometry resolved at execution:',report['geometryResolvedAtExecution'])

if __name__=='__main__': main()
