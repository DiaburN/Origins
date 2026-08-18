#!/usr/bin/env python3
"""Expand FilterDropDialog's deterministic ten-filter constructor loop."""
from __future__ import annotations
import argparse,json
from pathlib import Path

COUNT=10
LABEL_HEIGHT=16

def make(name,type_name,properties,resolved=None):
    item={'name':name,'type':type_name,'properties':dict(properties),'sourceGenerated':'FilterDropDialog constructor for-loop'}
    if resolved is not None:item['resolvedText']=resolved
    return item

def main():
    p=argparse.ArgumentParser();p.add_argument('--spec',type=Path,required=True);a=p.parse_args()
    spec=json.loads(a.spec.read_text(encoding='utf-8'))
    w=next((x for x in spec.get('windows',[]) if x.get('field')=='FilterDropBox'),None)
    if not w:raise SystemExit('FilterDropBox missing from manifest')
    controls=[c for c in w.get('controls',[]) if not str(c.get('name','')).startswith('FilterDropGenerated')]
    english=(spec.get('language') or {}).get('English') or {}
    template=str(english.get('FilterDialogFilterLabel') or 'Filter {0}')
    generated=[]
    for i in range(COUNT):
        try:label=template.format(i+1)
        except Exception:label=f'Filter {i+1}'
        generated.append(make(f'FilterDropGeneratedLabel{i+1:02d}','DXLabel',{
            'Parent':'this','Location':f'new Point(20, {50+(10+LABEL_HEIGHT)*i})','Text':f'string.Format(CEnvir.Language.FilterDialogFilterLabel, {i+1})','SourceLocationExpression':f'new Point(20, 50 + (10 + filterLabel.Size.Height) * {i})'
        },label))
        generated.append(make(f'FilterDropGeneratedTextBox{i+1:02d}','DXTextBox',{
            'Parent':'this','Location':f'new Point(100, {50+30*i})','Size':'new Size(150, 20)','MaxLength':'100','Text':"string.Empty",'SourceLocationExpression':f'new Point(100, 50 + (10 + filterBox.Size.Height) * {i})'
        },''))
    w['controls']=generated+controls
    w['filterDropSourceLoop']={'count':COUNT,'labelDefaultReferenceHeight':LABEL_HEIGHT,'textBoxSize':[150,20],'textBoxStep':30,'runtimeHighlightedItemsInvented':False,'checkedInConfigHighlightedItems':''}
    if len(generated)!=20:raise SystemExit('FilterDrop loop expansion count drifted')
    a.spec.write_text(json.dumps(spec,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print('FilterDrop source loop expanded: 10 labels + 10 text boxes')
if __name__=='__main__':main()
