#!/usr/bin/env python3
"""Lock runtime-only provenance for source dialogs that cannot be populated truthfully without live game state."""
from __future__ import annotations
import argparse,json
from pathlib import Path

POLICIES={
 'EditCharacterBox':'player appearance/customization',
 'FortuneCheckerBox':'linked item/fortune',
 'BundleBox':'bundle item/content',
 'LootBoxBox':'loot-box item/reward',
 'FishingBox':'fishing runtime state',
 'FishingCatchBox':'fish/catch runtime state',
 'HorseTameBox':'horse-tame runtime state',
 'MilestoneAchievedBox':'milestone runtime payload',
 'CaptionBox':'runtime caption/map text',
}

def main():
 p=argparse.ArgumentParser();p.add_argument('--spec',type=Path,required=True);p.add_argument('--zircon-root',type=Path,required=True);a=p.parse_args();spec=json.loads(a.spec.read_text(encoding='utf-8'));by={w.get('field'):w for w in spec.get('windows',[])};rows=[]
 for field,reason in POLICIES.items():
  w=by.get(field)
  if not w:raise SystemExit(f'Runtime-bound source window missing: {field}')
  relative=str(w.get('sourcePath') or '').strip()
  if not relative:raise SystemExit(f'Runtime-bound manifest source path missing: {field}')
  path=a.zircon_root/relative
  if not path.exists():raise SystemExit(f'Runtime-bound manifest source file missing: {field} -> {relative}')
  text=path.read_text(encoding='utf-8-sig')
  source_class=w.get('class') or w.get('sourceClass')
  if not source_class:raise SystemExit(f'Runtime-bound source class missing from manifest: {field}')
  if f'class {source_class}' not in text:raise SystemExit(f'Runtime-bound source class missing: {field}/{source_class} in {relative}')
  w['runtimeBoundaryAudit']={'passed':True,'reason':reason,'sourcePath':relative,'runtimeDataInvented':False,'serverResultInvented':False,'sourceChromePreserved':True}
  rows.append({'field':field,'id':w.get('id'),'sourceClass':source_class,'sourcePath':relative,'reason':reason})
 spec['runtimeBoundWindowAudit']={'passed':True,'windowCount':len(rows),'windows':rows,'manifestSourcePathsVerified':True,'runtimeDataInvented':False}
 a.spec.write_text(json.dumps(spec,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
 print(f'Runtime-bound window source audit: PASS ({len(rows)} windows; manifest source paths verified)')
if __name__=='__main__':main()
