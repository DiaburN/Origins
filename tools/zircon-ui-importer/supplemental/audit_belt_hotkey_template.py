#!/usr/bin/env python3
"""Strict gate for BeltDialog's resize-dependent hotkey label template/runtime."""
from __future__ import annotations
import argparse,json
from pathlib import Path

def main():
 p=argparse.ArgumentParser();p.add_argument('--spec',type=Path,required=True);p.add_argument('--zircon-root',type=Path,required=True);a=p.parse_args();spec=json.loads(a.spec.read_text(encoding='utf-8'));w=next((x for x in spec.get('windows',[]) if x.get('field')=='BeltBox'),None)
 if not w:raise SystemExit('BeltBox missing')
 t=w.get('beltHotkeyLabelTemplate') or {};expected={'passed':True,'sourceType':'DXLabel','parentExpression':'Grid.Grid[i]','countExpression':'Grid.Grid.Length','textExpression':'((i + 1) % 10).ToString()','fontSize':8.0,'fontStyle':'Italic','location':[-2,-1],'isControl':False,'localResizeDependent':True,'fixedCountInvented':False,'runtimeItemDataInvented':False,'runtimePlayerDataInvented':False}
 for k,v in expected.items():
  if t.get(k)!=v:raise SystemExit(f'Belt hotkey template drifted: {k}={t.get(k)!r}, expected {v!r}')
 grid=next((c for c in w.get('controls',[]) if c.get('name')=='Grid' and c.get('type')=='DXItemGrid'),None)
 if grid is None:raise SystemExit('Belt Grid missing')
 runtime=Path(__file__).resolve().parents[3]/'apps/zircon-ui-reference/extra-runtimes/belt-fidelity-runtime.js'
 if not runtime.exists():raise SystemExit('Belt fidelity runtime missing')
 text=runtime.read_text(encoding='utf-8')
 for needle in ("root.id!=='w-belt'",".generic-grid .generic-cell","String((index+1)%10)","left='-2px'","top='-1px'","fontStyle='italic'","fixedCountInvented!==false"):
  if needle not in text:raise SystemExit(f'Belt runtime source contract drifted: {needle}')
 spec['beltHotkeyTemplateAudit']={'passed':True,'localResizeDependent':True,'fixedCountInvented':False,'runtimeCreatesLabelsPerRenderedGridCell':True,'runtimeItemDataInvented':False,'runtimePlayerDataInvented':False};a.spec.write_text(json.dumps(spec,indent=2,ensure_ascii=False)+'\n',encoding='utf-8');print('Belt hotkey template audit: PASS (local cell count; no fake items/player data)')
if __name__=='__main__':main()
