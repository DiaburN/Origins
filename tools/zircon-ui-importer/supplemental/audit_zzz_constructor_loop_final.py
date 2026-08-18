#!/usr/bin/env python3
"""Last-pass guard tying constructor-loop coverage into the final matrix."""
from __future__ import annotations
import argparse,json
from pathlib import Path

def main():
 p=argparse.ArgumentParser();p.add_argument('--spec',type=Path,required=True);p.add_argument('--zircon-root',type=Path,required=True);a=p.parse_args();spec=json.loads(a.spec.read_text(encoding='utf-8'))
 loop=spec.get('constructorLoopInventory') or {};custom=spec.get('customConstructorLoopInventory') or {};final=spec.get('finalSupplementalSourceMatrix') or {};fail=[]
 if final.get('passed') is not True:fail.append(f'prior final supplemental matrix missing/not PASS: {final}')
 if loop.get('passed') is not True or loop.get('version')!=2:fail.append(f'constructor loop inventory missing/not v2 PASS: {loop}')
 if loop.get('unexpectedDeterministicLoops')!=[]:fail.append(f'uncovered deterministic constructor loops remain: {loop.get("unexpectedDeterministicLoops")}')
 if loop.get('controlsFabricatedByAudit') is not False or loop.get('runtimePayloadsInvented') is not False:fail.append(f'constructor loop audit boundary broken: {loop}')
 if custom.get('passed') is not True or custom.get('version')!=1:fail.append(f'custom constructor loop inventory missing/not v1 PASS: {custom}')
 if custom.get('unexpectedDeterministicLoops')!=[]:fail.append(f'uncovered deterministic custom-constructor loops remain: {custom.get("unexpectedDeterministicLoops")}')
 if custom.get('controlsFabricatedByAudit') is not False or custom.get('runtimePayloadsInvented') is not False:fail.append(f'custom constructor loop audit boundary broken: {custom}')
 final['constructorLoopInventoryVersion']=loop.get('version');final['constructorControlLoops']=loop.get('loopCount');final['constructorLoopClassifications']=loop.get('classificationCounts');final['unexpectedDeterministicConstructorLoops']=len(loop.get('unexpectedDeterministicLoops') or []);final['customConstructorLoopInventoryVersion']=custom.get('version');final['customConstructorControlLoops']=custom.get('loopCount');final['customConstructorLoopClassifications']=custom.get('classificationCounts');final['unexpectedDeterministicCustomConstructorLoops']=len(custom.get('unexpectedDeterministicLoops') or []);final['passed']=not fail and final.get('passed') is True;final['failures']=list(final.get('failures') or [])+fail;spec['finalSupplementalSourceMatrix']=final
 a.spec.write_text(json.dumps(spec,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
 if fail:raise SystemExit('Final constructor-loop coverage failed:\n- '+'\n- '.join(fail))
 print(f'Final constructor-loop coverage: PASS -> windowLoops={loop.get("loopCount")}, customLoops={custom.get("loopCount")}, unexpected deterministic=0')
if __name__=='__main__':main()
