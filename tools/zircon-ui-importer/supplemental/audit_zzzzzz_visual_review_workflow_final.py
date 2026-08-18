#!/usr/bin/env python3
"""Final bridge for exact-SHA 80-window visual evidence generation."""
from __future__ import annotations
import argparse,json
from pathlib import Path

def main():
 p=argparse.ArgumentParser();p.add_argument('--spec',type=Path,required=True);p.add_argument('--zircon-root',type=Path,required=True);a=p.parse_args();spec=json.loads(a.spec.read_text(encoding='utf-8'));final=spec.get('finalSupplementalSourceMatrix') or {};workflow=spec.get('visualReviewWorkflowAudit') or {};fail=[]
 if final.get('passed') is not True:fail.append(f'prior final matrix missing/not PASS: {final}')
 expected={'passed':True,'exactShaBuildRequired':True,'exactShaBrowserQaRequired':True,'expectedWindows':80,'expectedScreenshots':80,'domTargetValidation':True,'offlineIndex':True,'concurrencyCancelsStaleRuns':True,'failureEvidenceUploaded':True,'sourceFloor':2511,'nestedFloor':143,'runtimePayloadsInvented':False,'gameWindowContentInvented':False}
 for key,value in expected.items():
  if workflow.get(key)!=value:fail.append(f'visual evidence workflow drifted: {key}={workflow.get(key)!r}, expected {value!r}')
 final['visualReviewWorkflowPassed']=workflow.get('passed') is True;final['visualReviewExpectedScreenshots']=workflow.get('expectedScreenshots');final['visualReviewRequiresExactShaBrowserQa']=workflow.get('exactShaBrowserQaRequired');final['visualReviewRequiresExactShaBuild']=workflow.get('exactShaBuildRequired');final['visualReviewFailureEvidenceUploaded']=workflow.get('failureEvidenceUploaded') is True;final['passed']=final.get('passed') is True and not fail;final['failures']=list(final.get('failures') or [])+fail;spec['finalSupplementalSourceMatrix']=final
 a.spec.write_text(json.dumps(spec,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
 if fail:raise SystemExit('Final visual evidence workflow contract failed:\n- '+'\n- '.join(fail))
 print('Final visual evidence workflow: PASS -> exact SHA build + Browser QA + 80 validated screenshots + retained failure evidence')
if __name__=='__main__':main()
