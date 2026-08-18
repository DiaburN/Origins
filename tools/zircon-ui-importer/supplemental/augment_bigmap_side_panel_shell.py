#!/usr/bin/env python3
"""Materialise BigMapDialog.CreateSidePanel deterministic shell controls.

CreateSidePanel() is called directly by the BigMapDialog constructor. Side-panel
geometry is completed later by OnClientAreaChanged/LayoutSidePanel, but the four
shell controls (panel, tab control, NPC tab, monster tab) always exist before any
MapInfo/NPC/monster runtime payload arrives.
"""
from __future__ import annotations
import argparse,json
from pathlib import Path
PREFIX='deterministic-bigmap-side-shell:'

def text(spec,key,fallback):return str(((spec.get('language') or {}).get('English') or {}).get(key) or fallback)
def main():
 p=argparse.ArgumentParser();p.add_argument('--spec',type=Path,required=True);p.add_argument('--zircon-root',type=Path,required=True);a=p.parse_args()
 source=(a.zircon_root/'Client/Scenes/Views/BigMapDialog.cs').read_text(encoding='utf-8-sig')
 for needle in ('CreateSidePanel();','private void CreateSidePanel()','SidePanel = new DXControl','SideTabControl = new DXTabControl','NPCTab = new DXTab','MonsterTab = new DXTab','MinimumTabWidth = 104','TabButton = { Label = { Text = CEnvir.Language.BigMapNPCTabLabel } }','TabButton = { Label = { Text = CEnvir.Language.BigMapMonsterTabLabel } }','SideTabControl.SelectedTab = NPCTab;'):
  if needle not in source:raise SystemExit(f'BigMap side-panel source changed: missing {needle!r}')
 spec=json.loads(a.spec.read_text(encoding='utf-8'));w=next((x for x in spec.get('windows',[]) if x.get('field')=='BigMapBox'),None)
 if not w:raise SystemExit('BigMapBox missing')
 controls=[c for c in w.get('controls',[]) if not str(c.get('sourceGenerated') or '').startswith(PREFIX)]
 npc=text(spec,'BigMapNPCTabLabel','NPC');monster=text(spec,'BigMapMonsterTabLabel','Monster')
 generated=[
 {'name':'SidePanel','type':'DXControl','properties':{'Parent':'this','BackColour':'Constants.WindowBackColour','Border':'true','BorderColour':'Constants.PrimaryColour','DrawTexture':'true','RuntimeGeometry':'OnClientAreaChanged uses _MapClientSize; neutral source leaves unresolved until map layout'},'sourceGenerated':PREFIX+'CreateSidePanel','runtimePayloadInvented':False},
 {'name':'SideTabControl','type':'DXTabControl','properties':{'Parent':'SidePanel','MarginLeft':'0','Padding':'0','BackColour':'Color.Empty','RuntimeGeometry':'LayoutSidePanel/OnClientAreaChanged'},'sourceGenerated':PREFIX+'CreateSidePanel','runtimePayloadInvented':False},
 {'name':'NPCTab','type':'DXTab','properties':{'Parent':'SideTabControl','MinimumTabWidth':'104','BackColour':'Color.Empty','TabButton':'{ Label = { Text = CEnvir.Language.BigMapNPCTabLabel } }'},'resolvedText':npc,'sourceGenerated':PREFIX+'CreateSidePanel','runtimePayloadInvented':False},
 {'name':'MonsterTab','type':'DXTab','properties':{'Parent':'SideTabControl','MinimumTabWidth':'104','BackColour':'Color.Empty','TabButton':'{ Label = { Text = CEnvir.Language.BigMapMonsterTabLabel } }'},'resolvedText':monster,'sourceGenerated':PREFIX+'CreateSidePanel','runtimePayloadInvented':False},
 ]
 w['controls']=generated+controls;w['deterministicBigMapSidePanel']={'passed':True,'controlsAdded':4,'sidePanels':1,'tabControls':1,'tabs':2,'initialSelectedTab':'NPCTab','runtimeGeometryInvented':False,'runtimeMapInfoInvented':False,'runtimeNPCsInvented':False,'runtimeMonstersInvented':False}
 a.spec.write_text(json.dumps(spec,indent=2,ensure_ascii=False)+'\n',encoding='utf-8');print('BigMap side-panel shell expanded: 4 deterministic controls; map/list payloads neutral')
if __name__=='__main__':main()
