#!/usr/bin/env python3
"""Extract simple source-backed GameScene interactions and final placement audit."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from audit_ui_unplaced_controls import apply as audit_unplaced_controls

CLICK_EXPR_RE = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)\.MouseClick\s*\+=\s*\([^)]*\)\s*=>\s*([^;]+);",re.S)
VISIBLE_RE = re.compile(r"^GameScene\.Game\.([A-Za-z_][A-Za-z0-9_]*)\.Visible\s*=\s*(.+)$",re.S)
TOGGLE_OPEN_RE = re.compile(r"^GameScene\.Game\.([A-Za-z_][A-Za-z0-9_]*)\.ToggleOpen\s*\(\s*(.+)\s*\)$",re.S)


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

def extract_window_interactions(window: dict, source: str, known_fields: set[str]) -> list[dict]:
    out=[];control_names={control.get("name") for control in window.get("controls", [])}
    for match in CLICK_EXPR_RE.finditer(source):
        control,expression=match.groups()
        if control not in control_names: continue
        expression=normalise(expression)
        visible=VISIBLE_RE.match(expression)
        if visible:
            target,rhs=visible.groups()
            if target not in known_fields: continue
            action=classify_visible(target,rhs)
            if action: out.append({"sourceField":window["field"],"sourceClass":window.get("class"),"control":control,"event":"MouseClick","action":action,"targetField":target,"sourceExpression":expression})
            continue
        toggle=TOGGLE_OPEN_RE.match(expression)
        if toggle:
            target,argument=toggle.groups()
            if target not in known_fields: continue
            action=classify_toggle_open(target,argument)
            if action: out.append({"sourceField":window["field"],"sourceClass":window.get("class"),"control":control,"event":"MouseClick","action":action,"targetField":target,"sourceExpression":expression})
    return out


def main() -> None:
    parser=argparse.ArgumentParser();parser.add_argument("--spec",type=Path,required=True);parser.add_argument("--zircon-root",type=Path,required=True);args=parser.parse_args()
    spec=json.loads(args.spec.read_text(encoding="utf-8"));known_fields={window["field"] for window in spec.get("windows", [])};interactions=[]
    for window in spec.get("windows", []):
        source_path=window.get("sourcePath")
        if not source_path: continue
        path=args.zircon_root/source_path
        if not path.exists(): continue
        source=path.read_text(encoding="utf-8-sig");extracted=extract_window_interactions(window,source,known_fields)
        if extracted: window["interactions"]=extracted;interactions.extend(extracted)
    spec["interactions"]=interactions
    spec["interactionPass"]={"source":"direct Zircon MouseClick -> GameScene window visibility/ToggleOpen relationships","count":len(interactions),"sourceBackedOnly":True}

    audit=audit_unplaced_controls(spec,args.zircon_root)
    args.spec.write_text(json.dumps(spec,indent=2,ensure_ascii=False),encoding="utf-8")
    print("Source-backed window interactions:",len(interactions))
    for interaction in interactions: print(interaction["sourceField"],interaction["control"],"->",interaction["action"],interaction["targetField"])
    print('Controls without Location:',audit['totalControlsWithoutConstructorLocation'])
    print('Unplaced classifications:',audit['classificationCounts'])
    print('UNKNOWN unplaced controls:',audit['unknownCount'])
    for row in audit['unknown'][:100]: print('  UNKNOWN',row['window'],row['control'],row['type'],'parent=',row.get('parent'))
    if audit['unknownCount']:
        raise SystemExit(f"Unclassified controls without source-backed layout: {audit['unknownCount']}")

if __name__=="__main__": main()
