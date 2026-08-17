#!/usr/bin/env python3
"""Audit render/skin coverage across all reconstructed Zircon desktop UI.

This complements geometry QA. A control can be perfectly positioned and still be
visually wrong if the reference uses generic chrome where Zircon specifies an
indexed image or a different ButtonType.

The audit verifies:
- every GameScene and nested control type has an explicit renderer policy;
- all generated ButtonType values are supported by the reference skin map;
- literal LibraryFile + non-negative Index controls are image-capable types;
- every such indexed asset is present in assetRefs for extraction;
- the nested runtime contains the source-art enforcement used by indexed modal
  controls (notably NewCharacterDialog Interface1c class/gender buttons).
"""
from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from pathlib import Path

GAME_RENDER_TYPES={
    'DXAnimatedControl','DXButton','DXCheckBox','DXColourControl','DXComboBox','DXConfigTab','DXControl',
    'DXImageControl','DXItemCell','DXItemGrid','DXKeyBindWindow','DXLabel','DXListBox','DXNumberBox',
    'DXNumberTextBox','DXSoundBar','DXTab','DXTabControl','DXTextBox','DXTreeControl','DXVScrollBar',
}
NESTED_RENDER_TYPES={
    'DXButton','DXLabel','DXTextBox','DXNumberTextBox','DXNumberBox','DXVScrollBar','DXHScrollBar',
    'DXCheckBox','DXColourControl','DXComboBox','DXItemCell','DXControl','DXImageControl','DXAnimatedControl',
}
GENERATED_BUTTON_TYPES={'Default','SmallButton','AddButton','RemoveButton','LFGButton','OptionsButton'}
INDEXED_RENDER_TYPES={'DXImageControl','DXAnimatedControl','DXButton'}
LIB_RE=re.compile(r'LibraryFile\.([A-Za-z0-9_]+)')
BUTTON_RE=re.compile(r'ButtonType\.([A-Za-z0-9_]+)')


def literal_index(raw) -> int|None:
    value=str(raw or '').strip()
    return int(value) if re.fullmatch(r'-?\d+',value) else None

def library(raw) -> str|None:
    match=LIB_RE.search(str(raw or ''))
    return match.group(1) if match else None

def button_type(raw) -> str:
    match=BUTTON_RE.search(str(raw or ''))
    return match.group(1) if match else 'Default'


def indexed_controls(owners: list[dict]) -> list[dict]:
    rows=[]
    for owner in owners:
        for control in owner.get('controls',[]):
            p=control.get('properties',{});lib=library(p.get('LibraryFile'));idx=literal_index(p.get('Index'))
            if lib is None or idx is None or idx<0: continue
            rows.append({'window':owner.get('field'),'control':control.get('name'),'type':control.get('type'),'library':lib,'index':idx})
    return rows


