#!/usr/bin/env python3
"""Inventory and gate direct constructor loops that create UI controls.

The flat C# initializer parser can see a loop body once while Zircon may create
many controls from that body. This audit classifies direct constructor loops as
runtime, deterministic, or review and requires every deterministic loop to have
source-backed materialisation evidence from a dedicated augmenter/contract.
It never creates controls and never promotes runtime collections.
"""
from __future__ import annotations
import argparse,json,re
from collections import Counter
from pathlib import Path

# Deterministic direct-constructor loop families already reconstructed by source
# passes. Each predicate checks metadata emitted by the authoritative augmenter.
PROTECTED={
 'AutoPotionBox':lambda w:(w.get('autoPotionSourceLoop') or {}).get('rowCount')==8,
 'FilterDropBox':lambda w:(w.get('filterDropSourceLoop') or {}).get('count')==10,
 'MagicBarBox':lambda w:(w.get('magicBarSourceLoop') or {}).get('slots')==24,
 'RankingBox':lambda w:(w.get('deterministicRankingRows') or {}).get('rankingRows')==11 and (w.get('deterministicRankingRows') or {}).get('searchRows')==1,
 'DungeonFinderBox':lambda w:(w.get('deterministicDungeonRows') or {}).get('rowCount')==9,
 'FortuneCheckerBox':lambda w:(w.get('deterministicFortuneRows') or {}).get('rowCount')==9,
 'CommunicationBox':lambda w:(w.get('deterministicReceivedMailRows') or {}).get('rowCount')==5,
 'GroupBox':lambda w:(w.get('deterministicGroupLFGRows') or {}).get('rowCount')==5,
 'NPCQuestListBox':lambda w:(w.get('deterministicNPCQuestRows') or {}).get('rows')==6,
}

def match_brace(text,o):
 depth=0;quote=None;esc=False;i=o
 while i<len(text):
  c=text[i]
  if quote:
   if esc:esc=False
   elif c=='\\':esc=True
   elif c==quote:quote=None
   i+=1;continue
  if c in ('"',"'"):quote=c;i+=1;continue
  if c=='{':depth+=1
  elif c=='}':
   depth-=1
   if depth==0:return i
  i+=1
 return len(text)-1

def class_body(text,name):
 m=re.search(rf'\bclass\s+{re.escape(str(name))}\b[^{{]*\{{',text)
 if not m:return ''
 o=text.find('{',m.start());return text[o+1:match_brace(text,o)]

def constructor_body(body,name):
 m=re.search(rf'\b{re.escape(str(name))}\s*\([^)]*\)\s*(?::\s*[^{{]+)?\{{',body)
 if not m:return ''
 o=body.find('{',m.start());return body[o+1:match_brace(body,o)]

def main():
 p=argparse.ArgumentParser();p.add_argument('--spec',type=Path,required=True);p.add_argument('--zircon-root',type=Path,required=True);a=p.parse_args();spec=json.loads(a.spec.read_text(encoding='utf-8'))
 rows=[];unexpected=[]
 loop_re=re.compile(r'\b(for|foreach)\s*\(([^)]*)\)\s*\{');new_re=re.compile(r'\bnew\s+([A-Za-z_][A-Za-z0-9_]*)\b')
 for w in [*(spec.get('windows') or []),*(spec.get('nestedWindows') or [])]:
  path=a.zircon_root/str(w.get('sourcePath') or '');name=w.get('class') or w.get('sourceClass')
  if not path.exists() or not name:continue
  body=class_body(path.read_text(encoding='utf-8-sig'),name);ctor=constructor_body(body,name)
  for m in loop_re.finditer(ctor):
   opening=ctor.find('{',m.start());closing=match_brace(ctor,opening);chunk=ctor[opening+1:closing];created=sorted(set(new_re.findall(chunk)))
   controlish=[x for x in created if x.startswith('DX') or x.endswith(('Row','Line','Control','Dialog','Panel'))]
   if not controlish:continue
   header=' '.join(m.group(2).split())
   runtime=bool(re.search(r'GameScene|MapObject|\.Binding|\.Currencies|\.Members|\.Buffs|\.Quest|\.Items|\.Count\b(?!\s*[<>]=?\s*\d)',header))
   literal=bool(re.search(r'\b[<>]=?\s*\d+\b',header)) or 'Length' in header
   deterministic=literal and not runtime
   field=str(w.get('field') or '')
   protected=False
   if deterministic and field in PROTECTED:
    try: protected=bool(PROTECTED[field](w))
    except Exception: protected=False
   row={'id':w.get('id'),'field':w.get('field'),'sourceClass':name,'loopType':m.group(1),'header':header[:300],'createdTypes':controlish,'runtimeCollectionLikely':runtime,'deterministicBoundLikely':deterministic,'protectedDeterministic':protected}
   rows.append(row)
   if deterministic and not protected:unexpected.append(row)
 counts=Counter('runtime' if r['runtimeCollectionLikely'] else 'deterministic' if r['deterministicBoundLikely'] else 'review' for r in rows)
 report={'passed':not unexpected,'version':2,'loopCount':len(rows),'classificationCounts':dict(counts),'protectedDeterministicFields':sorted(PROTECTED),'unexpectedDeterministicLoops':unexpected,'sourceBackedOnly':True,'controlsFabricatedByAudit':False,'runtimePayloadsInvented':False,'rows':rows}
 spec['constructorLoopInventory']=report;a.spec.write_text(json.dumps(spec,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
 if unexpected:
  detail='; '.join(f"{r.get('field')}:{r.get('header')} -> {','.join(r.get('createdTypes') or [])}" for r in unexpected)
  raise SystemExit('Uncovered deterministic constructor control loops: '+detail)
 print('Constructor control-loop inventory v2: PASS',len(rows),dict(counts),'unexpected=0')
if __name__=='__main__':main()
