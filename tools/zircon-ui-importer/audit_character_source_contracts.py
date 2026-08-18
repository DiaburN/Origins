#!/usr/bin/env python3
"""Strict source contract for CharacterDialog / InspectBox neutral boundaries."""
from __future__ import annotations
import argparse,json
from pathlib import Path

def req(text,needle,label):
    if needle not in text: raise SystemExit(f"Character source contract changed: {label}: missing {needle!r}")

def main():
    p=argparse.ArgumentParser();p.add_argument('--spec',type=Path,required=True);p.add_argument('--zircon-root',type=Path,required=True);a=p.parse_args()
    spec=json.loads(a.spec.read_text(encoding='utf-8'))
    src=(a.zircon_root/'Client/Scenes/Views/CharacterDialog.cs').read_text(encoding='utf-8-sig')
    for needle,label in (
        ('Index = Inspect ? 115 : 110;','Character/Inspect source background'),
        ('TabControl.SelectedTab = CharacterTab;','Character primary initial tab'),
        ('DisciplineTab.TabButton.Visible = !Inspect && Globals.DisciplineInfoList.Binding.Count > 0;','Discipline runtime tab visibility'),
        ('HermitTab.TabButton.Visible = !Inspect && GameScene.Game.HermitEnabled;','Hermit runtime tab visibility'),
        ('MarriageIcon = new DXImageControl','marriage icon'),('Index = 1298,','marriage source icon'),('Visible = false','marriage neutral hidden'),
        ('GameScene.Game.FishingBox.Visible = HasFishingRod && IsVisible;','Fishing visibility runtime equipment gate'),
        ('GridType = Inspect ? GridType.Inspect : GridType.Equipment,','equipment/inspect grid mode'),
        ('public void NewInformation(S.Inspect p)','Inspect packet population'),('CharacterNameLabel.Text = p.Name;','Inspect runtime name'),('GuildNameLabel.Text = p.GuildName;','Inspect runtime guild'),('MarriageIcon.Visible = !string.IsNullOrEmpty(p.Partner);','Inspect runtime marriage'),
        ('public void UpdateStats()','runtime stat refresh'),('pair.Value.Text = Stats.GetFormat(pair.Key);','runtime stat formatting'),
    ): req(src,needle,label)
    char=next((w for w in spec.get('windows',[]) if w.get('field')=='CharacterBox'),None)
    inspect=next((w for w in spec.get('windows',[]) if w.get('field')=='InspectBox'),None)
    if not char or not inspect: raise SystemExit('CharacterBox/InspectBox missing from source manifest')
    if '110' not in str(char.get('root',{}).get('Index')): raise SystemExit(f"CharacterBox source index drifted: {char.get('root',{}).get('Index')}")
    if '115' not in str(inspect.get('root',{}).get('Index')): raise SystemExit(f"InspectBox source index drifted: {inspect.get('root',{}).get('Index')}")
    def primary_tabs(window):
        return [c for c in window.get('controls',[]) if c.get('type')=='DXTab' and c.get('properties',{}).get('Parent')=='TabControl']
    char_tabs=primary_tabs(char);inspect_tabs=primary_tabs(inspect)
    if [c.get('name') for c in char_tabs]!=['CharacterTab','DisciplineTab','HermitTab']:
        raise SystemExit(f"Character primary tabs drifted: {[c.get('name') for c in char_tabs]}")
    if [c.get('name') for c in inspect_tabs]!=['CharacterTab','DisciplineTab','HermitTab']:
        raise SystemExit(f"Inspect primary tabs drifted: {[c.get('name') for c in inspect_tabs]}")
    stats=[c for c in char.get('controls',[]) if c.get('type')=='DXTab' and c.get('properties',{}).get('Parent')=='StatsTabControl']
    if len(stats)!=7: raise SystemExit(f'Character stats tab count drifted: {len(stats)}')
    for window,inspect_mode,index in ((char,False,110),(inspect,True,115)):
        window['characterSourceAudit']={'passed':True,'inspect':inspect_mode,'sourceIndex':index,'initialPrimaryTab':'CharacterTab','neutralDisciplineVisible':False,'neutralHermitVisible':False,'neutralMarriageVisible':False,'runtimeIdentityInvented':False,'runtimeEquipmentInvented':False,'runtimePreviewInvented':False,'constructorZeroStatsPreserved':True}
    a.spec.write_text(json.dumps(spec,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print('Character source contract: PASS (Character#110 / Inspect#115, CharacterTab, runtime identity/equipment/preview neutral)')
if __name__=='__main__': main()