def apply(spec: dict, repo_root: Path) -> dict:
    game=spec.get('windows',[]);nested=spec.get('nestedWindows',[])
    game_types=Counter(c.get('type') for w in game for c in w.get('controls',[]))
    nested_types=Counter(c.get('type') for w in nested for c in w.get('controls',[]))
    issues=[]

    missing_game=sorted(set(game_types)-GAME_RENDER_TYPES)
    missing_nested=sorted(set(nested_types)-NESTED_RENDER_TYPES)
    if missing_game: issues.append({'kind':'UNMAPPED_GAME_TYPES','values':missing_game})
    if missing_nested: issues.append({'kind':'UNMAPPED_NESTED_TYPES','values':missing_nested})

    button_counts=Counter(); unsupported_buttons=[]
    for scope,owners in [('game',game),('nested',nested)]:
        for owner in owners:
            for control in owner.get('controls',[]):
                if control.get('type')!='DXButton': continue
                p=control.get('properties',{});idx=literal_index(p.get('Index'));lib=library(p.get('LibraryFile'))
                if lib and idx is not None and idx>=0:
                    button_counts[(scope,'INDEXED')]+=1;continue
                kind=button_type(p.get('ButtonType'));button_counts[(scope,kind)]+=1
                if kind not in GENERATED_BUTTON_TYPES:
                    unsupported_buttons.append({'scope':scope,'window':owner.get('field'),'control':control.get('name'),'ButtonType':kind})
    if unsupported_buttons: issues.append({'kind':'UNSUPPORTED_BUTTON_TYPES','values':unsupported_buttons})

    all_indexed={'game':indexed_controls(game),'nested':indexed_controls(nested)}
    indexed_wrong=[];asset_ref_missing=[]
    refs={name:{int(v) for v in values} for name,values in spec.get('assetRefs',{}).items()}
    for scope,rows in all_indexed.items():
        for row in rows:
            if row['type'] not in INDEXED_RENDER_TYPES:
                indexed_wrong.append({'scope':scope,**row})
            if row['index'] not in refs.get(row['library'],set()):
                asset_ref_missing.append({'scope':scope,**row})
    if indexed_wrong: issues.append({'kind':'INDEXED_CONTROL_NOT_IMAGE_RENDERED','values':indexed_wrong})
    if asset_ref_missing: issues.append({'kind':'INDEXED_ASSET_NOT_EXTRACTED','values':asset_ref_missing})

    # Current source has six real Interface1c indexed buttons in NewCharacterDialog.
    new_character=[row for row in all_indexed['nested'] if row['window']=='NewCharacterDialog' and row['type']=='DXButton']
    if len(new_character)!=6 or any(row['library']!='Interface1c' for row in new_character):
        issues.append({'kind':'NEW_CHARACTER_INDEXED_BUTTON_CONTRACT_CHANGED','values':new_character})

    nested_runtime=repo_root/'apps/zircon-ui-reference/nested-variant-runtime.js'
    runtime_text=nested_runtime.read_text(encoding='utf-8') if nested_runtime.exists() else ''
    runtime_markers=['applyIndexedSourceArtwork','nested-source-indexed-control','sourceAsset(library,index)']
    missing_markers=[marker for marker in runtime_markers if marker not in runtime_text]
    if missing_markers: issues.append({'kind':'NESTED_INDEXED_ART_RUNTIME_MISSING','values':missing_markers})

    report={
        'sourceBacked':True,
        'gameControlTypes':dict(sorted(game_types.items())),
        'nestedControlTypes':dict(sorted(nested_types.items())),
        'gameTypeCoverage':f'{len(game_types)}/{len(game_types)}' if not missing_game else f'{len(game_types)-len(missing_game)}/{len(game_types)}',
        'nestedTypeCoverage':f'{len(nested_types)}/{len(nested_types)}' if not missing_nested else f'{len(nested_types)-len(missing_nested)}/{len(nested_types)}',
        'buttonSkinCounts':{f'{scope}:{kind}':count for (scope,kind),count in sorted(button_counts.items())},
        'indexedGameControls':len(all_indexed['game']),
        'indexedNestedControls':len(all_indexed['nested']),
        'newCharacterIndexedButtons':len(new_character),
        'issues':issues,
        'issueCount':len(issues),
        'genericIndexedArtworkInvented':False,
    }
    spec['renderCoverageAudit']=report
    return report

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--spec',type=Path,required=True);p.add_argument('--repo-root',type=Path,default=Path('.'));args=p.parse_args()
    spec=json.loads(args.spec.read_text(encoding='utf-8'));report=apply(spec,args.repo_root)
    args.spec.write_text(json.dumps(spec,indent=2,ensure_ascii=False),encoding='utf-8')
    print('Game render type coverage:',report['gameTypeCoverage'])
    print('Nested render type coverage:',report['nestedTypeCoverage'])
    print('Indexed GameScene controls:',report['indexedGameControls'])
    print('Indexed nested controls:',report['indexedNestedControls'])
    print('NewCharacter indexed source buttons:',report['newCharacterIndexedButtons'])
    print('Render audit issues:',report['issueCount'])
    if report['issues']:
        for issue in report['issues']: print(' ',issue['kind'],issue['values'][:10] if isinstance(issue['values'],list) else issue['values'])
        raise SystemExit(f"Zircon render coverage audit failed with {report['issueCount']} issue groups")
