#!/usr/bin/env python3
"""Strict gate for NPCQuestListDialog's six deterministic row shells."""
from __future__ import annotations
import argparse,json
from pathlib import Path

def props(c): return (c or {}).get('properties') or {}
def main():
    p=argparse.ArgumentParser();p.add_argument('--spec',type=Path,required=True);p.add_argument('--zircon-root',type=Path,required=True);a=p.parse_args();spec=json.loads(a.spec.read_text(encoding='utf-8'));w=next((x for x in spec.get('windows',[]) if x.get('field')=='NPCQuestListBox'),None)
    if not w: raise SystemExit('NPCQuestListBox missing')
    contract=w.get('deterministicNPCQuestRows') or {};expected={'passed':True,'rows':6,'childrenPerRow':2,'controlsAdded':18,'rowVisibleAtConstruction':True,'questIconVisibleWithNullQuest':False,'runtimeQuestInfoInvented':False,'runtimeUserQuestInvented':False,'runtimeQuestTextInvented':False}
    for k,v in expected.items():
        if contract.get(k)!=v: raise SystemExit(f'NPC quest row contract drifted: {k}={contract.get(k)!r}, expected {v!r}')
    by={str(c.get('name') or ''):c for c in w.get('controls',[])}
    for i in range(6):
        name=f'NPCQuestRowSource{i+1:02d}';row=by.get(name);icon=by.get(name+'QuestIcon');label=by.get(name+'QuestNameLabel')
        if row is None or row.get('sourceType')!='NPCQuestRow': raise SystemExit(f'NPC quest source row missing: {name}')
        rp=props(row)
        if rp.get('Parent')!='panel' or rp.get('Location')!=f'new Point(2, {2+i*22})' or rp.get('Size')!='new Size(340, 20)': raise SystemExit(f'NPC quest row geometry drifted: {name} -> {rp}')
        # Source constructor does not set row Visible=false. Do not silently hide blank rows.
        if rp.get('Visible')=='false': raise SystemExit(f'NPC quest row was artificially hidden: {name}')
        if icon is None or icon.get('type')!='DXAnimatedControl' or props(icon).get('Parent')!=name or props(icon).get('Visible')!='false': raise SystemExit(f'NPC quest icon neutral state drifted: {name}')
        if label is None or label.get('type')!='DXLabel' or props(label).get('Parent')!=name or label.get('resolvedText') not in ('',None): raise SystemExit(f'NPC quest label fabricated/missing: {name}')
    generated=[c for c in w.get('controls',[]) if str(c.get('sourceGenerated') or '').startswith('deterministic-npc-quest-list:')]
    if len(generated)!=18 or any(c.get('runtimePayloadInvented') is not False for c in generated): raise SystemExit(f'NPC quest generated controls/payload contract drifted: {len(generated)}')
    spec['npcQuestListRowAudit']={'passed':True,'rows':6,'deterministicControls':18,'blankRowsVisibleAtConstruction':True,'runtimeQuestInfoInvented':False,'runtimeUserQuestInvented':False,'runtimeQuestTextInvented':False};a.spec.write_text(json.dumps(spec,indent=2,ensure_ascii=False)+'\n',encoding='utf-8');print('NPC quest-list row audit: PASS (6 blank rows / 18 controls; no quest payloads)')
if __name__=='__main__':main()
