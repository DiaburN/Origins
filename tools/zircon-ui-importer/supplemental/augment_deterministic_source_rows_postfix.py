#!/usr/bin/env python3
"""Apply exact post-expansion FortuneCheckerRow constructor details."""
from __future__ import annotations
import argparse,json
from pathlib import Path

def main():
    p=argparse.ArgumentParser();p.add_argument('--spec',type=Path,required=True);p.add_argument('--zircon-root',type=Path,required=True);a=p.parse_args()
    spec=json.loads(a.spec.read_text(encoding='utf-8'))
    w=next((x for x in spec.get('windows',[]) if x.get('field')=='FortuneCheckerBox'),None)
    if not w: raise SystemExit('FortuneCheckerBox missing')
    by={c.get('name'):c for c in w.get('controls',[])}
    for i in range(1,10):
        row=f'FortuneRowSource{i:02d}'
        cell=by.get(f'{row}ItemCell');name=by.get(f'{row}NameLabel');check=by.get(f'{row}CheckButton')
        if not all((cell,name,check)): raise SystemExit(f'Fortune deterministic row incomplete: {row}')
        cell['properties']['Location']='new Point(9, 9)'
        name['properties']['Location']='new Point(45, 22)'
        check['properties']['Enabled']='true'
    w.setdefault('deterministicFortuneRows',{})['exactIntegerCellLocation']=[9,9]
    w['deterministicFortuneRows']['checkButtonConstructorEnabled']=True
    a.spec.write_text(json.dumps(spec,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print('Fortune deterministic rows corrected to exact integer constructor geometry/state')
if __name__=='__main__':main()
