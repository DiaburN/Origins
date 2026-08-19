#!/usr/bin/env python3
"""Inventory non-DX Zircon view composites that the flat DX parser cannot see.

`build_ui_source_spec.object_initializers()` intentionally parses `new DX*`.
Zircon view files also use custom controls derived from DXControl, frequently in
fixed arrays or constructor-called helper methods. This audit walks both direct
constructor code and immediate constructor/helper call graphs, records custom
composite materialisation, and strictly protects all families already expanded
by supplemental source passes. It never creates UI itself.
"""
from __future__ import annotations
import argparse,json,re
from collections import defaultdict,deque
from pathlib import Path
from audit_ui_creation_helper_inventory import class_body,constructor_body,constructor_reachability,methods,strip_event_lambdas
CLASS_RE=re.compile(r"\b(?:public|private|protected|internal)?\s*(?:sealed\s+|abstract\s+|partial\s+)*class\s+([A-Za-z_][A-Za-z0-9_]*)\s*:\s*([A-Za-z_][A-Za-z0-9_]*)")
NEW_RE=re.compile(r"\bnew\s+([A-Za-z_][A-Za-z0-9_]*)\b")
ARRAY_RE=re.compile(r"\bnew\s+([A-Za-z_][A-Za-z0-9_]*)\s*\[([^\]]+)\]")
# Runtime-created families (QuestTreeEntry, CurrencyTreeHeader/CurrencyItem,
# MagicTab, HelpContainer/HelpItem, FriendRow, NPCGoodsCell/NPCRefineCell, etc.)
# are intentionally not protected as constructor instances.
KNOWN={
('RankingBox','RankingLine'):12,('DungeonFinderBox','DungeonRow'):9,('FortuneCheckerBox','FortuneCheckerRow'):9,('BigMapBox','BigMapListRow'):48,
('GuildBox','GuildMemberRow'):18,
('GameStoreBox','GameStoreItemListControl'):1,('GameStoreBox','GameStoreItem'):10,('GameStoreBox','GameStoreTopItemsControl'):1,('GameStoreBox','GameStoreTopItemControl'):5,
('CommunicationBox','CommunicationReceivedRow'):5,
('ConsignmentBox','ConsignmentItemTypeMenu'):1,('ConsignmentBox','ConsignmentSearchRow'):6,('ConsignmentBox','ConsignmentListRow'):6,
('GroupBox','GroupLFGRow'):5,
('CurrencyBox','CurrencyTree'):1,
('QuestBox','QuestTab'):3,('QuestBox','MilestoneTab'):1,('QuestBox','MissionTab'):1,
('NPCQuestListBox','NPCQuestRow'):6,
('HelpBox','HelpMenu'):1,
}
def class_bases(text):return {m.group(1):m.group(2) for m in CLASS_RE.finditer(text)}
def derives_dx(name,bases):
 seen=set();cur=name
 while cur and cur not in seen:
  seen.add(cur);base=bases.get(cur,'')
  if base.startswith('DX'):return True
  cur=base
 return False
def creation_chunk(source_text,class_name):
 body=class_body(source_text,class_name);ctor=constructor_body(body,class_name)
 if not ctor:return '',[]
 method_map=methods(body);reach=constructor_reachability(ctor,method_map);chunks=[strip_event_lambdas(ctor)]
 for helper in sorted(reach,key=lambda n:(reach[n],n)):
  for method_body in method_map.get(helper,[]):chunks.append(strip_event_lambdas(method_body))
 return '\n'.join(chunks),sorted(reach,key=lambda n:(reach[n],n))
def runtime_markers(chunk):
 patterns={'Binding':r'\.Binding\b','SelectedInfo':r'\bSelectedInfo\b','ClientMarketPlaceInfo':r'\bClientMarketPlaceInfo\b','StoreInfo':r'\bStoreInfo\b','ClientMailInfo':r'\bClientMailInfo\b','ClientLookingForGroup':r'\bClientLookingForGroup\b','ClientGuildMemberInfo':r'\bClientGuildMemberInfo\b','RankInfo':r'\bRankInfo\b','InstanceInfo':r'\bInstanceInfo\b','HelpInfo':r'\bHelpInfo\b','MagicInfo':r'\bMagicInfo\b','QuestInfo':r'\bQuestInfo\b','ClientUserCurrency':r'\bClientUserCurrency\b','ClientFriendInfo':r'\bClientFriendInfo\b','NPCGood':r'\bNPCGood\b','ClientRefineInfo':r'\bClientRefineInfo\b'}
 return [label for label,pattern in patterns.items() if re.search(pattern,chunk)]
