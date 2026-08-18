#!/usr/bin/env python3
"""Exact refinement for current-Zircon constructor helper boundaries."""
from __future__ import annotations
import argparse,json
from collections import Counter
from pathlib import Path

def require_source(source,needles,label):
 missing=[n for n in needles if n not in source]
 if missing:raise SystemExit(f'{label} source contract changed:\n- '+'\n- '.join(missing))

def find_row(rows,source_class,helper):
 matches=[r for r in rows if r.get('sourceClass')==source_class and r.get('helper')==helper]
 if len(matches)!=1:raise SystemExit(f'Expected one helper row for {source_class}.{helper}, found {len(matches)}')
 return matches[0]

def main():
 p=argparse.ArgumentParser();p.add_argument('--spec',type=Path,required=True);p.add_argument('--zircon-root',type=Path,required=True);a=p.parse_args()
 spec=json.loads(a.spec.read_text(encoding='utf-8'));inv=spec.get('uiCreationHelperInventory') or {}
 if inv.get('passed') is not True or inv.get('version')!=2:raise SystemExit(f'UI helper v2 inventory missing/not green: {inv.get("version")!r}')
 rows=inv.get('rows') or []
 store=(a.zircon_root/'Client/Scenes/Views/GameStoreDialog.cs').read_text(encoding='utf-8-sig')
 require_source(store,(
  'List<StoreInfo> items = Globals.StoreInfoList?.Binding',
  'private static void AddCategoryNode(List<DXTreeNode> nodes, List<StoreInfo> items,',
  'new DXTreeNode(text, new GameStoreTreeFilter(category))',
  'AddSortOption(MarketPlaceStoreSort.Alphabetical, CEnvir.Language.GameStoreDialogSortNameLabel);',
  'AddSortOption(MarketPlaceStoreSort.HighestPrice, CEnvir.Language.GameStoreDialogSortHighestPriceLabel);',
  'AddSortOption(MarketPlaceStoreSort.LowestPrice, CEnvir.Language.GameStoreDialogSortLowestPriceLabel);',
  'AddSortOption(MarketPlaceStoreSort.Favourite, CEnvir.Language.GameStoreDialogSortFavouritesLabel);',
  'private void AddSortOption(MarketPlaceStoreSort sort, string text)',
  'Parent = SortBox.ListBox',
 ),'GameStoreDialog helpers')
 communication=(a.zircon_root/'Client/Scenes/Views/CommunicationDialog.cs').read_text(encoding='utf-8-sig')
 require_source(communication,(
  'foreach (ClientBlockInfo info in CEnvir.BlockList)',
  'BlockListBoxItems.Add(new DXListBoxItem',
  'Parent = BlockListBox,',
  'Label = { Text = info.Name },',
  'Item = info.Index',
 ),'CommunicationDialog.RefreshBlockList')
 category=find_row(rows,'GameStoreDialog','AddCategoryNode')
 if not category.get('constructorReachable') or 'DXTreeNode' not in (category.get('createdTypes') or []):raise SystemExit(f'GameStore AddCategoryNode structural contract drifted: {category}')
 category.update({'externalRuntimeData':True,'classification':'runtime-bound','status':'runtime-bound','materializedControlNames':[],'runtimeProvenance':'BuildFolderTree -> Globals.StoreInfoList?.Binding -> List<StoreInfo>','runtimePayloadInvented':False,'v3Refined':True})
 block=find_row(rows,'CommunicationDialog','RefreshBlockList')
 if not block.get('constructorReachable') or 'DXListBoxItem' not in (block.get('createdTypes') or []):raise SystemExit(f'Communication RefreshBlockList structural contract drifted: {block}')
 block.update({'externalRuntimeData':True,'classification':'runtime-bound','status':'runtime-bound','materializedControlNames':[],'runtimeProvenance':'foreach ClientBlockInfo in CEnvir.BlockList','runtimePayloadInvented':False,'v3Refined':True})
 list_audit=spec.get('listBoxItemSourceBoundaryAudit') or {}
 if list_audit.get('passed') is not True:raise SystemExit(f'DXListBoxItem boundary audit missing/not green: {list_audit}')
 store_window=next((w for w in spec.get('windows',[]) if w.get('field')=='GameStoreBox'),None)
 if not store_window:raise SystemExit('GameStoreBox missing')
 sort_items=[c for c in store_window.get('controls',[]) if c.get('type')=='DXListBoxItem' and str((c.get('properties') or {}).get('Parent') or '')=='SortBox.ListBox']
 if len(sort_items)!=4:raise SystemExit(f'GameStore SortBox source item count drifted: {len(sort_items)} != 4')
 names=[str(c.get('name') or '') for c in sort_items]
 if any(not n for n in names) or len(set(names))!=4:raise SystemExit(f'GameStore SortBox source item names invalid: {names}')
 sort_row=find_row(rows,'GameStoreDialog','AddSortOption')
 if not sort_row.get('constructorReachable') or sort_row.get('classification')!='deterministic-source' or 'DXListBoxItem' not in (sort_row.get('createdTypes') or []):raise SystemExit(f'GameStore AddSortOption contract drifted: {sort_row}')
 sort_row.update({'status':'materialized','materializedControlNames':sorted(names),'existingSourceControlsLinked':True,'duplicateControlsAdded':0,'v3Refined':True})
 companion=next((w for w in spec.get('windows',[]) if w.get('field')=='CompanionBox'),None)
 if not companion:raise SystemExit('CompanionBox missing')
 contract=companion.get('deterministicCompanionFilters') or {}
 if contract.get('passed') is not True or contract.get('runtimeCheckedStateInvented') is not False or contract.get('runtimePayloadsInvented') is not False:raise SystemExit(f'Companion deterministic filter contract missing/unsafe: {contract}')
 for helper in ('DrawClassFilter','DrawRarityFilter','DrawItemTypeFilter'):
  row=find_row(rows,'CompanionDialog',helper)
  if not row.get('constructorReachable') or row.get('classification')!='deterministic-source' or row.get('status')!='materialized' or not row.get('materializedControlNames'):raise SystemExit(f'Companion {helper} not source-materialized: {row}')
 inv['classificationCounts']=dict(Counter(r.get('classification') for r in rows));inv['statusCounts']=dict(Counter(r.get('status') for r in rows));inv['version']=3
 inv.update({'storeCategoryNodesRemainRuntimeBound':True,'communicationBlockRowsRemainRuntimeBound':True,'gameStoreSortItemsLinkedWithoutDuplication':True,'companionEnumFiltersMaterialized':True,'runtimePayloadsInvented':False,'sourceBackedOnly':True})
 spec['uiCreationHelperInventory']=inv;spec['uiCreationHelperInventoryV3Audit']={'passed':True,'runtimeHelpersRefined':['GameStoreDialog.AddCategoryNode','CommunicationDialog.RefreshBlockList'],'existingSortItemsLinked':4,'sortItemsDuplicated':0,'companionFilterControls':contract.get('controlsAdded'),'runtimePayloadsInvented':False,'sourceBackedOnly':True}
 a.spec.write_text(json.dumps(spec,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
 print(f'UI helper inventory v3: PASS -> runtime Store/category + block rows; 4 sort items linked; Companion filters={contract.get("controlsAdded")}')
if __name__=='__main__':main()
