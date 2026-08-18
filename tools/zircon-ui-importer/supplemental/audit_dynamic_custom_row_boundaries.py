#!/usr/bin/env python3
"""Protect custom DX-derived families that must NOT be pre-created.

These controls are real Zircon types, but their instances are created only when
runtime/server/player collections exist. Desktop source fidelity therefore means
keeping the constructor shell while leaving these dynamic rows absent.
"""
from __future__ import annotations
import argparse,json
from pathlib import Path
CASES=(
('CommunicationBox','Client/Scenes/Views/CommunicationDialog.cs','FriendRow',('foreach (ClientFriendInfo info in FriendList.OrderBy(x => x.State))','FriendListBoxItems.Add(row = new FriendRow()')),
('HelpBox','Client/Scenes/Views/HelpDialog.cs','HelpContainer',('foreach (var helpInfo in Globals.HelpInfoList.Binding.OrderBy(x => x.Order))','var page = new HelpContainer(info)')),
('HelpBox','Client/Scenes/Views/HelpDialog.cs','HelpItem',('foreach (var infoSection in infoPage.Items.OrderBy(x => x.Order))','HelpItem cell = new HelpItem')),
('QuestBox','Client/Scenes/Views/QuestDialog.cs','QuestTreeEntry',('foreach (QuestInfo quest in pair.Value)','QuestTreeEntry entry = new QuestTreeEntry')),
('CurrencyBox','Client/Scenes/Views/CurrencyDialog.cs','CurrencyTreeHeader',('foreach (KeyValuePair<string, List<ClientUserCurrency>> pair in TreeList)','CurrencyTreeHeader header = new CurrencyTreeHeader')),
('CurrencyBox','Client/Scenes/Views/CurrencyDialog.cs','CurrencyItem',('foreach (ClientUserCurrency currency in pair.Value)','CurrencyItem entry = new CurrencyItem')),
('GuildBox','Client/Scenes/Views/GuildDialog.cs','GuildCastlePanel',('foreach (CastleInfo castle in CEnvir.CastleInfoList.Binding)','CastlePanels[castle] = new GuildCastlePanel')),
('NPCGoodsBox','Client/Scenes/Views/NPCDialog.cs','NPCGoodsCell',('foreach (NPCGood good in goods)','Cells.Add(cell = new NPCGoodsCell')),
('NPCRefineRetrieveBox','Client/Scenes/Views/NPCDialog.cs','NPCRefineCell',('foreach (ClientRefineInfo refine in Refines)','Cells.Add(cell = new NPCRefineCell')),
('CharacterBox','Client/Scenes/Views/CharacterDialog.cs','DisciplineMagicCell',('var mInfos = Globals.MagicInfoList.Binding','cell = new DisciplineMagicCell')),
)
def main():
 p=argparse.ArgumentParser();p.add_argument('--spec',type=Path,required=True);p.add_argument('--zircon-root',type=Path,required=True);a=p.parse_args();spec=json.loads(a.spec.read_text(encoding='utf-8'));by={w.get('field'):w for w in spec.get('windows',[])};rows=[];failures=[];cache={}
 for field,relative,type_name,evidence in CASES:
  w=by.get(field)
  if w is None:failures.append(f'{field} missing for runtime-only {type_name}');continue
  path=a.zircon_root/relative
  if relative not in cache:cache[relative]=path.read_text(encoding='utf-8-sig')
  source=cache[relative];missing=[needle for needle in evidence if needle not in source]
  if missing:failures.append(f'{field}.{type_name} source runtime evidence changed: {missing}')
  leaked=[str(c.get('name') or '') for c in w.get('controls',[]) if c.get('sourceType')==type_name]
  if leaked:failures.append(f'{field}.{type_name} runtime instances were pre-created: {leaked[:30]}')
  rows.append({'field':field,'type':type_name,'sourcePath':relative,'sourceEvidence':list(evidence),'manifestSourceTypeInstances':len(leaked),'runtimeOnly':True,'runtimePayloadInvented':False})
 helper=spec.get('uiCreationHelperInventory') or {}
 if helper.get('helpPagesRemainRuntimeBound') is not True:failures.append('Help helper runtime boundary missing')
 if helper.get('magicTabsRemainRuntimeBound') is not True:failures.append('Magic helper runtime boundary missing')
 report={'passed':not failures,'runtimeOnlyFamilies':len(CASES),'precreatedRuntimeInstances':0 if not failures else None,'sourceEvidenceChecked':True,'controlsFabricatedByAudit':False,'runtimePayloadsInvented':False,'rows':rows,'failures':failures};spec['dynamicCustomRowBoundaryAudit']=report;a.spec.write_text(json.dumps(spec,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
 if failures:raise SystemExit('Dynamic custom row boundary audit failed:\n- '+'\n- '.join(failures))
 print(f'Dynamic custom row boundaries: PASS ({len(CASES)} runtime-only families, 0 pre-created instances)')
if __name__=='__main__':main()