def materialisation(window,type_name):
 controls=window.get('controls') or [];typed=[str(c.get('name') or '') for c in controls if c.get('sourceType')==type_name];prov=[str(c.get('name') or '') for c in controls if type_name in str(c.get('sourceGenerated') or '')]
 return {'sourceTypeInstances':len(typed),'sourceTypeNames':typed,'provenanceControls':len(prov),'provenanceSample':prov[:20],'hasEvidence':bool(typed or prov)}
def reachable_custom_types(source_text,root_class):
 bases=class_bases(source_text);custom={n for n in bases if not n.startswith('DX') and derives_dx(n,bases)};root_chunk,root_helpers=creation_chunk(source_text,root_class)
 if not root_chunk:return [],bases
 rows=[];queue=deque([(root_class,root_chunk,0,None,root_helpers)]);visited=set()
 while queue:
  owner,chunk,depth,parent,helpers=queue.popleft()
  if owner in visited:continue
  visited.add(owner);arrays=defaultdict(list)
  for m in ARRAY_RE.finditer(chunk):arrays[m.group(1)].append(' '.join(m.group(2).split()))
  created=[n for n in NEW_RE.findall(chunk) if n in custom]
  for type_name in sorted(set(created)):
   child_chunk,child_helpers=creation_chunk(source_text,type_name);rows.append({'owner':owner,'type':type_name,'constructorDepth':depth+1,'parentComposite':parent,'arrayExpressions':sorted(set(arrays.get(type_name,[]))),'newOccurrences':created.count(type_name),'ownerImmediateHelpers':helpers,'compositeImmediateHelpers':child_helpers,'constructorRuntimeMarkers':runtime_markers(child_chunk),'customComposite':True,'sourceBackedOnly':True})
   if child_chunk and type_name not in visited:queue.append((type_name,child_chunk,depth+1,type_name,child_helpers))
 return rows,bases
def main():
 p=argparse.ArgumentParser();p.add_argument('--spec',type=Path,required=True);p.add_argument('--zircon-root',type=Path,required=True);a=p.parse_args();spec=json.loads(a.spec.read_text(encoding='utf-8'));report_rows=[];by_field={w.get('field'):w for w in spec.get('windows',[])}
 for window in spec.get('windows',[]):
  source_path=str(window.get('sourcePath') or '');source_class=str(window.get('class') or '');path=a.zircon_root/source_path
  if not source_path or not source_class or not path.exists():continue
  source_text=path.read_text(encoding='utf-8-sig');entries,_=reachable_custom_types(source_text,source_class)
  for entry in entries:
   evidence=materialisation(window,entry['type']);entry.update({'id':window.get('id'),'field':window.get('field'),'sourceClass':source_class,'sourcePath':source_path,'materialisation':evidence,'knownProtectedFamily':(window.get('field'),entry['type']) in KNOWN});report_rows.append(entry)
 failures=[];protected=[]
 for (field,type_name),minimum in KNOWN.items():
  window=by_field.get(field)
  if window is None:failures.append(f'{field} missing for protected custom composite {type_name}');continue
  evidence=materialisation(window,type_name);source_entries=[r for r in report_rows if r['field']==field and r['type']==type_name]
  if not source_entries:failures.append(f'{field}.{type_name} no longer constructor/helper-reachable from current Zircon source');continue
  typed=evidence['sourceTypeInstances'];prov=evidence['provenanceControls']
  if typed:
   if typed<minimum:failures.append(f'{field}.{type_name}: {typed} sourceType instances < {minimum}')
  elif prov<minimum:failures.append(f'{field}.{type_name}: provenance evidence {prov} < {minimum}')
  protected.append({'field':field,'type':type_name,'minimumEvidence':minimum,**evidence})
 review=[{'field':r['field'],'type':r['type'],'owner':r['owner'],'constructorDepth':r['constructorDepth'],'arrayExpressions':r['arrayExpressions'],'runtimeMarkers':r['constructorRuntimeMarkers'],'hasMaterialisationEvidence':r['materialisation']['hasEvidence']} for r in report_rows if not r['knownProtectedFamily']]
 report={'passed':not failures,'version':3,'parserBoundary':'base object_initializers parses new DX*; custom DX-derived composites require explicit expansion/audit','constructorAndHelperReachability':True,'eventCallbacksExcluded':True,'constructorReachableCompositeOccurrences':len(report_rows),'protectedFamilyCount':len(KNOWN),'protectedFamilies':protected,'reviewQueue':review,'reviewQueueCount':len(review),'runtimePayloadsInvented':False,'controlsFabricatedByAudit':False,'failures':failures,'rows':report_rows}
 spec['customCompositeInventory']=report;a.spec.write_text(json.dumps(spec,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
 if failures:raise SystemExit('Custom composite inventory failed:\n- '+'\n- '.join(failures))
 print(f'Custom composite inventory v3: PASS -> protected={len(KNOWN)} source-occurrences={len(report_rows)} review={len(review)}')
if __name__=='__main__':main()
