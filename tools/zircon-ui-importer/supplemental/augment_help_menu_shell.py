#!/usr/bin/env python3
"""Materialise HelpDialog's fixed HelpMenu shell and its scrollbar.

HelpDialog always constructs HelpMenu. HelpMenu always constructs one scrollbar.
Buttons, HelpContainer pages, DXTabs and HelpItems are created only after
Globals.HelpInfoList supplies real runtime help data, so they remain absent.
"""
from __future__ import annotations
import argparse,json
from pathlib import Path
PREFIX='deterministic-help-menu:'
def main():
    p=argparse.ArgumentParser();p.add_argument('--spec',type=Path,required=True);p.add_argument('--zircon-root',type=Path,required=True);a=p.parse_args()
    source=(a.zircon_root/'Client/Scenes/Views/HelpDialog.cs').read_text(encoding='utf-8-sig')
    for needle in ('Menu = new HelpMenu','Location = new Point(13, 70)','public sealed class HelpMenu : DXControl','Size = new Size(156, 306);','MenuScrollBar = new DXVScrollBar','Location = new Point(134, 0)','Size = new Size(20, 310)','VisibleSize = Size.Height','Change = ButtonHeight','private const int ButtonHeight = 23;','foreach (var helpInfo in Globals.HelpInfoList.Binding.OrderBy(x => x.Order))','var page = new HelpContainer(info)','var button = new DXButton'):
        if needle not in source: raise SystemExit(f'Help source changed: missing {needle!r}')
    spec=json.loads(a.spec.read_text(encoding='utf-8'));w=next((x for x in spec.get('windows',[]) if x.get('field')=='HelpBox'),None)
    if not w: raise SystemExit('HelpBox missing')
    controls=[c for c in w.get('controls',[]) if not str(c.get('sourceGenerated') or '').startswith(PREFIX)]
    root={'name':'HelpMenuSource','type':'DXControl','sourceType':'HelpMenu','properties':{'Parent':'this','Location':'new Point(13, 70)','Size':'new Size(156, 306)','RuntimeHelpPages':'Globals.HelpInfoList; absent in neutral reference'},'sourceGenerated':PREFIX+'HelpDialog constructor','runtimePayloadInvented':False}
    scroll={'name':'HelpMenuSourceScrollBar','type':'DXVScrollBar','properties':{'Parent':'HelpMenuSource','BackColour':'Color.Empty','Location':'new Point(134, 0)','Size':'new Size(20, 310)','MinValue':'0','MaxValue':'0','VisibleSize':'HelpMenuSource.Size.Height','Change':'23','Border':'false','UpButton':'{ Index = 61, LibraryFile = LibraryFile.Interface }','DownButton':'{ Index = 62, LibraryFile = LibraryFile.Interface }','PositionBar':'{ Index = 60, LibraryFile = LibraryFile.Interface }','ShowBackgroundSlider':'true'},'sourceGenerated':PREFIX+'HelpMenu constructor','runtimePayloadInvented':False}
    w['controls']=[root,scroll]+controls;w['deterministicHelpMenu']={'passed':True,'controlsAdded':2,'menuShells':1,'scrollbars':1,'runtimeButtonsInvented':False,'runtimeHelpContainersInvented':False,'runtimeHelpTabsInvented':False,'runtimeHelpItemsInvented':False,'runtimeHelpInfoInvented':False}
    a.spec.write_text(json.dumps(spec,indent=2,ensure_ascii=False)+'\n',encoding='utf-8');print('Help menu shell expanded: 2 controls; no HelpInfo pages/items/buttons')
if __name__=='__main__':main()
