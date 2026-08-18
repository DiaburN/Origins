#!/usr/bin/env python3
"""Strict contract for ChatOptionsDialog.AddNewTab local viewer runtime.

The constructor must remain empty of tabs. Only the source Add button may create
viewer-local UI. No player/server/chat-history payload may be synthesized.
"""
from __future__ import annotations
import argparse,json
from pathlib import Path

TRUE_SET={"LocalCheckBox","WhisperCheckBox","GroupCheckBox","GuildCheckBox","ShoutCheckBox","GlobalCheckBox","ObserverCheckBox","HintCheckBox","SystemCheckBox","GainsCheckBox","AlertCheckBox"}
FALSE_SET={"TransparentCheckBox","HideTabCheckBox","ReverseListCheckBox","CleanUpCheckBox","FadeOutCheckBox"}

def main():
 p=argparse.ArgumentParser();p.add_argument('--spec',type=Path,required=True);p.add_argument('--zircon-root',type=Path,required=True);a=p.parse_args();spec=json.loads(a.spec.read_text(encoding='utf-8'));window=next((w for w in spec.get('windows',[]) if w.get('field')=='ChatOptionsBox'),None)
 if not window:raise SystemExit('ChatOptionsBox missing')
 template=window.get('chatOptionsAddNewTabTemplate') or {};fail=[]
 def req(condition,message):
  if not condition:fail.append(message)
 req(template.get('passed') is True,f'AddNewTab template missing/not PASS: {template}')
 req(template.get('constructorPrecreatesTabs') is False,'Chat Options constructor must precreate zero tabs')
 req(template.get('manifestControlsAdded')==0,'AddNewTab template must add zero manifest controls')
 req(set(template.get('checkedTrue') or [])==TRUE_SET,f'AddNewTab checked-true set drifted: {template.get("checkedTrue")}')
 req(set(template.get('checkedFalse') or [])==FALSE_SET,f'AddNewTab checked-false set drifted: {template.get("checkedFalse")}')
 req(template.get('panelInitialVisible') is False,'new ChatOptionsPanel source initial Visible must be false')
 req(template.get('tabControlSize')==[200,200],'new DXTabControl source size must be 200x200')
 req(template.get('tabControlParent')=='GameScene.Game','new DXTabControl source parent drifted')
 req(template.get('chatTabOpacity')==0.5 and template.get('chatTabAllowResize') is True,'ChatTab local source state drifted')
 req(template.get('tabButtonMovable') is True and template.get('tabButtonAllowDragOut') is True,'ChatTab button source drag state drifted')
 req(template.get('localStateOnly') is True and template.get('existingTabsInvented') is False and template.get('chatMessagesInvented') is False and template.get('userDataInvented') is False and template.get('serverDataInvented') is False,'Chat Options runtime-data boundary broken in template')
 root=Path(__file__).resolve().parents[3];runtime=root/'apps/zircon-ui-reference/extra-runtimes/chat-options-add-runtime.js'
 if not runtime.exists():fail.append('chat-options-add-runtime.js missing');text=''
 else:text=runtime.read_text(encoding='utf-8')
 required=(
  "import { buildWindowLayout } from '../layout-resolver.js';",
  "const state={tabs:[],selectedId:null,nextId:0};",
  "const RESIZE_BUFFER=9",
  "assetSize('Interface',41)",
  "leftIndex:41,middleIndex:43,rightIndex:42",
  "leftIndex:56,middleIndex:58,rightIndex:57",
  "Math.max(60",
  "dataset.sourceType='DXListBoxItem'",
  "dataset.sourceType='ChatOptionsPanel'",
  "dataset.sourceType='DXTabControl'",
  "dataset.sourceType='ChatTab'",
  "dataset.sourceType='DXVScrollBar'",
  "dataset.runtimeMessages='none'",
  "makeImage('GameInter',240,tabButton)",
  "alert.style.display='none'",
  "const id=state.nextId++,name=`Window ${state.tabs.length}`",
  "add.dataset.sourceLocalAction='AddNewTab(null)'",
  "add.addEventListener('click'",
  "remove.addEventListener('click',()=>removeTab(tab.id))",
  "template?.localStateOnly",
  "constructor tabs remain 0",
 )
 for needle in required:req(needle in text,f'Chat Options local runtime source marker missing: {needle}')
 forbidden=(
  "width:85px","middle.style.width='38px'","middle.style.width='73px'",
  "runtimeLabel(","Zuma Temple","Wizard","ClientUserItem","MapObject.User","GameScene.Game.User",
  "ReceiveChat(","History.push","serverData","sample message",
 )
 for needle in forbidden:req(needle not in text,f'Chat Options local runtime contains forbidden guessed/runtime payload marker: {needle}')
 # Config.FontName is current source truth; do not silently use the old viewer Arial measurement.
 config=(a.zircon_root/'Client/Envir/Config.cs').read_text(encoding='utf-8-sig')
 req('public static string FontName { get; set; } = "MS Sans Serif";' in config,'Zircon Config.FontName source changed; review local tab text measurement')
 req("context.font='9px Arial'" not in text and 'context.font="9px Arial"' not in text,'Chat Options tab width must not be measured with guessed Arial')
 report={'passed':not fail,'constructorTabs':0,'clickCreatedStateOnly':True,'checkedTrue':sorted(TRUE_SET),'checkedFalse':sorted(FALSE_SET),'tabControlSize':[200,200],'resizeBuffer':9,'usesAssetSizedButtonPieces':True,'nestedChatTabStructure':['DXVScrollBar','DXControl(TextPanel)','DXImageControl(AlertIcon hidden)'],'chatMessagesInvented':False,'userDataInvented':False,'serverDataInvented':False,'manifestControlsAdded':0,'failures':fail};spec['chatOptionsAddLocalRuntimeAudit']=report;a.spec.write_text(json.dumps(spec,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
 if fail:raise SystemExit('Chat Options Add local runtime audit failed:\n- '+'\n- '.join(fail))
 print('Chat Options Add local runtime audit: PASS -> constructor tabs=0; click-created Window N local UI only')
if __name__=='__main__':main()
