#!/usr/bin/env python3
"""Record BeltDialog's size-dependent DXLabel template without fixing a row count.

BeltDialog.OnClientAreaChanged recreates its DXItemGrid and then creates one
DXLabel per local Grid.Grid cell. The number of cells depends on the locally
resized Belt window, not server/player data, so source fidelity is a template
bound to the rendered grid rather than a fabricated fixed control array.
"""
from __future__ import annotations
import argparse,json
from pathlib import Path

def main():
 p=argparse.ArgumentParser();p.add_argument('--spec',type=Path,required=True);p.add_argument('--zircon-root',type=Path,required=True);a=p.parse_args();source=(a.zircon_root/'Client/Scenes/Views/BeltDialog.cs').read_text(encoding='utf-8-sig')
 for needle in ('OnClientAreaChanged(ClientArea, ClientArea);','for (int i = 0; i < Grid.Grid.Length; i++)','Parent = Grid.Grid[i]','Text = ((i + 1) % 10).ToString()','CEnvir.FontSize(8F), FontStyle.Italic','Location = new Point(-2, -1)'):
  if needle not in source:raise SystemExit(f'Belt hotkey label source changed: missing {needle!r}')
 spec=json.loads(a.spec.read_text(encoding='utf-8'));w=next((x for x in spec.get('windows',[]) if x.get('field')=='BeltBox'),None)
 if not w:raise SystemExit('BeltBox missing')
 grid=next((c for c in w.get('controls',[]) if c.get('name')=='Grid' and c.get('type')=='DXItemGrid'),None)
 if grid is None:raise SystemExit('Belt source Grid control missing')
 w['beltHotkeyLabelTemplate']={'passed':True,'sourceType':'DXLabel','parentExpression':'Grid.Grid[i]','countExpression':'Grid.Grid.Length','textExpression':'((i + 1) % 10).ToString()','fontSize':8.0,'fontStyle':'Italic','location':[-2,-1],'isControl':False,'localResizeDependent':True,'fixedCountInvented':False,'runtimeItemDataInvented':False,'runtimePlayerDataInvented':False}
 a.spec.write_text(json.dumps(spec,indent=2,ensure_ascii=False)+'\n',encoding='utf-8');print('Belt hotkey label template: PASS -> one source label per local grid cell, no fixed count')
if __name__=='__main__':main()
