#!/usr/bin/env python3
"""Strict shared DXV/DXH scrollbar source contract."""
from __future__ import annotations
import argparse,json
from pathlib import Path

def req(text,needle,label):
    if needle not in text: raise SystemExit(f'Scrollbar source contract changed: {label}: missing {needle!r}')

def main():
    p=argparse.ArgumentParser();p.add_argument('--spec',type=Path,required=True);p.add_argument('--zircon-root',type=Path,required=True);a=p.parse_args();spec=json.loads(a.spec.read_text(encoding='utf-8'))
    vpath=a.zircon_root/'Client/Controls/DXVScrollBar.cs';hpath=a.zircon_root/'Client/Controls/DXHScrollBar.cs'
    v=vpath.read_text(encoding='utf-8-sig');h=hpath.read_text(encoding='utf-8-sig')
    req(v,'public sealed class DXVScrollBar : DXControl','vertical class')
    req(h,'public sealed class DXHScrollBar : DXControl','horizontal class')
    for needle,label in (('private int ScrollHeight => Size.Height - 50;','vertical track formula'),('Index = 44,','vertical back/up art'),('Index = 46,','vertical forward/down art'),('Index = 45,','vertical thumb art')):req(v,needle,label)
    for needle,label in (('private int ScrollWidth => Size.Width - 50;','horizontal track formula'),('Index = 44,','horizontal back art'),('Index = 46,','horizontal forward art'),('Index = 45,','horizontal thumb art')):req(h,needle,label)
    shared=(('public int Change','Change field'),('public int MinValue','MinValue property'),('public int MaxValue','MaxValue property'),('public int Value','Value property'),('public int VisibleSize','VisibleSize property'),('public bool HideWhenNoScroll','HideWhenNoScroll property'))
    for text,axis in ((v,'vertical'),(h,'horizontal')):
        for needle,label in shared:req(text,needle,f'{axis} {label}')
    controls=[c for w in [*(spec.get('windows') or []),*(spec.get('nestedWindows') or [])] for c in w.get('controls',[]) if c.get('type') in ('DXVScrollBar','DXHScrollBar')]
    if not controls:raise SystemExit('No DXV/DXH scrollbars in final source inventory')
    spec['scrollbarSourceAudit']={'passed':True,'controlCount':len(controls),'trackPadding':50,'sourceBackIndex':44,'sourceForwardIndex':46,'sourceThumbIndex':45,'verticalSourcePath':'Client/Controls/DXVScrollBar.cs','horizontalSourcePath':'Client/Controls/DXHScrollBar.cs','sharedBaseClassFileRequired':False,'runtimeValuesInvented':False}
    a.spec.write_text(json.dumps(spec,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(f'Scrollbar source contract: PASS ({len(controls)} DXV/DXH controls; current Zircon split classes)')
if __name__=='__main__':main()
