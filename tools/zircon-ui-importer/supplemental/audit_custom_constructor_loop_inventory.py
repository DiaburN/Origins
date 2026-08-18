#!/usr/bin/env python3
"""Gate deterministic control loops inside custom DX-derived composite constructors.

GameStore's fixed custom-control loops are accepted only when their exact source
signature matches and the already-materialised deterministic GameStore contract
proves the corresponding 10 item rows / 5 top rows / quantity options. Any new
or changed deterministic custom-constructor loop remains a hard failure.
"""
from __future__ import annotations
import argparse,json,re
from collections import Counter
from pathlib import Path

CLASS_RE=re.compile(r'\bclass\s+([A-Za-z_][A-Za-z0-9_]*)\s*:\s*([A-Za-z_][A-Za-z0-9_]*)')


def store_window_contract(spec):
    w=next((x for x in spec.get('windows',[]) if x.get('field')=='GameStoreBox'),None)
    return (w or {}).get('deterministicGameStoreComposites') or {}


def protected_loop(spec,type_name,header,created_controls):
    contract=store_window_contract(spec)
    base=(
        contract.get('passed') is True
        and contract.get('controlsAdded')==215
        and contract.get('runtimeStoreInfoInvented') is False
        and contract.get('runtimeItemsInvented') is False
    )
    if not base:
        return False
    if type_name=='GameStoreItemListControl':
        return (
            header=='int i = 0; i < Rows.Length; i++'
            and created_controls==['GameStoreItem']
            and contract.get('itemRows')==10
            and contract.get('itemRowsVisible') is False
        )
    if type_name=='GameStoreTopItemsControl':
        return (
            header=='int i = 0; i < Rows.Length; i++'
            and created_controls==['GameStoreTopItemControl']
            and contract.get('topRows')==5
        )
    if type_name=='GameStoreItem':
        return (
            header=='int i = 1; i <= 10; i++'
            and created_controls==['DXListBoxItem']
            and contract.get('quantityOptionsPerRow')==10
        )
    return False

PROTECTED={'GameStoreItemListControl','GameStoreTopItemsControl','GameStoreItem'}


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
    m=re.search(rf'\bclass\s+{re.escape(name)}\b[^{{]*\{{',text)
    if not m:return ''
    o=text.find('{',m.start());return text[o+1:match_brace(text,o)]


def ctor(body,name):
    m=re.search(rf'\b{re.escape(name)}\s*\([^)]*\)\s*(?::\s*[^{{]+)?\{{',body)
    if not m:return ''
    o=body.find('{',m.start());return body[o+1:match_brace(body,o)]


def build_index(root):
    bases={};paths={}
    for path in (root/'Client').rglob('*.cs'):
        try:text=path.read_text(encoding='utf-8-sig')
        except UnicodeDecodeError:continue
        for name,base in CLASS_RE.findall(text):bases[name]=base;paths[name]=path
    return bases,paths


def derives(name,bases):
    seen=set();cur=name
    while cur and cur not in seen:
        if cur in {'DXControl','DXWindow','DXTab','DXImageControl'}:return True
        seen.add(cur);cur=bases.get(cur,'')
    return False


def main():
    p=argparse.ArgumentParser();p.add_argument('--spec',type=Path,required=True);p.add_argument('--zircon-root',type=Path,required=True);a=p.parse_args();spec=json.loads(a.spec.read_text(encoding='utf-8'));bases,paths=build_index(a.zircon_root)
    custom_types=sorted({str(c.get('sourceType')) for w in [*(spec.get('windows') or []),*(spec.get('nestedWindows') or [])] for c in w.get('controls',[]) if c.get('sourceType') and not str(c.get('sourceType')).startswith('DX') and str(c.get('sourceType')) in bases and derives(str(c.get('sourceType')),bases)})
    loop_re=re.compile(r'\b(for|foreach)\s*\(([^)]*)\)\s*\{');new_re=re.compile(r'\bnew\s+([A-Za-z_][A-Za-z0-9_]*)\b');rows=[];unexpected=[]
    for type_name in custom_types:
        path=paths.get(type_name)
        if not path:continue
        source=path.read_text(encoding='utf-8-sig');body=class_body(source,type_name);constructor=ctor(body,type_name)
        for m in loop_re.finditer(constructor):
            opening=constructor.find('{',m.start());closing=match_brace(constructor,opening);chunk=constructor[opening+1:closing];created=sorted(set(new_re.findall(chunk)));created_controls=[x for x in created if x.startswith('DX') or (x in bases and derives(x,bases))]
            if not created_controls:continue
            header=' '.join(m.group(2).split());runtime=bool(re.search(r'GameScene|MapObject|\.Binding|\.Count\b(?!\s*[<>]=?\s*\d)|StoreInfo|QuestInfo|HelpInfo|Currency|Members|Buffs',header));literal=bool(re.search(r'\b[<>]=?\s*\d+\b',header)) or 'Length' in header;deterministic=literal and not runtime;protected=bool(deterministic and type_name in PROTECTED and protected_loop(spec,type_name,header,created_controls));row={'sourceType':type_name,'sourcePath':path.relative_to(a.zircon_root).as_posix(),'loopType':m.group(1),'header':header[:300],'createdTypes':created_controls,'runtimeCollectionLikely':runtime,'deterministicBoundLikely':deterministic,'protectedDeterministic':protected};rows.append(row)
            if deterministic and not protected:unexpected.append(row)
    counts=Counter('runtime' if r['runtimeCollectionLikely'] else 'deterministic' if r['deterministicBoundLikely'] else 'review' for r in rows);report={'passed':not unexpected,'version':2,'customTypesScanned':len(custom_types),'loopCount':len(rows),'classificationCounts':dict(counts),'protectedCustomTypes':sorted(PROTECTED),'gameStoreContractRequired':{'controlsAdded':215,'itemRows':10,'topRows':5,'quantityOptionsPerRow':10},'exactLoopSignaturesRequired':True,'unexpectedDeterministicLoops':unexpected,'controlsFabricatedByAudit':False,'runtimePayloadsInvented':False,'rows':rows};spec['customConstructorLoopInventory']=report;a.spec.write_text(json.dumps(spec,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    if unexpected:raise SystemExit('Uncovered deterministic custom-constructor loops:\n'+json.dumps(unexpected,indent=2,ensure_ascii=False))
    print(f'Custom constructor-loop inventory v2: PASS -> types={len(custom_types)} loops={len(rows)} unexpected=0; GameStore 10+5+quantity exact signatures protected')

if __name__=='__main__':main()
