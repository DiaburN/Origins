#!/usr/bin/env python3
"""Compatibility source gate for the superseded Consignment composite pass.

The original implementation assumed ItemType ended at Reel. Current Zircon has
38 ItemType values through SocketGem. The authoritative deterministic UI is
emitted only by augment_consignment_deterministic_composites.py. This pass keeps
source-regression coverage and records that it emits zero controls.
"""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from augment_combo_options import parse_enum

def main():
    p=argparse.ArgumentParser();p.add_argument('--spec',type=Path,required=True);p.add_argument('--zircon-root',type=Path,required=True);a=p.parse_args()
    source=(a.zircon_root/'Client/Scenes/Views/ConsignmentDialog.cs').read_text(encoding='utf-8-sig')
    for needle in ('public const int VisibleRowCount = 6;','ItemTypeMenu = new ConsignmentItemTypeMenu','SearchRows = new ConsignmentSearchRow[VisibleRowCount];','ConsignRows = new ConsignmentListRow[VisibleRowCount];','foreach (ItemType itemType in Enum.GetValues(enumType))','if (itemType == ItemType.Nothing) continue;','button.Index = selected ? 830 : 831;','SortLabel = CreateHeaderLabel(','ConsignDateLabel = CreateHeaderLabel('):
        if needle not in source: raise SystemExit(f'Consignment compatibility source changed: missing {needle!r}')
    members=parse_enum(a.zircon_root,'ItemType')
    if len(members)!=38 or members[0].get('name')!='Nothing' or members[-1].get('name')!='SocketGem': raise SystemExit(f'Current ItemType source changed: count={len(members)} first={members[:1]} last={members[-1:]}')
    spec=json.loads(a.spec.read_text(encoding='utf-8'));w=next((x for x in spec.get('windows',[]) if x.get('field')=='ConsignmentBox'),None)
    if not w: raise SystemExit('ConsignmentBox missing')
    w['legacyConsignmentCompositeCompatibility']={'passed':True,'legacyControlsEmitted':0,'authoritativeOwner':'augment_consignment_deterministic_composites.py','duplicateControlsInvented':False,'runtimePayloadsInvented':False}
    a.spec.write_text(json.dumps(spec,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print('Consignment compatibility: PASS -> legacy controls=0; modern deterministic owner retained')
if __name__=='__main__':main()
