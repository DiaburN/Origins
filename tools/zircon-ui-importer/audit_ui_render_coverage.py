#!/usr/bin/env python3
"""Audit render/skin/animation coverage across reconstructed Zircon desktop UI.

The pass runs before artwork extraction and promotes every source-required indexed
asset into `assetRefs`: normal images, indexed button hover/pressed states and
all deterministic DXAnimatedControl frame ranges. Symbolic animation constants
such as HorseTame `LoopBaseIndex` / `AngleCount` are resolved from the actual
Zircon class source; the original expressions remain as provenance.
"""
from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

from augment_ui_symbols import parse_class_symbols, substitute_symbols

GAME_RENDER_TYPES={
    'DXAnimatedControl','DXButton','DXCheckBox','DXColourControl','DXComboBox','DXConfigTab','DXControl',
    'DXImageControl','DXItemCell','DXItemGrid','DXKeyBindWindow','DXLabel','DXListBox','DXListBoxItem','DXNumberBox',
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
STATE_PROPERTIES=('HoverIndex','PressedIndex')


def literal_index(raw) -> int|None:
    value=str(raw or '').strip()
    return int(value) if re.fullmatch(r'-?\d+',value) else None

def library(raw) -> str|None:
    match=LIB_RE.search(str(raw or ''))
    return match.group(1) if match else None

def button_type(raw) -> str:
    match=BUTTON_RE.search(str(raw or ''))
    return match.group(1) if match else 'Default'

def bool_value(raw, fallback=True) -> bool:
    value=str(raw if raw is not None else '').strip().lower()
    if value=='true': return True
    if value=='false': return False
    return fallback

def safe_int(expression: str) -> int|None:
    value=str(expression).strip()
    if not re.fullmatch(r'[0-9+\-*/().\s]+',value): return None
    try:
        result=eval(value,{'__builtins__':{}},{})
        if isinstance(result,(int,float)) and float(result).is_integer(): return int(result)
    except Exception: pass
    return None


def owner_symbols(owner: dict, repo_root: Path) -> dict[str,str]:
    source_path=owner.get('sourcePath')
    if not source_path: return {}
    path=repo_root/'.source/Zircon'/source_path
    if not path.exists(): return {}
    return parse_class_symbols(path.read_text(encoding='utf-8-sig'))

def resolve_int(raw, symbols: dict[str,str]) -> int|None:
    direct=literal_index(raw)
    if direct is not None: return direct
    if raw is None: return None
    resolved=substitute_symbols(str(raw),symbols)
    return safe_int(resolved)


def indexed_controls(owners: list[dict]) -> list[dict]:
    rows=[]
    for owner in owners:
        for control in owner.get('controls',[]):
            p=control.get('properties',{});lib=library(p.get('LibraryFile'));idx=literal_index(p.get('Index'))
            if lib is None or idx is None or idx<0: continue
            rows.append({'window':owner.get('field'),'control':control.get('name'),'type':control.get('type'),'library':lib,'index':idx})
    return rows


def promote_button_state_assets(spec: dict, owners: list[dict], scope: str) -> tuple[list[dict],list[dict]]:
    refs=spec.setdefault('assetRefs',{});controls=[];added=[]
    for owner in owners:
        for control in owner.get('controls',[]):
            if control.get('type')!='DXButton': continue
            p=control.get('properties',{});lib=library(p.get('LibraryFile'));normal=literal_index(p.get('Index'))
            if not lib or normal is None or normal<0: continue
            states={'normal':normal}
            for prop in STATE_PROPERTIES:
                value=literal_index(p.get(prop))
                if value is not None and value>=0:
                    states['hover' if prop=='HoverIndex' else 'pressed']=value
                    bucket={int(v) for v in refs.get(lib,[])}
                    if value not in bucket:
                        bucket.add(value);refs[lib]=sorted(bucket)
                        added.append({'scope':scope,'window':owner.get('field'),'control':control.get('name'),'library':lib,'property':prop,'index':value})
            if len(states)>1: controls.append({'scope':scope,'window':owner.get('field'),'control':control.get('name'),'library':lib,'states':states})
    return controls,added


def promote_animation_assets(spec: dict, owners: list[dict], scope: str, repo_root: Path) -> tuple[list[dict],list[dict]]:
    refs=spec.setdefault('assetRefs',{});rows=[];added=[]
    for owner in owners:
        symbols=owner_symbols(owner,repo_root)
        for control in owner.get('controls',[]):
            if control.get('type')!='DXAnimatedControl': continue
            p=control.get('properties',{});lib=library(p.get('LibraryFile'))
            frame_count=resolve_int(p.get('FrameCount'),symbols)
            source_base=p.get('BaseIndex');base=resolve_int(source_base,symbols)
            index=resolve_int(p.get('Index'),symbols)
            # DXAnimatedControl only advances from BaseIndex. A literal Index with
            # no BaseIndex is retained as an index-driven source state (Timer egg).
            automatic=base is not None and base>=0 and frame_count is not None and frame_count>0
            extraction_base=base if automatic else index
            if source_base is not None and base is not None and literal_index(source_base) is None:
                control.setdefault('sourceBaseIndexExpression',source_base);p['BaseIndex']=str(base)
            if p.get('FrameCount') is not None and frame_count is not None and literal_index(p.get('FrameCount')) is None:
                control.setdefault('sourceFrameCountExpression',p['FrameCount']);p['FrameCount']=str(frame_count)
            detail={
                'scope':scope,'window':owner.get('field'),'control':control.get('name'),'library':lib,
                'baseIndex':base,'index':index,'frameCount':frame_count,
                'animationDelay':p.get('AnimationDelay'),'loop':bool_value(p.get('Loop'),True),
                'animated':bool_value(p.get('Animated'),True),'automaticBaseIndexAnimation':automatic,
                'indexDrivenWithoutBaseIndex':not automatic and index is not None and frame_count not in (None,0),
            }
            rows.append(detail)
            if not lib or extraction_base is None or extraction_base<0 or frame_count is None or frame_count<=0: continue
            bucket={int(v) for v in refs.get(lib,[])}
            for frame in range(extraction_base,extraction_base+frame_count):
                if frame not in bucket:
                    bucket.add(frame);added.append({'scope':scope,'window':owner.get('field'),'control':control.get('name'),'library':lib,'index':frame})
            refs[lib]=sorted(bucket)
            detail['extractionRange']=[extraction_base,extraction_base+frame_count-1]
    return rows,added


def apply(spec: dict, repo_root: Path) -> dict:
    game=spec.get('windows',[]);nested=spec.get('nestedWindows',[])
    game_types=Counter(c.get('type') for w in game for c in w.get('controls',[]));nested_types=Counter(c.get('type') for w in nested for c in w.get('controls',[]));issues=[]

    game_state,game_state_added=promote_button_state_assets(spec,game,'game');nested_state,nested_state_added=promote_button_state_assets(spec,nested,'nested')
    state_controls=game_state+nested_state;state_assets_added=game_state_added+nested_state_added
    game_anims,game_anim_added=promote_animation_assets(spec,game,'game',repo_root);nested_anims,nested_anim_added=promote_animation_assets(spec,nested,'nested',repo_root)
    animations=game_anims+nested_anims;animation_assets_added=game_anim_added+nested_anim_added

    missing_game=sorted(set(game_types)-GAME_RENDER_TYPES);missing_nested=sorted(set(nested_types)-NESTED_RENDER_TYPES)
    if missing_game: issues.append({'kind':'UNMAPPED_GAME_TYPES','values':missing_game})
    if missing_nested: issues.append({'kind':'UNMAPPED_NESTED_TYPES','values':missing_nested})

    button_counts=Counter();unsupported_buttons=[]
    for scope,owners in [('game',game),('nested',nested)]:
        for owner in owners:
            for control in owner.get('controls',[]):
                if control.get('type')!='DXButton': continue
                p=control.get('properties',{});idx=literal_index(p.get('Index'));lib=library(p.get('LibraryFile'))
                if lib and idx is not None and idx>=0: button_counts[(scope,'INDEXED')]+=1;continue
                kind=button_type(p.get('ButtonType'));button_counts[(scope,kind)]+=1
                if kind not in GENERATED_BUTTON_TYPES: unsupported_buttons.append({'scope':scope,'window':owner.get('field'),'control':control.get('name'),'ButtonType':kind})
    if unsupported_buttons: issues.append({'kind':'UNSUPPORTED_BUTTON_TYPES','values':unsupported_buttons})

    all_indexed={'game':indexed_controls(game),'nested':indexed_controls(nested)};indexed_wrong=[];asset_ref_missing=[]
    refs={name:{int(v) for v in values} for name,values in spec.get('assetRefs',{}).items()}
    for scope,items in all_indexed.items():
        for row in items:
            if row['type'] not in INDEXED_RENDER_TYPES: indexed_wrong.append({'scope':scope,**row})
            if row['index'] not in refs.get(row['library'],set()): asset_ref_missing.append({'scope':scope,**row})
    for row in state_controls:
        for state,index in row['states'].items():
            if index not in refs.get(row['library'],set()): asset_ref_missing.append({'scope':row['scope'],'window':row['window'],'control':row['control'],'type':'DXButton','library':row['library'],'index':index,'state':state})
    for row in animations:
        if not row.get('extractionRange') or not row.get('library'): continue
        for index in range(row['extractionRange'][0],row['extractionRange'][1]+1):
            if index not in refs.get(row['library'],set()): asset_ref_missing.append({'scope':row['scope'],'window':row['window'],'control':row['control'],'type':'DXAnimatedControl','library':row['library'],'index':index,'state':'animation-frame'})
    if indexed_wrong: issues.append({'kind':'INDEXED_CONTROL_NOT_IMAGE_RENDERED','values':indexed_wrong})
    if asset_ref_missing: issues.append({'kind':'INDEXED_ASSET_NOT_EXTRACTED','values':asset_ref_missing})

    new_character=[row for row in all_indexed['nested'] if row['window']=='NewCharacterDialog' and row['type']=='DXButton']
    if len(new_character)!=6 or any(row['library']!='Interface1c' for row in new_character): issues.append({'kind':'NEW_CHARACTER_INDEXED_BUTTON_CONTRACT_CHANGED','values':new_character})
    reroll=next((row for row in state_controls if row['window']=='LootBoxBox' and row['control']=='RerollButton'),None);expected_reroll={'normal':2926,'hover':2927,'pressed':2925}
    if not reroll or reroll.get('library')!='GameInter2' or reroll.get('states')!=expected_reroll: issues.append({'kind':'LOOTBOX_REROLL_STATE_CONTRACT_CHANGED','values':[reroll,expected_reroll]})

    # Current Suprcode/Zircon source contract. Keep this locked to source names and
    # values so upstream animation changes fail loudly instead of being silently
    # rendered with stale frame ranges.
    if len(animations)!=17: issues.append({'kind':'ANIMATED_CONTROL_COUNT_CHANGED','values':len(animations)})
    horse=next((row for row in animations if row['window']=='HorseTameBox' and row['control']=='LassoAnimation'),None)
    if (
        not horse
        or horse.get('baseIndex')!=7600
        or horse.get('frameCount')!=10
        or horse.get('loop') is not True
        or horse.get('animated') is not False
    ):
        issues.append({'kind':'HORSE_TAME_ANIMATION_CONTRACT_CHANGED','values':horse})

    egg=next((row for row in animations if row['window']=='TimerBox' and row['control']=='_eggTimer'),None)
    if (
        not egg
        or not egg.get('indexDrivenWithoutBaseIndex')
        or egg.get('index')!=960
        or egg.get('frameCount')!=6
        or egg.get('loop') is not False
        or egg.get('animated') is not True
    ):
        issues.append({'kind':'TIMER_EGG_ANIMATION_CONTRACT_CHANGED','values':egg})

    nested_runtime=repo_root/'apps/zircon-ui-reference/nested-variant-runtime.js';nested_text=nested_runtime.read_text(encoding='utf-8') if nested_runtime.exists() else ''
    missing_markers=[marker for marker in ['applyIndexedSourceArtwork','nested-source-indexed-control','sourceAsset(library,index)'] if marker not in nested_text]
    if missing_markers: issues.append({'kind':'NESTED_INDEXED_ART_RUNTIME_MISSING','values':missing_markers})

    # DXListBoxItem is source-created in current GameScene constructors, but the
    # corresponding DXComboBox.ListBox starts closed. The official build bundles
    # a neutral runtime that preserves the source control identity while removing
    # the generic UNMAPPED diagnostic and keeping the row hidden until list state
    # is implemented from source. Treating it as a mapped type is valid only while
    # this runtime and explicit policy remain present.
    listbox_runtime=repo_root/'apps/zircon-ui-reference/extra-runtimes/listbox-item-fidelity-runtime.js'
    listbox_text=listbox_runtime.read_text(encoding='utf-8') if listbox_runtime.exists() else ''
    listbox_markers=['data-control-type="DXListBoxItem"','dx-listbox-item-deferred','sourceInitialVisibility','runtimePayloadInvented']
    listbox_missing=[marker for marker in listbox_markers if marker not in listbox_text]
    if game_types.get('DXListBoxItem',0)>0 and listbox_missing:
        issues.append({'kind':'DXLISTBOXITEM_RUNTIME_MAPPING_MISSING','values':listbox_missing})
    policy_path=repo_root/'apps/zircon-ui-reference/control-render-policy.json'
    try:
        policy=json.loads(policy_path.read_text(encoding='utf-8')) if policy_path.exists() else {}
    except Exception as error:
        policy={};issues.append({'kind':'CONTROL_RENDER_POLICY_INVALID','values':[str(error)]})
    item_policy=(policy.get('policies') or {}).get('DXListBoxItem') or {}
    if game_types.get('DXListBoxItem',0)>0 and item_policy.get('mode')!='source-row-deferred':
        issues.append({'kind':'DXLISTBOXITEM_RENDER_POLICY_MISSING','values':[item_policy]})

    report={
        'sourceBacked':True,'gameControlTypes':dict(sorted(game_types.items())),'nestedControlTypes':dict(sorted(nested_types.items())),
        'gameTypeCoverage':f'{len(game_types)}/{len(game_types)}' if not missing_game else f'{len(game_types)-len(missing_game)}/{len(game_types)}',
        'nestedTypeCoverage':f'{len(nested_types)}/{len(nested_types)}' if not missing_nested else f'{len(nested_types)-len(missing_nested)}/{len(nested_types)}',
        'buttonSkinCounts':{f'{scope}:{kind}':count for (scope,kind),count in sorted(button_counts.items())},
        'indexedGameControls':len(all_indexed['game']),'indexedNestedControls':len(all_indexed['nested']),
        'indexedButtonStateControls':len(state_controls),'indexedButtonStateDetails':state_controls,'stateAssetRefsAdded':len(state_assets_added),'stateAssetRefsAddedDetails':state_assets_added,
        'animatedControls':len(animations),'animationDetails':animations,'animationFrameRefsAdded':len(animation_assets_added),'animationFrameRefsAddedDetails':animation_assets_added,
        'animationTimingPolicy':'DXAnimatedControl: frameDelay = AnimationDelay / FrameCount; Loop=false freezes BaseIndex+FrameCount-1',
        'newCharacterIndexedButtons':len(new_character),'lootBoxRerollStates':reroll,
        'dxListBoxItemGameControls':game_types.get('DXListBoxItem',0),'dxListBoxItemRenderer':'extra-runtimes/listbox-item-fidelity-runtime.js','dxListBoxItemInitialState':'deferred closed combo rows','dxListBoxItemRuntimePayloadsInvented':False,
        'issues':issues,'issueCount':len(issues),'genericIndexedArtworkInvented':False,
    }
    spec['renderCoverageAudit']=report
    return report

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--spec',type=Path,required=True);p.add_argument('--repo-root',type=Path,default=Path('.'));args=p.parse_args()
    spec=json.loads(args.spec.read_text(encoding='utf-8'));report=apply(spec,args.repo_root);args.spec.write_text(json.dumps(spec,indent=2,ensure_ascii=False),encoding='utf-8')
    print('Game render type coverage:',report['gameTypeCoverage']);print('Nested render type coverage:',report['nestedTypeCoverage'])
    print('Indexed button state controls:',report['indexedButtonStateControls']);print('State asset refs added:',report['stateAssetRefsAdded'])
    print('Animated controls:',report['animatedControls']);print('Animation frame refs added:',report['animationFrameRefsAdded'])
    print('DXListBoxItem GameScene controls:',report['dxListBoxItemGameControls'])
    print('Render audit issues:',report['issueCount'])
    if report['issues']:
        for issue in report['issues']: print(' ',issue['kind'],issue['values'][:10] if isinstance(issue['values'],list) else issue['values'])
        raise SystemExit(f"Zircon render coverage audit failed with {report['issueCount']} issue groups")
