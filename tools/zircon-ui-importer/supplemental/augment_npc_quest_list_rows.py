#!/usr/bin/env python3
"""Materialise NPCQuestListDialog's six source-created NPCQuestRow shells.

The dialog constructor always creates six rows. QuestInfo/UserQuest are assigned
later from real quest state. A null QuestInfo clears the name and hides the quest
icon but does not hide the row itself, so the neutral desktop reference keeps
six visible blank row shells exactly as Zircon constructs them.
"""
from __future__ import annotations
import argparse,json,re,sys
from copy import deepcopy
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from build_ui_source_spec import constructor_body,object_initializers,simple_assignments
PREFIX='deterministic-npc-quest-list:'
ROOT_KEYS={'Size','Visible','DrawTexture','BackColour','Border','BorderColour'}

def main():
    p=argparse.ArgumentParser();p.add_argument('--spec',type=Path,required=True);p.add_argument('--zircon-root',type=Path,required=True);a=p.parse_args()
    source=(a.zircon_root/'Client/Scenes/Views/NPCDialog.cs').read_text(encoding='utf-8-sig')
    if not re.search(r'Rows\s*=\s*new\s+NPCQuestRow\s*\[\s*6\s*\]',source): raise SystemExit('NPCQuestListDialog fixed NPCQuestRow[6] source changed')
    if not re.search(r'Rows\s*\[\s*i\s*\]\s*=\s*new\s+NPCQuestRow',source): raise SystemExit('NPCQuestListDialog row constructor loop changed')
    for needle in ('Parent = panel','Location = new Point(2, 2 + i * 22)','Size = new Size(340, 20)','public NPCQuestRow()','QuestIcon = new DXAnimatedControl','QuestNameLabel = new DXLabel','QuestNameLabel.Text = string.Empty','QuestIcon.Visible = false'):
        if needle not in source: raise SystemExit(f'NPC quest-list source changed: missing {needle!r}')
    ctor=constructor_body(source,'NPCQuestRow');defaults=simple_assignments(ctor,ROOT_KEYS);children=object_initializers(ctor)
    if {str(c.get('name') or '') for c in children}!={'QuestIcon','QuestNameLabel'}: raise SystemExit(f'NPCQuestRow child set drifted: {[c.get("name") for c in children]}')
    spec=json.loads(a.spec.read_text(encoding='utf-8'));w=next((x for x in spec.get('windows',[]) if x.get('field')=='NPCQuestListBox'),None)
    if not w: raise SystemExit('NPCQuestListBox missing')
    controls=[c for c in w.get('controls',[]) if not str(c.get('sourceGenerated') or '').startswith(PREFIX)];generated=[]
    panel=next((c for c in controls if c.get('name')=='panel' and c.get('type')=='DXControl'),None)
    if panel is None: raise SystemExit('NPCQuestListDialog source panel missing from base manifest')
    for i in range(6):
        row=f'NPCQuestRowSource{i+1:02d}';rp=dict(defaults);rp.update({'Parent':'panel','Location':f'new Point(2, {2+i*22})','Size':'new Size(340, 20)','RuntimeQuestInfo':'QuestInfo/UserQuest; null in neutral reference'})
        generated.append({'name':row,'type':'DXControl','sourceType':'NPCQuestRow','properties':rp,'sourceGenerated':PREFIX+'NPCQuestListDialog Rows[6]','runtimePayloadInvented':False})
        for template in children:
            child=deepcopy(template);original=str(child.get('name') or '');child['name']=row+original;props=child.setdefault('properties',{})
            if props.get('Parent','this')=='this': props['Parent']=row
            if original=='QuestIcon': props['Visible']='false'
            if original=='QuestNameLabel': props['Text']='""';child['resolvedText']=''
            child['sourceGenerated']=PREFIX+'NPCQuestRow constructor';child['runtimePayloadInvented']=False;generated.append(child)
    if len(generated)!=18: raise SystemExit(f'NPC quest-list deterministic count {len(generated)} != 18')
    w['controls']=generated+controls;w['deterministicNPCQuestRows']={'passed':True,'rows':6,'childrenPerRow':2,'controlsAdded':18,'rowVisibleAtConstruction':True,'questIconVisibleWithNullQuest':False,'runtimeQuestInfoInvented':False,'runtimeUserQuestInvented':False,'runtimeQuestTextInvented':False}
    a.spec.write_text(json.dumps(spec,indent=2,ensure_ascii=False)+'\n',encoding='utf-8');print('NPC quest-list rows expanded: 6 blank visible rows / 18 controls; no quest payloads')
if __name__=='__main__':main()
