#!/usr/bin/env python3
"""Promote CurrencyTree's deterministic empty-tree scrollbar structure."""
from __future__ import annotations
import argparse,json
from pathlib import Path

def main():
    p=argparse.ArgumentParser();p.add_argument('--spec',type=Path,required=True);a=p.parse_args()
    spec=json.loads(a.spec.read_text(encoding='utf-8'))
    w=next((x for x in spec.get('windows',[]) if x.get('field')=='CurrencyBox'),None)
    if not w:raise SystemExit('CurrencyBox missing from source manifest')
    controls=[c for c in w.get('controls',[]) if c.get('name')!='CurrencyBindTreeScrollBar']
    bind=next((c for c in controls if c.get('name')=='BindTree'),None)
    if not bind:raise SystemExit('Currency BindTree missing from source manifest')
    # CurrencyTree inherits DXControl. Keep its source type provenance while making
    # the base renderer treat it structurally if the importer has not already.
    bind.setdefault('sourceType',bind.get('type'))
    if bind.get('type') not in ('DXControl','CurrencyTree'):
        raise SystemExit(f"Unexpected CurrencyTree manifest type: {bind.get('type')}")
    bind['type']='DXControl'
    bind['properties'].update({'Location':'new Point(22, 55)','Size':'new Size(235, 340)','Border':'true','BorderColour':'Constants.PrimaryColour'})
    scroll={'name':'CurrencyBindTreeScrollBar','type':'DXVScrollBar','properties':{'Parent':'BindTree','Location':'new Point(221, 0)','Size':'new Size(14, 340)','Change':'22','VisibleSize':'340','MaxValue':'0'},'sourceGenerated':'CurrencyTree constructor + OnSizeChanged'}
    w['controls']=[scroll]+controls
    w['currencyTreeSourceState']={'size':[235,340],'location':[22,55],'scrollBar':[221,0,14,340],'scrollChange':22,'scrollMaxValueNeutral':0,'headerHeight':22,'currencyHeight':42,'runtimeCurrenciesInvented':False,'neutralHeaders':0,'neutralCurrencies':0}
    a.spec.write_text(json.dumps(spec,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print('CurrencyTree neutral source structure promoted: border + 14px scroll, 0 runtime rows')
if __name__=='__main__':main()
