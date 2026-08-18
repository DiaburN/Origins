#!/usr/bin/env python3
"""Require every constructor-reachable deterministic UI helper to be materialized."""
from __future__ import annotations
import argparse,json
from pathlib import Path

def main():
 p=argparse.ArgumentParser();p.add_argument('--spec',type=Path,required=True);p.add_argument('--zircon-root',type=Path,required=True);a=p.parse_args();spec=json.loads(a.spec.read_text(encoding='utf-8'))
 inv=spec.get('uiCreationHelperInventory') or {};rows=inv.get('rows') or [];final=spec.get('finalSupplementalSourceMatrix') or {};missing=[]
 if inv.get('passed') is not True or inv.get('version')!=2:missing.append({'issue':'uiCreationHelperInventory missing/not v2 PASS','inventory':inv})
 for row in rows:
  if row.get('constructorReachable') is True and row.get('classification')=='deterministic-source' and row.get('status')!='materialized':
   missing.append({'field':row.get('field'),'sourceClass':row.get('sourceClass'),'helper':row.get('helper'),'depth':row.get('constructorReachDepth'),'createdTypes':row.get('createdTypes'),'namedCreations':row.get('namedCreations'),'status':row.get('status')})
 report={'passed':not missing,'deterministicConstructorHelpers':sum(1 for r in rows if r.get('constructorReachable') is True and r.get('classification')=='deterministic-source'),'unmaterializedDeterministicHelpers':missing,'allDeterministicConstructorHelpersMaterialized':not missing,'controlsFabricatedByAudit':False,'runtimePayloadsInvented':False};spec['deterministicHelperMaterializationAudit']=report
 if final:
  final['deterministicConstructorHelpers']=report['deterministicConstructorHelpers'];final['unmaterializedDeterministicHelpers']=len(missing);final['passed']=final.get('passed') is True and not missing
  if missing:final['failures']=list(final.get('failures') or [])+[f'unmaterialized deterministic helpers: {missing}']
  spec['finalSupplementalSourceMatrix']=final
 a.spec.write_text(json.dumps(spec,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
 if missing:raise SystemExit('Deterministic constructor helpers not materialized:\n'+json.dumps(missing,indent=2,ensure_ascii=False))
 print(f'Deterministic helper materialization: PASS ({report["deterministicConstructorHelpers"]} helpers, 0 source-only)')
if __name__=='__main__':main()
