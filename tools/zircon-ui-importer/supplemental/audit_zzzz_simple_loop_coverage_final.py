#!/usr/bin/env python3
"""Last-pass guard for mechanically provable literal constructor loops."""
from __future__ import annotations
import argparse,json
from pathlib import Path

def main():
    p=argparse.ArgumentParser();p.add_argument('--spec',type=Path,required=True);p.add_argument('--zircon-root',type=Path,required=True);a=p.parse_args()
    spec=json.loads(a.spec.read_text(encoding='utf-8'));final=spec.get('finalSupplementalSourceMatrix') or {};coverage=spec.get('constructorLoopCoverageAudit') or {};fail=[]
    if final.get('passed') is not True:fail.append(f'prior final supplemental matrix missing/not PASS: {final}')
    if coverage.get('passed') is not True or coverage.get('version')!=2:fail.append(f'simple constructor-loop coverage missing/not v2 PASS: {coverage}')
    if coverage.get('uncoveredSimpleLiteralLoops')!=0:fail.append(f'uncovered simple literal constructor loops remain: {coverage.get("strictRows")}')
    if coverage.get('sourceBackedOnly') is not True or coverage.get('controlsFabricatedByAudit') is not False or coverage.get('runtimePayloadsInvented') is not False:fail.append(f'simple loop audit boundary broken: {coverage}')
    final['simpleConstructorLoopCoverageVersion']=coverage.get('version');final['strictSimpleLiteralConstructorLoops']=coverage.get('strictSimpleLiteralLoops');final['reviewConstructorLoops']=coverage.get('reviewLoops');final['runtimeConstructorLoops']=coverage.get('runtimeLoops');final['uncoveredSimpleLiteralConstructorLoops']=coverage.get('uncoveredSimpleLiteralLoops');final['passed']=not fail and final.get('passed') is True;final['failures']=list(final.get('failures') or [])+fail;spec['finalSupplementalSourceMatrix']=final
    a.spec.write_text(json.dumps(spec,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    if fail:raise SystemExit('Final simple constructor-loop coverage failed:\n- '+'\n- '.join(fail))
    print(f'Final simple constructor-loop coverage: PASS -> strict={coverage.get("strictSimpleLiteralLoops")}, uncovered=0')
if __name__=='__main__':main()
