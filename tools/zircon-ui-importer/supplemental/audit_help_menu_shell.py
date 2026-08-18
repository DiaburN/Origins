#!/usr/bin/env python3
"""Strict gate for HelpDialog's fixed HelpMenu shell."""
from __future__ import annotations
import argparse,json
from pathlib import Path

def props(c): return (c or {}).get('properties') or {}
def main():
    p=argparse.ArgumentParser();p.add_argument('--spec',type=Path,required=True);p.add_argument('--zircon-root',type=Path,required=True);a=p.parse_args();spec=json.loads(a.spec.read_text(encoding='utf-8'));w=next((x for x in spec.get('windows',[]) if x.get('field')=='HelpBox'),None)
    if not w: raise SystemExit('HelpBox missing')
    contract=w.get('deterministicHelpMenu') or {};expected={'passed':True,'controlsAdded':2,'menuShells':1,'scrollbars':1,'runtimeButtonsInvented':False,'runtimeHelpContainersInvented':False,'runtimeHelpTabsInvented':False,'runtimeHelpItemsInvented':False,'runtimeHelpInfoInvented':False}
    for k,v in expected.items():
        if contract.get(k)!=v: raise SystemExit(f'Help menu contract drifted: {k}={contract.get(k)!r}, expected {v!r}')
    by={str(c.get('name') or ''):c for c in w.get('controls',[])};menu=by.get('HelpMenuSource');scroll=by.get('HelpMenuSourceScrollBar')
    if menu is None or menu.get('sourceType')!='HelpMenu': raise SystemExit('HelpMenu source shell missing')
    mp=props(menu)
    if mp.get('Parent')!='this' or mp.get('Location')!='new Point(13, 70)' or mp.get('Size')!='new Size(156, 306)': raise SystemExit(f'HelpMenu source geometry drifted: {mp}')
    sp=props(scroll)
    if sp.get('Parent')!='HelpMenuSource' or sp.get('Location')!='new Point(134, 0)' or sp.get('Size')!='new Size(20, 310)' or sp.get('Change')!='23' or sp.get('VisibleSize')!='HelpMenuSource.Size.Height' or sp.get('MaxValue')!='0': raise SystemExit(f'HelpMenu scrollbar source/neutral state drifted: {sp}')
    generated=[c for c in w.get('controls',[]) if str(c.get('sourceGenerated') or '').startswith('deterministic-help-menu:')]
    if len(generated)!=2 or any(c.get('runtimePayloadInvented') is not False for c in generated): raise SystemExit('HelpMenu generated control/payload contract drifted')
    forbidden={'HelpContainer','HelpItem'};leaked=[c.get('name') for c in w.get('controls',[]) if c.get('sourceType') in forbidden]
    if leaked: raise SystemExit(f'Runtime Help pages/items were pre-created: {leaked}')
    spec['helpMenuShellAudit']={'passed':True,'deterministicControls':2,'runtimeButtonsInvented':False,'runtimeHelpContainersInvented':False,'runtimeHelpTabsInvented':False,'runtimeHelpItemsInvented':False,'runtimeHelpInfoInvented':False};a.spec.write_text(json.dumps(spec,indent=2,ensure_ascii=False)+'\n',encoding='utf-8');print('Help menu shell audit: PASS (2 controls; no HelpInfo-derived UI)')
if __name__=='__main__':main()
