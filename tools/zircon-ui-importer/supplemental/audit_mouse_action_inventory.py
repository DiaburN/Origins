#!/usr/bin/env python3
"""Inventory/classify source MouseClick handlers across all reconstructed windows.

This is intentionally an inventory, not a claim that every action is browser-
executable. It distinguishes source-local actions from server/runtime effects so
later fidelity passes can prioritize real missing behavior without fabrication.
"""
from __future__ import annotations
import argparse,json,re
from collections import Counter
from pathlib import Path


def matching(text,opening):
    depth=0;quote=None;escape=False;i=opening
    while i<len(text):
        c=text[i]
        if quote:
            if escape:escape=False
            elif c=='\\':escape=True
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
    o=text.find('{',m.start());return text[o+1:matching(text,o)]

def handlers(body):
    pattern=re.compile(r'\b([A-Za-z_][A-Za-z0-9_]*)\.MouseClick\s*\+=\s*\([^)]*\)\s*=>\s*')
    out=[]
    for m in pattern.finditer(body):
        pos=m.end();control=m.group(1)
        while pos<len(body) and body[pos].isspace():pos+=1
        if pos<len(body) and body[pos]=='{':
            end=matching(body,pos);expr=body[pos+1:end];finish=end+1
        else:
            end=body.find(';',pos);end=len(body) if end<0 else end;expr=body[pos:end];finish=end+1
        out.append((control,' '.join(expr.split()),m.start(),finish))
    return out

def classify(expr):
    if 'CEnvir.Enqueue' in expr or 'new C.' in expr:return 'SERVER_PACKET'
    if 'RenderingPipelineManager.' in expr or 'CEnvir.Target.Close' in expr:return 'ENGINE_ACTION'
    if 'new DX' in expr and ('Window' in expr or 'MessageBox' in expr):return 'OPEN_MODAL'
    if re.search(r'GameScene\.Game\.[A-Za-z0-9_]+\.Visible\s*=',expr) or '.ToggleOpen(' in expr:return 'WINDOW_VISIBILITY'
    if 'Config.' in expr and '=' in expr:return 'LOCAL_CONFIG'
    if 'Dispose()' in expr or re.search(r'\bVisible\s*=\s*false',expr):return 'CLOSE_OR_HIDE'
    if '.InvokeMouseClick()' in expr:return 'DELEGATED_CLICK'
    if re.search(r'\b(SetActiveTab|Refresh|Clear|Sort|Select|Update|Populate|Build|Load|Save)[A-Za-z0-9_]*\s*\(',expr):return 'LOCAL_METHOD'
    if re.search(r'\b(Checked|Enabled|Value|Index|Text|Opacity|Expanded|Showing)\s*=',expr):return 'LOCAL_STATE'
    return 'OTHER_SOURCE_ACTION'

def main():
    p=argparse.ArgumentParser();p.add_argument('--spec',type=Path,required=True);p.add_argument('--zircon-root',type=Path,required=True);a=p.parse_args();spec=json.loads(a.spec.read_text(encoding='utf-8'))
    rows=[]
    for w in [*(spec.get('windows') or []),*(spec.get('nestedWindows') or [])]:
        path=a.zircon_root/str(w.get('sourcePath') or '');name=w.get('class') or w.get('sourceClass')
        if not path.exists() or not name:continue
        body=class_body(path.read_text(encoding='utf-8-sig'),str(name))
        for control,expr,_,__ in handlers(body):rows.append({'id':w.get('id'),'field':w.get('field'),'sourceClass':name,'control':control,'category':classify(expr),'sourceExpression':expr[:500]})
    counts=Counter(row['category'] for row in rows)
    spec['mouseActionInventory']={'handlerCount':len(rows),'categoryCounts':dict(sorted(counts.items())),'rows':rows,'sourceBackedOnly':True,'browserExecutionNotImplied':True}
    a.spec.write_text(json.dumps(spec,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print('MouseClick source inventory:',len(rows),dict(sorted(counts.items())))
if __name__=='__main__':main()
