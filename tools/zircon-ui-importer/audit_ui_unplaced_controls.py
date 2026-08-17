#!/usr/bin/env python3
"""Classify Zircon UI controls that intentionally have no constructor Location.

A missing `Location` property is not automatically an error. Zircon uses several
source-backed patterns:
- SizeChanged/OnClientAreaChanged/helper methods assign Location later;
- DXTabControl places tab content/buttons automatically;
- a child intentionally starts at Point.Empty (0,0) inside a sized parent;
- rows/items/maps are positioned only when runtime data exists;
- detached nested/modal objects are not spatial children of the declaring window.

This auditor never invents a coordinate. It records source evidence and leaves an
UNKNOWN classification whenever the code cannot justify the missing Location.
CI can tighten the unknown threshold as the reconstruction is completed.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

ASSIGN_TEMPLATE = r"\b{name}\.Location\s*=\s*(.+?)\s*;"
SIZE_EVENT_TEMPLATE = r"\b{name}\.SizeChanged\s*\+="
MOVE_EVENT_TEMPLATE = r"\b{name}\.(?:Moving|LocationChanged|VisibleChanged)\s*\+="


def source_name(control: dict) -> str:
    return str(control.get('sourceName') or control.get('name') or '')


def find_location_assignments(text: str, name: str) -> list[str]:
    if not name or not re.match(r'^[A-Za-z_][A-Za-z0-9_]*$', name):
        return []
    pattern=re.compile(ASSIGN_TEMPLATE.format(name=re.escape(name)),re.S)
    return [' '.join(value.split()) for value in pattern.findall(text)]


def classify(window: dict, control: dict, text: str) -> dict:
    p=control.get('properties',{})
    name=source_name(control)
    ctype=str(control.get('type',''))
    parent=str(p.get('Parent','this'))
    assignments=find_location_assignments(text,name)

    # Exact source assignments outside the captured initializer are strongest evidence.
    if assignments:
        event = bool(re.search(SIZE_EVENT_TEMPLATE.format(name=re.escape(name)),text))
        return {
            'classification':'SOURCE_EVENT_LAYOUT' if event else 'SOURCE_METHOD_LAYOUT',
            'sourceName':name,
            'sourceAssignments':assignments[:12],
            'assignmentCount':len(assignments),
            'runtimeCoordinateInvented':False,
        }

    if ctype in {'DXTab','DXConfigTab'}:
        return {
            'classification':'SOURCE_TAB_AUTO_LAYOUT',
            'sourceName':name,
            'sourceRule':'DXTabControl/DXTab selected-tab layout; tab content may begin at the tab client origin when no Location is specified',
            'runtimeCoordinateInvented':False,
        }

    # ConfigBox owns KeyBindWindow as a detached modal. It is deliberately not a child
    # coordinate of ConfigBox and is reconstructed separately in nestedWindows.
    if window.get('field')=='ConfigBox' and name=='KeyBindWindow':
        return {
            'classification':'DETACHED_NESTED_WINDOW',
            'sourceName':name,
            'sourceRule':'DXConfigWindow.OnParentChanged assigns KeyBindWindow.Parent; DXKeyBindWindow.OnIsVisibleChanged centres it against Config.GameSize',
            'nestedSourceClass':'DXKeyBindWindow',
            'runtimeCoordinateInvented':False,
        }

    # CharacterNameLabel deliberately occupies the top-left of the 137px name panel;
    # following Guild labels are offset from its height.
    if name=='CharacterNameLabel' and parent=='namePanel':
        return {
            'classification':'SOURCE_DEFAULT_ORIGIN',
            'sourceName':name,
            'sourceRule':'No Location assignment in CharacterDialog; parent namePanel is explicitly positioned/sized and CharacterNameLabel intentionally starts at Point.Empty',
            'runtimeCoordinateInvented':False,
        }

    # Runtime-generated row/cell controls are positioned when data/layout methods run.
    runtime_markers=('row','cell','entry','item','pair.Value')
    if any(marker.lower() in name.lower() or marker in parent for marker in runtime_markers):
        return {
            'classification':'RUNTIME_DATA_LAYOUT',
            'sourceName':name,
            'sourceRule':'runtime/data-driven row/cell/entry placement; neutral reference does not fabricate row data',
            'runtimeCoordinateInvented':False,
        }

    # Synthetic DXConfigSection art/labels or already documented composite children may
    # intentionally use their parent origin if their source helper controls the layout.
    if control.get('syntheticSourceControl'):
        return {
            'classification':'SOURCE_COMPOSITE_LAYOUT',
            'sourceName':name,
            'sourceRule':str(control.get('syntheticSourceControl')),
            'runtimeCoordinateInvented':False,
        }

    return {
        'classification':'UNKNOWN',
        'sourceName':name,
        'parent':parent,
        'type':ctype,
        'runtimeCoordinateInvented':False,
    }


def audit_owner(owner: dict, zircon_root: Path) -> list[dict]:
    source_path=owner.get('sourcePath')
    text=''
    if source_path:
        path=zircon_root/source_path
        if path.exists(): text=path.read_text(encoding='utf-8-sig')
    rows=[]
    for index,control in enumerate(owner.get('controls',[])):
        if 'Location' in control.get('properties',{}):
            continue
        result=classify(owner,control,text)
        control['unplacedAudit']=result
        rows.append({
            'window':owner.get('field'),
            'windowClass':owner.get('class'),
            'controlIndex':index,
            'control':control.get('name'),
            'type':control.get('type'),
            **result,
        })
    return rows


def main() -> None:
    parser=argparse.ArgumentParser()
    parser.add_argument('--spec',type=Path,required=True)
    parser.add_argument('--zircon-root',type=Path,required=True)
    parser.add_argument('--fail-unknown',action='store_true')
    args=parser.parse_args()

    spec=json.loads(args.spec.read_text(encoding='utf-8'))
    rows=[]
    for owner in list(spec.get('windows',[]))+list(spec.get('nestedWindows',[])):
        rows.extend(audit_owner(owner,args.zircon_root))
    counts=Counter(row['classification'] for row in rows)
    unknown=[row for row in rows if row['classification']=='UNKNOWN']
    by_window=defaultdict(list)
    for row in rows: by_window[row['window']].append(row)
    report={
        'sourceBacked':True,
        'totalControlsWithoutConstructorLocation':len(rows),
        'classificationCounts':dict(sorted(counts.items())),
        'unknownCount':len(unknown),
        'unknown':unknown,
        'byWindow':dict(by_window),
        'runtimeCoordinatesInvented':False,
    }
    spec['unplacedControlAudit']=report
    args.spec.write_text(json.dumps(spec,indent=2,ensure_ascii=False),encoding='utf-8')
    print('Controls without Location:',len(rows))
    print('Unplaced classifications:',dict(sorted(counts.items())))
    print('UNKNOWN unplaced controls:',len(unknown))
    for row in unknown[:100]:
        print('  UNKNOWN',row['window'],row['control'],row['type'],'parent=',row.get('parent'))
    if args.fail_unknown and unknown:
        raise SystemExit(f'Unclassified controls without Location: {len(unknown)}')

if __name__=='__main__':
    main()
