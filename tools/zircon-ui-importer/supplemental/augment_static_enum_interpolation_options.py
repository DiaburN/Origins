#!/usr/bin/env python3
"""Resolve combo labels written as $"{Enum.Member}" from checked-in enums.

Only a qualifier that resolves to an actual checked-in enum is handled here.
Expressions such as $"{pair.Key}" are ordinary runtime/local-variable member
access and must not be misclassified as enum members. Once an enum is known,
an unknown member still fails loudly.
"""
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

def control_source_name(control):
    return str(control.get('sourceName') or control.get('name') or '')

def main():
    p=argparse.ArgumentParser();p.add_argument('--spec',type=Path,required=True);p.add_argument('--zircon-root',type=Path,required=True);a=p.parse_args()
    spec=json.loads(a.spec.read_text(encoding='utf-8'));added=0;changed=0;reconciled=0;non_enum_skipped=0
    for owner in [*(spec.get('windows') or []),*(spec.get('nestedWindows') or [])]:
        combo_controls=[c for c in owner.get('controls',[]) if c.get('type')=='DXComboBox']
        combos={control_source_name(c):c for c in combo_controls if control_source_name(c)}
        path=a.zircon_root/str(owner.get('sourcePath') or '')
        cls=owner.get('sourceClass') or owner.get('class')
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
            enum_rows=parse_enum(a.zircon_root,enum_name)
            if not enum_rows:
                # Not a checked-in enum at all (for example NPCDialog pair.Key).
                # This pass owns static enum interpolation only; leave local/runtime
                # member expressions to their source-specific/runtime boundary.
                non_enum_skipped+=1
                continue
            members={m['name'] for m in enum_rows}
            if member not in members: raise SystemExit(f'Unknown static enum combo member: {enum_name}.{member}')
            merge_entries(found[parent.group(1)],[{'label':member,'labelSource':f'$"{{{enum_name}.{member}}}"','valueExpression':f'{enum_name}.{member}','sourceBuilder':'static-enum-interpolation'}])
        for source_name,entries in found.items():
            if not entries: continue
            control=combos[source_name];options=list(control.get('comboOptions') or []);before=len(options);merge_entries(options,entries)
            delta=len(options)-before;control['comboOptions']=options
            expr=balanced_selected_expression(body,source_name)
            if expr:
                control['comboSelectedExpression']=expr
                selected=resolve_selected_index(body,expr,options)
                if selected is not None: control['comboSelectedOptionIndex']=selected
                reconciled+=1
            if delta: added+=delta;changed+=1
    pass_info=spec.setdefault('comboOptionPass',{});pass_info['staticEnumInterpolationOptionsAdded']=added;pass_info['staticEnumInterpolationCombosChanged']=changed;pass_info['staticEnumSelectionsReconciled']=reconciled;pass_info['staticEnumNonEnumInterpolationsSkipped']=non_enum_skipped;pass_info['staticEnumKnownMembersRemainStrict']=True;pass_info['runtimeOptionsInvented']=False
    a.spec.write_text(json.dumps(spec,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(f'Static enum interpolation combo options added: {added} across {changed} controls; selections reconciled={reconciled}; non-enum member expressions skipped={non_enum_skipped}')
if __name__=='__main__':main()
