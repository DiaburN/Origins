#!/usr/bin/env python3
"""Late final bridge for exact-SHA Browser QA commit-status evidence."""
from __future__ import annotations
import argparse,json
from pathlib import Path

def main():
 p=argparse.ArgumentParser();p.add_argument('--spec',type=Path,required=True);p.add_argument('--zircon-root',type=Path,required=True);a=p.parse_args();spec=json.loads(a.spec.read_text(encoding='utf-8'));final=spec.get('finalSupplementalSourceMatrix') or {};audit=spec.get('browserQaStatusPublisherAudit') or {};fail=[]
 if final.get('passed') is not True:fail.append(f'prior final matrix missing/not PASS: {final}')
 expected={'passed':True,'trigger':'Browser QA Zircon UI reference completed','branch':'origins-game-v1','statusPermissionWrite':True,'exactHeadSha':True,'context':'origins/zircon-browser-qa','successMapsToSuccess':True,'nonSuccessMapsToFailure':True,'targetUrlIsWorkflowRun':True,'mutatesSourceContracts':False,'runtimePayloadsInvented':False,'controlsAdded':0}
 for key,value in expected.items():
  if audit.get(key)!=value:fail.append(f'Browser QA status publisher drifted: {key}={audit.get(key)!r}, expected {value!r}')
 final['browserQaStatusPublisherPassed']=audit.get('passed') is True;final['browserQaStatusContext']=audit.get('context');final['browserQaStatusExactHeadSha']=audit.get('exactHeadSha') is True;final['browserQaStatusMutatesSourceContracts']=False;final['browserQaStatusControlsAdded']=0;final['passed']=final.get('passed') is True and not fail;final['failures']=list(final.get('failures') or [])+fail;spec['finalSupplementalSourceMatrix']=final
 a.spec.write_text(json.dumps(spec,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
 if fail:raise SystemExit('Final Browser QA status publisher contract failed:\n- '+'\n- '.join(fail))
 print('Final Browser QA status publisher: PASS -> exact-SHA CI evidence readable as commit status; source floor remains pending until success')
if __name__=='__main__':main()
