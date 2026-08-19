#!/usr/bin/env python3
"""Last-pass bridge for the external 80-window visual review harness."""
from __future__ import annotations
import argparse,json
from pathlib import Path

def main():
 p=argparse.ArgumentParser();p.add_argument('--spec',type=Path,required=True);p.add_argument('--zircon-root',type=Path,required=True);a=p.parse_args();spec=json.loads(a.spec.read_text(encoding='utf-8'));final=spec.get('finalSupplementalSourceMatrix') or {};review=spec.get('visualReviewHarnessAudit') or {};fail=[]
 if final.get('passed') is not True:fail.append(f'prior final matrix missing/not PASS: {final}')
 expected={'passed':True,'expectedWindows':80,'externalToStage':True,'prevNext':True,'keyboardNavigation':True,'queryAddressableWindow':True,'writesGameWindowContent':False,'runtimePayloadsInvented':False,'controlsFabricatedInManifest':False}
 for key,value in expected.items():
  if review.get(key)!=value:fail.append(f'visual review harness contract drifted: {key}={review.get(key)!r}, expected {value!r}')
 final['visualReviewHarnessPassed']=review.get('passed') is True;final['visualReviewExpectedWindows']=review.get('expectedWindows');final['visualReviewExternalToStage']=review.get('externalToStage');final['visualReviewWritesGameWindowContent']=review.get('writesGameWindowContent');final['passed']=final.get('passed') is True and not fail;final['failures']=list(final.get('failures') or [])+fail;spec['finalSupplementalSourceMatrix']=final
 a.spec.write_text(json.dumps(spec,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
 if fail:raise SystemExit('Final visual review harness contract failed:\n- '+'\n- '.join(fail))
 print('Final visual review harness: PASS -> Prev/Next 80 windows; external-only, zero runtime payloads')
if __name__=='__main__':main()
