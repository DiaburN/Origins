#!/usr/bin/env python3
"""Final bridge for exact-SHA Browser QA workflow guarantees."""
from __future__ import annotations
import argparse,json
from pathlib import Path

def main():
 p=argparse.ArgumentParser();p.add_argument('--spec',type=Path,required=True);p.add_argument('--zircon-root',type=Path,required=True);a=p.parse_args();spec=json.loads(a.spec.read_text(encoding='utf-8'));final=spec.get('finalSupplementalSourceMatrix') or {};qa=spec.get('browserQaWorkflowAudit') or {};fail=[]
 if final.get('passed') is not True:fail.append(f'prior final matrix missing/not PASS: {final}')
 expected={'passed':True,'exactShaBuildArtifactRequired':True,'artifactName':'zircon-ui-reference-complete','expectedWindows':80,'sourceGameFloor':2511,'nestedFloor':143,'priorBrowserCheckpoint':2507,'checkpointPromotionPendingUntilPass':True,'bigMapSidePanelContractRequired':True,'failureEvidenceUploaded':True,'runtimePayloadsInvented':False}
 for key,value in expected.items():
  if qa.get(key)!=value:fail.append(f'Browser QA workflow contract drifted: {key}={qa.get(key)!r}, expected {value!r}')
 final['browserQaWorkflowPassed']=qa.get('passed') is True;final['browserQaExactShaArtifact']=qa.get('exactShaBuildArtifactRequired');final['browserQaExpectedWindows']=qa.get('expectedWindows');final['browserQaSourceGameFloor']=qa.get('sourceGameFloor');final['browserQaPriorCheckpoint']=qa.get('priorBrowserCheckpoint');final['passed']=final.get('passed') is True and not fail;final['failures']=list(final.get('failures') or [])+fail;spec['finalSupplementalSourceMatrix']=final
 a.spec.write_text(json.dumps(spec,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
 if fail:raise SystemExit('Final Browser QA workflow contract failed:\n- '+'\n- '.join(fail))
 print('Final Browser QA workflow: PASS -> exact SHA artifact, 80 windows, 2511 pending promotion until Chrome PASS')
if __name__=='__main__':main()
