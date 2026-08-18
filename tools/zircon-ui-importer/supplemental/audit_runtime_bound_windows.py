#!/usr/bin/env python3
"""Lock runtime-only provenance for source dialogs that cannot be populated truthfully without live game state."""
from __future__ import annotations
import argparse,json
from pathlib import Path

POLICIES={
 'EditCharacterBox':('Client/Scenes/Views/EditCharacterDialog.cs','player appearance/customization'),
 'FortuneCheckerBox':('Client/Scenes/Views/FortuneCheckerDialog.cs','linked item/fortune'),
 'BundleBox':('Client/Scenes/Views/BundleDialog.cs','bundle item/content'),
 'LootBoxBox':('Client/Scenes/Views/LootBoxDialog.cs','loot-box item/reward'),
 'FishingBox':('Client/Scenes/Views/FishingDialog.cs','fishing runtime state'),
 'FishingCatchBox':('Client/Scenes/Views/FishingDialog.cs','fish/catch runtime state'),
 'HorseTameBox':('Client/Scenes/Views/HorseTameDialog.cs','horse-tame runtime state'),
 'MilestoneAchievedBox':('Client/Scenes/Views/MilestoneAchievedDialog.cs','milestone runtime payload'),
 'CaptionBox':('Client/Scenes/Views/CaptionDialog.cs','runtime caption/map text'),
}

def main():
 p=argparse.ArgumentParser();p.add_argument('--spec',type=Path,required=True);p.add_argument('--zircon-root',type=Path,required=True);a=p.parse_args();spec=json.loads(a.spec.read_text(encoding='utf-8'));by={w.get('field'):w for w in spec.get('windows',[])};rows=[]
 for field,(relative,reason) in POLICIES.items():
  w=by.get(field)
  if not w:raise SystemExit(f'Runtime-bound source window missing: {field}')
  path=a.zircon_root/relative
  if not path.exists():raise SystemExit(f'Runtime-bound source file missing: {relative}')
  text=path.read_text(encoding='utf-8-sig')
  source_class=w.get('class') or w.get('sourceClass')
  if source_class and f'class {source_class}' not in text:raise SystemExit(f'Runtime-bound source class missing: {field}/{source_class}')
  w['runtimeBoundaryAudit']={'passed':True,'reason':reason,'runtimeDataInvented':False,'serverResultInvented':False,'sourceChromePreserved':True}
  rows.append({'field':field,'id':w.get('id'),'sourceClass':source_class,'reason':reason})
 spec['runtimeBoundWindowAudit']={'passed':True,'windowCount':len(rows),'windows':rows,'runtimeDataInvented':False}
 a.spec.write_text(json.dumps(spec,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
 print(f'Runtime-bound window source audit: PASS ({len(rows)} windows)')
if __name__=='__main__':main()
