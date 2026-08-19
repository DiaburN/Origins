#!/usr/bin/env python3
"""Promote ChatOptionsDialog.AddNewTab as a local-only source template.

The constructor does not call AddNewTab, so no chat tabs/panels are precreated.
This records the exact local recipe used only after the viewer's Add button is
clicked. It does not create manifest controls or user/server state.
"""
from __future__ import annotations
import argparse,json
from pathlib import Path

CHECKED_TRUE=['LocalCheckBox','WhisperCheckBox','GroupCheckBox','GuildCheckBox','ShoutCheckBox','GlobalCheckBox','ObserverCheckBox','HintCheckBox','SystemCheckBox','GainsCheckBox','AlertCheckBox']
CHECKED_FALSE=['TransparentCheckBox','HideTabCheckBox','ReverseListCheckBox','CleanUpCheckBox','FadeOutCheckBox']

def main():
 p=argparse.ArgumentParser();p.add_argument('--spec',type=Path,required=True);p.add_argument('--zircon-root',type=Path,required=True);a=p.parse_args();source=(a.zircon_root/'Client/Scenes/Views/ChatOptionsDialog.cs').read_text(encoding='utf-8-sig')
 needles=('button.MouseClick += (o, e) => AddNewTab(null);','public ChatTab AddNewTab(ChatTabPageSetting settings)','Item = panel = new ChatOptionsPanel','Visible = false','Location = new Point(ListBox.Location.X + ListBox.Size.Width + 5, ListBox.Location.Y)','DXTabControl tabControl = new DXTabControl','Size = new Size(200, 200)','Parent = GameScene.Game','Movable = true','ChatTab tab = new ChatTab','Opacity = 0.5F','AllowResize = true','Movable = true, AllowDragOut = true','Label = { Text = $"Window {ListBox.Controls.Count - 1}" }','panel.Size = new Size(ClientArea.Width - panel.Location.X, ClientArea.Height);','panel.Text = $"Window {ListBox.Controls.Count - 1}";','ListBox.SelectedItem = item;')
 for needle in needles:
  if needle not in source:raise SystemExit(f'Chat Options AddNewTab source changed: missing {needle!r}')
 for name in CHECKED_TRUE:
  if f'{name} = {{ Checked = true }}' not in source:raise SystemExit(f'Chat Options source default changed: {name} should be true in AddNewTab')
 # The remaining panel constructor defaults are false; AddNewTab does not override them.
 spec=json.loads(a.spec.read_text(encoding='utf-8'));w=next((x for x in spec.get('windows',[]) if x.get('field')=='ChatOptionsBox'),None)
 if not w:raise SystemExit('ChatOptionsBox missing')
 before=len(w.get('controls',[]))
 w['chatOptionsAddNewTabTemplate']={'passed':True,'constructorPrecreatesTabs':False,'trigger':'ChatOptionsDialog Add button MouseClick -> AddNewTab(null)','listItemType':'DXListBoxItem','panelSourceType':'ChatOptionsPanel','panelInitialVisible':False,'panelLocationExpression':'new Point(ListBox.Location.X + ListBox.Size.Width + 5, ListBox.Location.Y)','panelSizeExpression':'new Size(ClientArea.Width - panel.Location.X, ClientArea.Height)','checkedTrue':CHECKED_TRUE,'checkedFalse':CHECKED_FALSE,'tabControlSourceType':'DXTabControl','tabControlSize':[200,200],'tabControlParent':'GameScene.Game','tabControlMovable':True,'chatTabSourceType':'ChatTab','chatTabOpacity':0.5,'chatTabAllowResize':True,'tabButtonMovable':True,'tabButtonAllowDragOut':True,'nameExpression':'Window {ListBox.Controls.Count - 1}','selectedListItemAfterCreate':True,'settingsPayload':None,'localStateOnly':True,'existingTabsInvented':False,'chatMessagesInvented':False,'userDataInvented':False,'serverDataInvented':False,'manifestControlsAdded':0}
 if len(w.get('controls',[]))!=before:raise SystemExit('Chat Options template augmenter must not create controls')
 a.spec.write_text(json.dumps(spec,indent=2,ensure_ascii=False)+'\n',encoding='utf-8');print('Chat Options AddNewTab template promoted: local-only; constructor tabs=0; manifest controls +0')
if __name__=='__main__':main()
