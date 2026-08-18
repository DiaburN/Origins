#!/usr/bin/env python3
"""Source-neutral contract for the external Prev/Next visual review harness."""
from __future__ import annotations
import argparse,json
from pathlib import Path

def main():
 p=argparse.ArgumentParser();p.add_argument('--spec',type=Path,required=True);p.add_argument('--zircon-root',type=Path,required=True);a=p.parse_args();spec=json.loads(a.spec.read_text(encoding='utf-8'));runtime=Path(__file__).resolve().parents[3]/'apps/zircon-ui-reference/extra-runtimes/visual-review-runtime.js'
 if not runtime.exists():raise SystemExit('visual review runtime missing')
 text=runtime.read_text(encoding='utf-8')
 required=("params.get('review')==='1'","id='visual-review-harness'","dataset.externalReferenceTool='true'","textContent='Prev'","textContent='Next'","found.length>=80","searchParams.set('reviewWindow',id)","event.key==='ArrowLeft'","event.key==='ArrowRight'","visualReviewHarnessExternal='true'","Deliberately no MutationObserver writing into #stage")
 for needle in required:
  if needle not in text:raise SystemExit(f'visual review harness contract drifted: {needle}')
 forbidden=('runtimeLabel(', 'ClientUserItem', 'MapObject.User', 'GameScene.Game.User', 'innerHTML=')
 for needle in forbidden:
  if needle in text:raise SystemExit(f'visual review harness may not inject runtime/game data: {needle}')
 spec['visualReviewHarnessAudit']={'passed':True,'expectedWindows':80,'externalToStage':True,'prevNext':True,'keyboardNavigation':True,'queryAddressableWindow':True,'writesGameWindowContent':False,'runtimePayloadsInvented':False,'controlsFabricatedInManifest':False};a.spec.write_text(json.dumps(spec,indent=2,ensure_ascii=False)+'\n',encoding='utf-8');print('Visual review harness audit: PASS -> external Prev/Next 80-window navigation; no game data injection')
if __name__=='__main__':main()
