#!/usr/bin/env python3
"""Expand DXColourControlPair composite children in DXConfigWindow."""
from __future__ import annotations
import argparse,json
from pathlib import Path

PAIR_NAMES=[
    'TargetColourControl','LocalColourBox','WhisperInColourBox','WhisperOutColourBox',
    'GroupColourBox','GuildColourBox','ShoutColourBox','GlobalColourBox',
    'ObserverColourBox','HintColourBox','SystemColourBox','GainsColourBox','AnnouncementColourBox',
]

def child(pair,name,x):
    return {'name':f'{pair}__{name}','type':'DXColourControl','properties':{'Parent':pair,'Location':f'new Point({x}, 0)','Size':'new Size(20, 16)'},'sourceGenerated':'DXColourControlPair constructor'}

def main():
    p=argparse.ArgumentParser();p.add_argument('--spec',type=Path,required=True);a=p.parse_args();spec=json.loads(a.spec.read_text(encoding='utf-8'))
    w=next((x for x in spec.get('windows',[]) if x.get('field')=='ConfigBox'),None)
    if not w:raise SystemExit('ConfigBox missing from manifest')
    controls=[c for c in w.get('controls',[]) if '__ForeColourControl' not in str(c.get('name','')) and '__BackColourControl' not in str(c.get('name',''))]
    by={c.get('name'):c for c in controls};missing=[name for name in PAIR_NAMES if name not in by]
    if missing:raise SystemExit(f'DXColourControlPair source controls missing from Config manifest: {missing}')
    generated=[]
    for name in PAIR_NAMES:
        pair=by[name];pair.setdefault('sourceType',pair.get('type'));pair['type']='DXControl';pair.setdefault('properties',{})['Size']='new Size(40, 16)';pair['sourceComposite']='DXColourControlPair'
        generated.extend([child(name,'ForeColourControl',0),child(name,'BackColourControl',20)])
    w['controls']=generated+controls
    w['colourPairSourcePass']={'pairCount':len(PAIR_NAMES),'generatedSwatchCount':len(generated),'pairSize':[40,16],'swatchSize':[20,16],'runtimeColoursInvented':False}
    if len(generated)!=26:raise SystemExit(f'Colour pair expansion drifted: {len(generated)}')
    a.spec.write_text(json.dumps(spec,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print('DXColourControlPair source composites expanded: 13 pairs / 26 swatches')
if __name__=='__main__':main()
