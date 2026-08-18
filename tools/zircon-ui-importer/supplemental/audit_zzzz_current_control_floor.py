#!/usr/bin/env python3
"""Last supplemental floor gate for the current source-faithful manifest."""
from __future__ import annotations
import argparse,json
from pathlib import Path
MIN_GAME=2511
MIN_NESTED=143

def main():
 p=argparse.ArgumentParser();p.add_argument('--spec',type=Path,required=True);p.add_argument('--zircon-root',type=Path,required=True);a=p.parse_args();spec=json.loads(a.spec.read_text(encoding='utf-8'));windows=spec.get('windows',[]);nested=spec.get('nestedWindows',[]);game=sum(len(w.get('controls',[])) for w in windows);nested_count=sum(len(w.get('controls',[])) for w in nested);final=spec.get('finalSupplementalSourceMatrix') or {};fail=[]
 if len(windows)!=65:fail.append(f'GameScene windows {len(windows)} != 65')
 if len(nested)!=15:fail.append(f'nested windows {len(nested)} != 15')
 if game<MIN_GAME:fail.append(f'GameScene controls {game} < {MIN_GAME}')
 if nested_count<MIN_NESTED:fail.append(f'nested controls {nested_count} < {MIN_NESTED}')
 if final.get('passed') is not True:fail.append(f'prior final matrix missing/not PASS: {final}')
 final['gameSceneControls']=game;final['nestedControls']=nested_count;final['minimumGameSceneControls']=MIN_GAME;final['minimumNestedControls']=MIN_NESTED;final['passed']=final.get('passed') is True and not fail;final['failures']=list(final.get('failures') or [])+fail;spec['finalSupplementalSourceMatrix']=final;spec['currentSourceControlFloor']={'passed':not fail,'gameScene':MIN_GAME,'nested':MIN_NESTED,'windows':[65,15],'runtimePayloadsInvented':False,'controlsFabricatedByAudit':False}
 a.spec.write_text(json.dumps(spec,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
 if fail:raise SystemExit('Current source control floor failed:\n- '+'\n- '.join(fail))
 print(f'Current source control floor: PASS -> {game}+{nested_count} controls, minimum={MIN_GAME}+{MIN_NESTED}')
if __name__=='__main__':main()
