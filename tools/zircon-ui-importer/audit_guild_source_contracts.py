#!/usr/bin/env python3
"""Strict source contract for GuildDialog no-guild reference state."""
from __future__ import annotations
import argparse,json
from pathlib import Path

def req(text,needle,label):
    if needle not in text: raise SystemExit(f"Guild source contract changed: {label}: missing {needle!r}")

def main():
    p=argparse.ArgumentParser();p.add_argument('--spec',type=Path,required=True);p.add_argument('--zircon-root',type=Path,required=True);a=p.parse_args()
    spec=json.loads(a.spec.read_text(encoding='utf-8'))
    src=(a.zircon_root/'Client/Scenes/Views/GuildDialog.cs').read_text(encoding='utf-8-sig');globals_src=(a.zircon_root/'LibraryCore/Globals.cs').read_text(encoding='utf-8-sig')
    for needle,label in (
        ('GuildTabs = new DXTabControl','guild tabs'),('CreateCreateTab();','Create tab creation'),('CreateHomeTab();','Home tab creation'),('CreateMemberTab();','Member tab creation'),('CreateStorageTab();','Storage tab creation'),('CreateWarTab();','War tab creation'),('CreateStyleTab();','Style tab creation'),('CreateCastleTab();','Castle tab creation'),
        ('ClearGuild();','constructor clear'),('CreateTab.TabButton.InvokeMouseClick();','no-guild Create tab selection'),('BackgroundImage.Index = 266;','Create tab background'),
        ('GoldCheckBox = new DXCheckBox','gold checkbox'),('Checked = true,','gold initially selected'),('HornCheckBox = new DXCheckBox','horn checkbox'),('Checked = false,','horn initially unselected'),
        ('MemberLimit = 0;','no-guild member limit'),('StorageSize = 0;','no-guild storage size'),('CreateButton.Enabled = CanCreate;','dynamic create gate'),('public bool CanCreate => !CreateAttempted && GuildNameValid && GameScene.Game != null && TotalCost <= GameScene.Game.User.Gold.Amount;','create source gate'),
        ('CEnvir.Enqueue(new C.GuildCreate','guild create packet'),('CEnvir.Enqueue(new C.JoinStarterGuild','starter guild packet'),('Globals.GuildNameRegex.IsMatch','guild name validation'),
    ): req(src,needle,label)
    for needle,label in (('GuildCreationCost = 7500000,','creation cost'),('GuildMemberCost = 1000000,','member cost'),('GuildStorageCost = 350000,','storage cost'),('MinGuildNameLength = 2,','guild min name'),('MaxGuildNameLength = 15,','guild max name')): req(globals_src,needle,label)
    w=next((w for w in spec.get('windows',[]) if w.get('field')=='GuildBox'),None)
    if not w: raise SystemExit('GuildBox missing from final manifest')
    tabs=[c for c in w.get('controls',[]) if c.get('type') in ('DXTab','DXConfigTab') and c.get('properties',{}).get('Parent')=='GuildTabs']
    if len(tabs)!=7: raise SystemExit(f'Guild tab count drifted: {len(tabs)}')
    visible=[c.get('name') for c in tabs if c.get('tabButtonVisible')]
    if visible!=['CreateTab']: raise SystemExit(f'Guild neutral visible tabs drifted: {visible}')
    w['guildSourceAudit']={'passed':True,'neutralGuildInfo':None,'initialTab':'CreateTab','initialBackground':266,'creationCost':7500000,'runtimeGuildDataInvented':False,'serverActionsExecutedByReference':False}
    a.spec.write_text(json.dumps(spec,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print('Guild source contract: PASS (7 tabs, no-guild CreateTab/#266, 7.5m Gold base cost)')
if __name__=='__main__': main()
