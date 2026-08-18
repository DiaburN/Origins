#!/usr/bin/env python3
"""Reject duplicate deterministic UI emitters for consolidated source families.

Compatibility passes may remain executable for regression coverage, but they
must emit zero controls. The authoritative owners are the current deterministic
Consignment composite pass and the current CurrencyTree shell pass.
"""
from __future__ import annotations
import argparse,json
from collections import Counter
from pathlib import Path

def main():
    p=argparse.ArgumentParser();p.add_argument('--spec',type=Path,required=True);p.add_argument('--zircon-root',type=Path,required=True);a=p.parse_args()
    spec=json.loads(a.spec.read_text(encoding='utf-8'));by={w.get('field'):w for w in spec.get('windows',[])};failures=[]

    consignment=by.get('ConsignmentBox') or {};cc=consignment.get('controls') or []
    modern_consignment=[str(c.get('name') or '') for c in cc if str(c.get('sourceGenerated') or '').startswith('deterministic-consignment:')]
    stale_consignment=[str(c.get('name') or '') for c in cc if str(c.get('sourceGenerated') or '').startswith(('deterministic-consignment-v2:','deterministic-consignment-headers:'))]
    legacy_report=consignment.get('legacyConsignmentCompositeCompatibility') or {};header_compat=consignment.get('consignmentHeaderCompatibility') or {}
    if stale_consignment: failures.append(f'stale Consignment controls remain: {stale_consignment[:30]}')
    if len(modern_consignment)!=135: failures.append(f'authoritative Consignment controls {len(modern_consignment)} != 135')
    if legacy_report.get('passed') is not True or legacy_report.get('legacyControlsEmitted')!=0: failures.append(f'Consignment compatibility incomplete: {legacy_report}')
    if header_compat.get('passed') is not True or header_compat.get('controlsAddedByCompatibilityPass')!=0: failures.append(f'Consignment header compatibility incomplete: {header_compat}')

    currency=by.get('CurrencyBox') or {};cur=currency.get('controls') or []
    modern_currency=[str(c.get('name') or '') for c in cur if str(c.get('sourceGenerated') or '').startswith('deterministic-currency-tree:')]
    stale_currency=[str(c.get('name') or '') for c in cur if str(c.get('sourceGenerated') or '').startswith(('deterministic-currency:CurrencyDialog constructor loop','deterministic-currency-array:CurrencyDialog constructor array loop'))]
    currency_compat=currency.get('legacyCurrencyRowCompatibility') or {};currency_tree=currency.get('deterministicCurrencyTree') or {}
    if stale_currency: failures.append(f'stale fixed Currency controls remain: {stale_currency}')
    if len(modern_currency)!=2: failures.append(f'authoritative CurrencyTree controls {len(modern_currency)} != 2')
    if currency_tree.get('passed') is not True or currency_tree.get('controlsAdded')!=2: failures.append(f'CurrencyTree authoritative pass incomplete: {currency_tree}')
    if currency_compat.get('passed') is not True or currency_compat.get('legacyControlsEmitted')!=0: failures.append(f'Currency compatibility incomplete: {currency_compat}')

    duplicate_names={}
    for w in [*(spec.get('windows') or []),*(spec.get('nestedWindows') or [])]:
        names=[str(c.get('name') or '') for c in w.get('controls',[])];dups=sorted(n for n,count in Counter(names).items() if n and count>1)
        if dups: duplicate_names[str(w.get('field') or w.get('id'))]=dups
    if duplicate_names: failures.append(f'duplicate manifest control identities: {duplicate_names}')

    report={'passed':not failures,'consignmentStaleControls':len(stale_consignment),'consignmentAuthoritativeControls':len(modern_consignment),'currencyStaleControls':len(stale_currency),'currencyAuthoritativeControls':len(modern_currency),'duplicateControlIdentityWindows':duplicate_names,'runtimePayloadsInvented':False,'controlsFabricatedByAudit':False,'failures':failures}
    spec['duplicateDeterministicEmitterAudit']=report;a.spec.write_text(json.dumps(spec,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    if failures: raise SystemExit('Duplicate deterministic emitter audit failed:\n- '+'\n- '.join(failures))
    print('Duplicate deterministic emitter audit: PASS -> Consignment=135 unique; CurrencyTree=2 unique; duplicate names=0')
if __name__=='__main__':main()
