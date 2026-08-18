#!/usr/bin/env python3
"""Strict gate for BigMapDialog.CreateSidePanel deterministic shell."""
from __future__ import annotations
import argparse,json
from pathlib import Path

def props(c):return (c or {}).get('properties') or {}
def main():
 p=argparse.ArgumentParser();p.add_argument('--spec',type=Path,required=True);p.add_argument('--zircon-root',type=Path,required=True);a=p.parse_args();spec=json.loads(a.spec.read_text(encoding='utf-8'));w=next((x for x in spec.get('windows',[]) if x.get('field')=='BigMapBox'),None)
 if not w:raise SystemExit('BigMapBox missing')
 c=w.get('deterministicBigMapSidePanel') or {};expected={'passed':True,'controlsAdded':4,'sidePanels':1,'tabControls':1,'tabs':2,'initialSelectedTab':'NPCTab','runtimeGeometryInvented':False,'runtimeMapInfoInvented':False,'runtimeNPCsInvented':False,'runtimeMonstersInvented':False}
 for k,v in expected.items():
  if c.get(k)!=v:raise SystemExit(f'BigMap side-panel contract drifted: {k}={c.get(k)!r}, expected {v!r}')
 by={str(x.get('name') or ''):x for x in w.get('controls',[])};side=by.get('SidePanel');tabs=by.get('SideTabControl');npc=by.get('NPCTab');monster=by.get('MonsterTab')
 if side is None or side.get('type')!='DXControl':raise SystemExit('BigMap SidePanel missing')
 if props(side).get('Parent')!='this' or props(side).get('Border')!='true' or props(side).get('BorderColour')!='Constants.PrimaryColour':raise SystemExit(f'BigMap SidePanel source chrome drifted: {props(side)}')
 if tabs is None or tabs.get('type')!='DXTabControl' or props(tabs).get('Parent')!='SidePanel' or props(tabs).get('MarginLeft')!='0' or props(tabs).get('Padding')!='0':raise SystemExit(f'BigMap SideTabControl drifted: {tabs}')
 for item,key,label in ((npc,'BigMapNPCTabLabel','NPCTab'),(monster,'BigMapMonsterTabLabel','MonsterTab')):
  if item is None or item.get('type')!='DXTab' or props(item).get('Parent')!='SideTabControl' or props(item).get('MinimumTabWidth')!='104':raise SystemExit(f'BigMap {label} source tab drifted: {item}')
  if key not in str(props(item).get('TabButton') or '') or not str(item.get('resolvedText') or '').strip():raise SystemExit(f'BigMap {label} source label unresolved: {item}')
 generated=[x for x in w.get('controls',[]) if str(x.get('sourceGenerated') or '').startswith('deterministic-bigmap-side-shell:')]
 if len(generated)!=4 or any(x.get('runtimePayloadInvented') is not False for x in generated):raise SystemExit(f'BigMap side shell generated count/payload drifted: {len(generated)}')
 spec['bigMapSidePanelAudit']={'passed':True,'deterministicControls':4,'initialSelectedTab':'NPCTab','runtimeGeometryInvented':False,'runtimeMapInfoInvented':False,'runtimeNPCsInvented':False,'runtimeMonstersInvented':False};a.spec.write_text(json.dumps(spec,indent=2,ensure_ascii=False)+'\n',encoding='utf-8');print('BigMap side-panel shell audit: PASS (4 controls; map/list runtime neutral)')
if __name__=='__main__':main()
