#!/usr/bin/env python3
"""Keep AutoPathRouteControl runtime-bound in MiniMap and BigMap."""
from __future__ import annotations
import argparse,json
from pathlib import Path

def main():
 p=argparse.ArgumentParser();p.add_argument('--spec',type=Path,required=True);p.add_argument('--zircon-root',type=Path,required=True);a=p.parse_args();spec=json.loads(a.spec.read_text(encoding='utf-8'));by={w.get('field'):w for w in spec.get('windows',[])};fail=[];rows=[]
 for field,relative in (('MiniMapBox','Client/Scenes/Views/MiniMapDialog.cs'),('BigMapBox','Client/Scenes/Views/BigMapDialog.cs')):
  w=by.get(field)
  if not w:fail.append(f'{field} missing');continue
  source=(a.zircon_root/relative).read_text(encoding='utf-8-sig')
  for needle in ('for (int i = 0; i < GameScene.Game.AutoPathRoutes.Count; i++)','AutoPathRouteControl control = new AutoPathRouteControl'):
   if needle not in source:fail.append(f'{field} AutoPath runtime source changed: {needle}')
  leaked=[str(c.get('name') or '') for c in w.get('controls',[]) if c.get('sourceType')=='AutoPathRouteControl']
  if leaked:fail.append(f'{field} pre-created AutoPathRouteControl: {leaked}')
  rows.append({'field':field,'sourcePath':relative,'manifestInstances':len(leaked),'runtimeCollection':'GameScene.Game.AutoPathRoutes'})
 report={'passed':not fail,'windows':2,'precreatedRouteControls':0 if not fail else None,'runtimeRoutesInvented':False,'controlsFabricatedByAudit':False,'rows':rows,'failures':fail};spec['autoPathRouteRuntimeBoundaryAudit']=report;a.spec.write_text(json.dumps(spec,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
 if fail:raise SystemExit('AutoPath route runtime boundary failed:\n- '+'\n- '.join(fail))
 print('AutoPath route runtime boundary: PASS (MiniMap + BigMap, 0 pre-created routes)')
if __name__=='__main__':main()
