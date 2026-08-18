#!/usr/bin/env python3
"""Inventory source constructor loops that materialise controls at runtime.

This catches the class of importer gap previously seen in MagicBar, AutoPotion,
FilterDrop, Ranking and similar repeated UI structures. The inventory is source-
backed and intentionally distinguishes deterministic loop bounds from runtime
collection loops; it does not fabricate the controls.
"""
from __future__ import annotations
import argparse,json,re
from collections import Counter
from pathlib import Path

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
    m=re.search(rf'\b{re.escape(str(name))}\s*\([^)]*\)\s*\{{',body)
    if not m:return ''
    o=body.find('{',m.start());return body[o+1:match_brace(body,o)]

def main():
    p=argparse.ArgumentParser();p.add_argument('--spec',type=Path,required=True);p.add_argument('--zircon-root',type=Path,required=True);a=p.parse_args();spec=json.loads(a.spec.read_text(encoding='utf-8'))
    rows=[]
    loop_re=re.compile(r'\b(for|foreach)\s*\(([^)]*)\)\s*\{')
    new_re=re.compile(r'\bnew\s+([A-Za-z_][A-Za-z0-9_]*)\b')
    for w in [*(spec.get('windows') or []),*(spec.get('nestedWindows') or [])]:
        path=a.zircon_root/str(w.get('sourcePath') or '');name=w.get('class') or w.get('sourceClass')
        if not path.exists() or not name:continue
        body=class_body(path.read_text(encoding='utf-8-sig'),name);ctor=constructor_body(body,name)
        for m in loop_re.finditer(ctor):
            opening=ctor.find('{',m.start());closing=match_brace(ctor,opening);chunk=ctor[opening+1:closing];created=sorted(set(new_re.findall(chunk)))
            controlish=[x for x in created if x.startswith('DX') or x.endswith(('Row','Line','Control','Dialog','Panel'))]
            if not controlish:continue
            header=' '.join(m.group(2).split());runtime=bool(re.search(r'GameScene|MapObject|\.Binding|\.Currencies|\.Members|\.Buffs|\.Quest|\.Items|\.Count\b(?!\s*[<>]=?\s*\d)',header))
            literal=bool(re.search(r'\b[<>]=?\s*\d+\b',header)) or 'Length' in header
            rows.append({'id':w.get('id'),'field':w.get('field'),'sourceClass':name,'loopType':m.group(1),'header':header[:300],'createdTypes':controlish,'runtimeCollectionLikely':runtime,'deterministicBoundLikely':literal and not runtime})
    counts=Counter('runtime' if r['runtimeCollectionLikely'] else 'deterministic' if r['deterministicBoundLikely'] else 'review' for r in rows)
    spec['constructorLoopInventory']={'loopCount':len(rows),'classificationCounts':dict(counts),'rows':rows,'sourceBackedOnly':True,'controlsFabricatedByAudit':False}
    a.spec.write_text(json.dumps(spec,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print('Constructor control-loop inventory:',len(rows),dict(counts))
if __name__=='__main__':main()
