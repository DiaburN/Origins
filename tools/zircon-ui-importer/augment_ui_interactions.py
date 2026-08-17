#!/usr/bin/env python3
"""Extract source-backed interactions and run final placement/render audits."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from audit_ui_render_coverage import apply as audit_render_coverage
from audit_ui_unplaced_controls import apply as audit_unplaced_controls

CLICK_EXPR_RE = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)\.MouseClick\s*\+=\s*\([^)]*\)\s*=>\s*([^;{]+);",re.S)
CLICK_BLOCK_RE = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)\.MouseClick\s*\+=\s*\([^)]*\)\s*=>\s*\{(.*?)\};",re.S)
VISIBLE_RE = re.compile(r"^GameScene\.Game\.([A-Za-z_][A-Za-z0-9_]*)\.Visible\s*=\s*(.+)$",re.S)
TOGGLE_OPEN_RE = re.compile(r"^GameScene\.Game\.([A-Za-z_][A-Za-z0-9_]*)\.ToggleOpen\s*\(\s*(.+)\s*\)$",re.S)
VISIBLE_ASSIGN_RE = re.compile(r"\bGameScene\.Game\.([A-Za-z_][A-Za-z0-9_]*)\.Visible\s*=\s*([^;]+);",re.S)
TOGGLE_OPEN_ASSIGN_RE = re.compile(r"\bGameScene\.Game\.([A-Za-z_][A-Za-z0-9_]*)\.ToggleOpen\s*\(\s*([^;]+?)\s*\)\s*;",re.S)
MIN_GAME_EXPLICIT_LOCATIONS=1389
MIN_NESTED_EXPLICIT_LOCATIONS=78


def normalise(value: str) -> str: return " ".join(value.strip().split())
def classify_visible(target: str, rhs: str) -> str | None:
    value=normalise(rhs)
    if value=="true": return "open"
    if value=="false": return "close"
    if value==f"!GameScene.Game.{target}.Visible": return "toggle"
    return None
def classify_toggle_open(target: str, argument: str) -> str | None:
    value=normalise(argument)
    if value=="true": return "open"
    if value=="false": return "close"
    if value==f"!GameScene.Game.{target}.Visible": return "toggle"
    return None

def make_interaction(window: dict, control: str, target: str, action: str, expression: str) -> dict:
    return {
        "sourceField":window["field"],"sourceClass":window.get("class"),"control":control,
        "event":"MouseClick","action":action,"targetField":target,"sourceExpression":normalise(expression),
    }
def classify_expression(window: dict, control: str, expression: str, known_fields: set[str]) -> list[dict]:
    expression=normalise(expression);out=[]
    visible=VISIBLE_RE.match(expression)
    if visible:
        target,rhs=visible.groups()
        if target in known_fields:
            action=classify_visible(target,rhs)
            if action: out.append(make_interaction(window,control,target,action,expression))
        return out
    toggle=TOGGLE_OPEN_RE.match(expression)
    if toggle:
        target,argument=toggle.groups()
        if target in known_fields:
            action=classify_toggle_open(target,argument)
            if action: out.append(make_interaction(window,control,target,action,expression))
    return out

def matching_brace(text: str, opening: int) -> int:
    depth=0;in_string=False;in_char=False;escaped=False;line_comment=False;block_comment=False;i=opening
    while i<len(text):
        c=text[i];n=text[i+1] if i+1<len(text) else ''
        if line_comment:
            if c=='\n': line_comment=False
            i+=1;continue
        if block_comment:
            if c=='*' and n=='/': block_comment=False;i+=2;continue
            i+=1;continue
        if in_char:
            if escaped: escaped=False
            elif c=='\\': escaped=True
            elif c=="'": in_char=False
            i+=1;continue
        if in_string:
            if escaped: escaped=False
            elif c=='\\': escaped=True
            elif c=='"': in_string=False
            i+=1;continue
        if c=='/' and n=='/': line_comment=True;i+=2;continue
        if c=='/' and n=='*': block_comment=True;i+=2;continue
        if c=='"': in_string=True;i+=1;continue
        if c=="'": in_char=True;i+=1;continue
        if c=='{': depth+=1
        elif c=='}':
            depth-=1
            if depth==0:return i
        i+=1
    raise ValueError('unbalanced C# class body')

def exact_class_body(source: str, class_name: str) -> str:
    match=re.search(rf"\bclass\s+{re.escape(class_name)}\b[^{{]*\{{",source)
    if not match:return ''
    opening=source.find('{',match.start())
    return source[opening+1:matching_brace(source,opening)]

def extract_window_interactions(window: dict, source: str, known_fields: set[str]) -> list[dict]:
    out=[];control_names={control.get("name") for control in window.get("controls", [])}
    for match in CLICK_EXPR_RE.finditer(source):
        control,expression=match.groups()
        if control in control_names: out.extend(classify_expression(window,control,expression,known_fields))
    for match in CLICK_BLOCK_RE.finditer(source):
        control,body=match.groups()
        if control not in control_names: continue
        for visible in VISIBLE_ASSIGN_RE.finditer(body):
            target,rhs=visible.groups()
            if target not in known_fields: continue
            action=classify_visible(target,rhs)
            if action: out.append(make_interaction(window,control,target,action,visible.group(0).rstrip(';')))
        for toggle in TOGGLE_OPEN_ASSIGN_RE.finditer(body):
            target,argument=toggle.groups()
            if target not in known_fields: continue
            action=classify_toggle_open(target,argument)
            if action: out.append(make_interaction(window,control,target,action,toggle.group(0).rstrip(';')))
    unique=[];seen=set()
    for item in out:
        key=(item['control'],item['targetField'],item['action'])
        if key in seen: continue
        seen.add(key);unique.append(item)
    return unique


def explicit_locations(owners: list[dict]) -> int:
    return sum(1 for owner in owners for control in owner.get('controls',[]) if 'Location' in control.get('properties',{}))


def main() -> None:
    parser=argparse.ArgumentParser();parser.add_argument("--spec",type=Path,required=True);parser.add_argument("--zircon-root",type=Path,required=True);args=parser.parse_args()
    spec=json.loads(args.spec.read_text(encoding="utf-8"));known_fields={window["field"] for window in spec.get("windows", [])};interactions=[];missing_bodies=[]
    for window in spec.get("windows", []):
        source_path=window.get("sourcePath");class_name=window.get('class') or window.get('sourceClass')
        if not source_path or not class_name: continue
        path=args.zircon_root/source_path
        if not path.exists(): continue
        source=path.read_text(encoding="utf-8-sig");body=exact_class_body(source,str(class_name))
        if not body:
            missing_bodies.append((window.get('field'),class_name,source_path));continue
        extracted=extract_window_interactions(window,body,known_fields)
        if extracted: window["interactions"]=extracted;interactions.extend(extracted)
    spec["interactions"]=interactions

    placement=audit_unplaced_controls(spec,args.zircon_root)
    render=audit_render_coverage(spec,Path('.'))
    game_explicit=explicit_locations(spec.get('windows',[]));nested_explicit=explicit_locations(spec.get('nestedWindows',[]))
    spec["interactionPass"]={
        "source":"exact Zircon source-class MouseClick -> GameScene window visibility/ToggleOpen relationships (expression + block lambdas)","count":len(interactions),"sourceBackedOnly":True,
        "sourceClassesMissingBody":missing_bodies,
        "gameExplicitLocationFloor":MIN_GAME_EXPLICIT_LOCATIONS,"nestedExplicitLocationFloor":MIN_NESTED_EXPLICIT_LOCATIONS,
        "gameExplicitLocations":game_explicit,"nestedExplicitLocations":nested_explicit,"zeroUnknownPlacementRequired":True,
        "renderCoverageIssueCount":render.get('issueCount',0),
    }
    args.spec.write_text(json.dumps(spec,indent=2,ensure_ascii=False),encoding="utf-8")
    print("Source-backed window interactions:",len(interactions))
    for interaction in interactions: print(interaction["sourceField"],interaction["control"],"->",interaction["action"],interaction["targetField"])
    print('Interaction source classes missing exact body:',len(missing_bodies))
    print('Explicit GameScene Locations:',game_explicit)
    print('Explicit nested Locations:',nested_explicit)
    print('Controls without Location:',placement['totalControlsWithoutConstructorLocation'])
    print('Unplaced classifications:',placement['classificationCounts'])
    print('UNKNOWN unplaced controls:',placement['unknownCount'])
    print('Game render type coverage:',render['gameTypeCoverage'])
    print('Nested render type coverage:',render['nestedTypeCoverage'])
    print('Indexed GameScene controls:',render['indexedGameControls'])
    print('Indexed nested controls:',render['indexedNestedControls'])
    print('Render audit issues:',render['issueCount'])
    if missing_bodies:
        raise SystemExit(f"Exact interaction class-body extraction failed: {missing_bodies}")
    if placement['unknownCount']:
        raise SystemExit(f"Unclassified controls without source-backed layout: {placement['unknownCount']}")
    if render['issueCount']:
        raise SystemExit(f"Zircon render coverage audit failed: {render['issues']}")
    if game_explicit < MIN_GAME_EXPLICIT_LOCATIONS:
        raise SystemExit(f"GameScene explicit Location coverage regressed: {game_explicit} < {MIN_GAME_EXPLICIT_LOCATIONS}")
    if nested_explicit < MIN_NESTED_EXPLICIT_LOCATIONS:
        raise SystemExit(f"Nested explicit Location coverage regressed: {nested_explicit} < {MIN_NESTED_EXPLICIT_LOCATIONS}")

if __name__=="__main__": main()