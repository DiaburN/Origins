#!/usr/bin/env python3
"""Late final-matrix bridge for local-size and runtime-only source contracts."""
from __future__ import annotations
import argparse,json
from pathlib import Path

def main():
 p=argparse.ArgumentParser();p.add_argument('--spec',type=Path,required=True);p.add_argument('--zircon-root',type=Path,required=True);a=p.parse_args();spec=json.loads(a.spec.read_text(encoding='utf-8'));final=spec.get('finalSupplementalSourceMatrix') or {};fail=[]
 big=spec.get('bigMapSidePanelAudit') or {};belt=spec.get('beltHotkeyTemplateAudit') or {};auto=spec.get('autoPathRouteRuntimeBoundaryAudit') or {}
 if final.get('passed') is not True:fail.append(f'prior final matrix missing/not PASS: {final}')
 if big.get('passed') is not True or big.get('deterministicControls')!=4 or big.get('runtimeGeometryInvented') is not False or big.get('runtimeMapInfoInvented') is not False:fail.append(f'BigMap side-shell contract incomplete: {big}')
 if belt.get('passed') is not True or belt.get('localResizeDependent') is not True or belt.get('fixedCountInvented') is not False or belt.get('runtimeCreatesLabelsPerRenderedGridCell') is not True or belt.get('runtimeItemDataInvented') is not False or belt.get('runtimePlayerDataInvented') is not False:fail.append(f'Belt hotkey template contract incomplete: {belt}')
 if auto.get('passed') is not True or auto.get('windows')!=2 or auto.get('precreatedRouteControls')!=0 or auto.get('runtimeRoutesInvented') is not False:fail.append(f'AutoPath runtime boundary incomplete: {auto}')
 final['bigMapSidePanelControls']=big.get('deterministicControls');final['beltHotkeysLocalResizeTemplate']=belt.get('passed') is True;final['autoPathRuntimeOnlyWindows']=auto.get('windows');final['passed']=final.get('passed') is True and not fail;final['failures']=list(final.get('failures') or [])+fail;spec['finalSupplementalSourceMatrix']=final
 a.spec.write_text(json.dumps(spec,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
 if fail:raise SystemExit('Late local/runtime source contracts failed:\n- '+'\n- '.join(fail))
 print('Late local/runtime contracts: PASS -> BigMap side=4, Belt local template, AutoPath runtime-only x2')
if __name__=='__main__':main()
