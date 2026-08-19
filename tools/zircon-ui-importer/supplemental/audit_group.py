#!/usr/bin/env python3
"""Strict neutral-state contract for GroupDialog/GroupHealth source flow."""
from __future__ import annotations
import argparse,json
from pathlib import Path

def req(text,needle,label):
    if needle not in text: raise SystemExit(f'Group source contract changed: {label}: missing {needle!r}')

def main():
    p=argparse.ArgumentParser();p.add_argument('--spec',type=Path,required=True);p.add_argument('--zircon-root',type=Path,required=True);a=p.parse_args();spec=json.loads(a.spec.read_text(encoding='utf-8'))
    src=(a.zircon_root/'Client/Scenes/Views/GroupDialog.cs').read_text(encoding='utf-8-sig')
    for needle,label in (
        ('private bool _AllowGroup;','AllowGroup default false'),('Checked = false,','AllowGroup checkbox false'),('new C.GroupSwitch { Allow = !AllowGroup }','AllowGroup server request'),('public List<ClientPlayerInfo> Members = new List<ClientPlayerInfo>();','group members runtime list'),
        ('RemoveButton = new DXButton','remove button'),('Enabled = false,','neutral disabled controls'),('DXInputWindow window = new DXInputWindow','Add opens input window'),('ConfirmButton = { Enabled = false },','invite confirm initially disabled'),('Globals.CharacterReg.IsMatch','invite name validation'),('new C.GroupInvite','group invite packet'),
        ('UpdateList(new List<ClientLookingForGroup>());','neutral empty LFG list'),('LFGRows = new GroupLFGRow[5];','five LFG rows'),('Visible = false,','LFG rows neutral hidden'),
        ('Size = new Size(150, 500);','GroupHealth source size'),('Opacity = 0.0F;','GroupHealth neutral opacity'),('public List<GroupHealthMember> Members = new();','GroupHealth runtime members'),
    ): req(src,needle,label)
    by={w.get('field'):w for w in spec.get('windows',[])};group=by.get('GroupBox');health=by.get('GroupHealthBox')
    if not group or not health: raise SystemExit('GroupBox/GroupHealthBox missing from final manifest')
    if health.get('root',{}).get('Size')!='new Size(150, 500)' or health.get('root',{}).get('Opacity')!='0F': raise SystemExit(f'GroupHealth neutral promotion drifted: {health.get("root")}')
    group['groupSourceAudit']={'passed':True,'neutralMemberCount':0,'neutralAllowGroup':False,'neutralLfgCount':0,'sourceLfgRowCapacity':5,'runtimeMembersInvented':False,'runtimeLfgInvented':False,'serverActionsExecutedByReference':False}
    health['groupHealthSourceAudit']={'passed':True,'neutralMemberCount':0,'size':[150,500],'opacity':0.0,'runtimeMembersInvented':False}
    a.spec.write_text(json.dumps(spec,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print('Group source contract: PASS (0 members/LFG, AllowGroup=false, GroupHealth 150x500 opacity0)')
if __name__=='__main__':main()
