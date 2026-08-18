#!/usr/bin/env python3
"""Resolve combo labels written as $"{Enum.Member}" from checked-in enums."""
from __future__ import annotations
import argparse,json,re,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from augment_combo_options import class_body,list_item_initializers,merge_entries,parse_enum,resolve_selected_index

def balanced_selected_expression(body,name):
    marker=f'{name}.ListBox.SelectItem('
    starts=[];offset=0
    while True:
        pos=body.find(marker,offset)
        if pos<0: break
        starts.append(pos);offset=pos+len(marker)
    if not starts:return None
    pos=starts[-1]+len(marker);start=pos;depth=1;in_string=False;escaped=False
    while pos<len(body):
        c=body[pos]
        if in_string:
            if escaped: escaped=False
            elif c=='\\': escaped=True
            elif c=='"': in_string=False
        else:
            if c=='"': in_string=True
            elif c=='(': depth+=1
            elif c==')':
                depth-=1
                if depth==0:return ' '.join(body[start:pos].split())
        pos+=1
    return None

def main():
    p=argparse.ArgumentParser();p.add_argument('--spec',type=Path,required=True);p.add_argument('--zircon-root',type=Path,required=True);a=p.parse_args()
    spec=json.loads(a.spec.read_text(encoding='utf-8'));added=0;changed=0;reconciled=0
    for owner in [*(spec.get('windows') or []),*(spec.get('nestedWindows') or [])]:
        combos={c.get('name'):c for c in owner.get('controls',[]) if c.get('type')=='DXComboBox'}
        path=a.zircon_root/str(owner.get('sourcePath') or '')
        cls=owner.get('class') or owner.get('sourceClass')
        if not combos or not path.exists() or not cls: continue
        body=class_body(path.read_text(encoding='utf-8-sig'),str(cls))
        if not body: continue
        found={name:[] for name in combos}
        for init in list_item_initializers(body):
            parent=re.search(r'\bParent\s*=\s*([A-Za-z_][A-Za-z0-9_]*)\.ListBox\b',init)
            label=re.search(r'\bLabel\s*=\s*\{\s*Text\s*=\s*\$"\{([A-Za-z_][A-Za-z0-9_]*)\.([A-Za-z_][A-Za-z0-9_]*)\}"\s*\}',init,re.S)
            item=re.search(r'\bItem\s*=\s*([A-Za-z_][A-Za-z0-9_]*)\.([A-Za-z_][A-Za-z0-9_]*)\b',init)
            if not parent or parent.group(1) not in combos or not label or not item: continue
            enum_name,member=label.groups();item_enum,item_member=item.groups()
            if (enum_name,member)!=(item_enum,item_member): continue
            members={m['name'] for m in parse_enum(a.zircon_root,enum_name)}
            if member not in members: raise SystemExit(f'Unknown static enum combo member: {enum_name}.{member}')
            merge_entries(found[parent.group(1)],[{'label':member,'labelSource':f'$"{{{enum_name}.{member}}}"','valueExpression':f'{enum_name}.{member}','sourceBuilder':'static-enum-interpolation'}])
        for name,entries in found.items():
            if not entries: continue
            control=combos[name];options=list(control.get('comboOptions') or []);before=len(options);merge_entries(options,entries)
            delta=len(options)-before;control['comboOptions']=options
            expr=balanced_selected_expression(body,name)
            if expr:
                control['comboSelectedExpression']=expr
                selected=resolve_selected_index(body,expr,options)
                if selected is not None: control['comboSelectedOptionIndex']=selected
                reconciled+=1
            if delta: added+=delta;changed+=1
    pass_info=spec.setdefault('comboOptionPass',{});pass_info['staticEnumInterpolationOptionsAdded']=added;pass_info['staticEnumInterpolationCombosChanged']=changed;pass_info['staticEnumSelectionsReconciled']=reconciled;pass_info['runtimeOptionsInvented']=False
    a.spec.write_text(json.dumps(spec,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(f'Static enum interpolation combo options added: {added} across {changed} controls; selections reconciled={reconciled}')
if __name__=='__main__':main()
