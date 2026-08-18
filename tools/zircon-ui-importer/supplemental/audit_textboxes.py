#!/usr/bin/env python3
"""Strict shared DXTextBox / DXNumberTextBox source contract."""
from __future__ import annotations
import argparse,json
from pathlib import Path

def req(text,needle,label):
    if needle not in text:raise SystemExit(f'TextBox source contract changed: {label}: missing {needle!r}')

def main():
    p=argparse.ArgumentParser();p.add_argument('--spec',type=Path,required=True);p.add_argument('--zircon-root',type=Path,required=True);a=p.parse_args();spec=json.loads(a.spec.read_text(encoding='utf-8'))
    src=(a.zircon_root/'Client/Controls/DXTextBox.cs').read_text(encoding='utf-8-sig')
    for needle,label in (('public int MaxLength','MaxLength property'),('public bool ReadOnly','ReadOnly property'),('public bool KeepFocus','KeepFocus property'),('public bool Multiline','Multiline property'),('TextBox.TextChanged','text-change bridge')):req(src,needle,label)
    controls=[c for w in [*(spec.get('windows') or []),*(spec.get('nestedWindows') or [])] for c in w.get('controls',[]) if c.get('type') in ('DXTextBox','DXNumberTextBox')]
    if not controls:raise SystemExit('No DXTextBox/DXNumberTextBox controls in source inventory')
    spec['textBoxSourceAudit']={'passed':True,'controlCount':len(controls),'sourceTypes':sorted({c.get('type') for c in controls}),'runtimeValidationInvented':False}
    a.spec.write_text(json.dumps(spec,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(f'TextBox source contract: PASS ({len(controls)} text controls)')
if __name__=='__main__':main()
