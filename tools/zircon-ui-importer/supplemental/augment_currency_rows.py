#!/usr/bin/env python3
"""Compatibility gate for retired fixed Currency rows.

Current Zircon constructs one CurrencyTree. CurrencyTreeHeader/CurrencyItem are
runtime-created from the live user's currencies. This pass emits zero controls;
augment_currency_tree_shell.py owns the deterministic tree + scrollbar shell.
"""
from __future__ import annotations
import argparse,json
from pathlib import Path

def main():
    p=argparse.ArgumentParser();p.add_argument('--spec',type=Path,required=True);p.add_argument('--zircon-root',type=Path,required=True);a=p.parse_args()
    source=(a.zircon_root/'Client/Scenes/Views/CurrencyDialog.cs').read_text(encoding='utf-8-sig')
    for needle in ('private CurrencyTree BindTree;','BindTree = new CurrencyTree','public class CurrencyTree : DXControl','ScrollBar = new DXVScrollBar','CurrencyTreeHeader header = new CurrencyTreeHeader','CurrencyItem entry = new CurrencyItem'):
        if needle not in source: raise SystemExit(f'Current Currency tree source changed: missing {needle!r}')
    for retired in ('CurrencyRows = new CurrencyRow[4];','public sealed class CurrencyRow : DXControl'):
        if retired in source: raise SystemExit(f'Retired Currency fixed-row source returned: {retired}')
    spec=json.loads(a.spec.read_text(encoding='utf-8'));w=next((x for x in spec.get('windows',[]) if x.get('field')=='CurrencyBox'),None)
    if not w: raise SystemExit('CurrencyBox missing')
    stale=[str(c.get('name') or '') for c in w.get('controls',[]) if str(c.get('sourceGenerated') or '').startswith(('deterministic-currency:CurrencyDialog constructor loop','deterministic-currency-array:CurrencyDialog constructor array loop'))]
    if stale: raise SystemExit(f'Retired Currency fixed rows remain: {stale}')
    w['legacyCurrencyRowCompatibility']={'passed':True,'legacyControlsEmitted':0,'authoritativeOwner':'augment_currency_tree_shell.py','duplicateRowsInvented':False,'runtimeCurrencyRowsInvented':False}
    a.spec.write_text(json.dumps(spec,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print('Currency compatibility: PASS -> fixed rows=0; CurrencyTree is authoritative')
if __name__=='__main__':main()
