import { buildWindowLayout } from '../layout-resolver.js';

// Source-faithful local implementation of ChatOptionsDialog.AddNewTab(null).
// No tab/panel exists until the source Add button is clicked. Created state is
// viewer-local only and contains no chat messages, player data or server state.
const stage=document.querySelector('#stage');
const pad=value=>String(value).padStart(5,'0');
const asset=(library,index)=>`assets/${library}/${pad(index)}.png`;
const state={tabs:[],selectedId:null,nextId:0};
let spec=null,chatItem=null,template=null;
const RESIZE_BUFFER=9; // DXControl.ResizeBuffer source constant.
const SOURCE_FONT='MS Sans Serif'; // Config.FontName checked-in Zircon default.

function language(key){const value=spec?.language?.English?.[key];return typeof value==='string'?value:''}
function assetSize(library,index){const raw=spec?.assetSizes?.[library]?.[String(index)];return Array.isArray(raw)&&raw.length===2?[Number(raw[0]),Number(raw[1])]:[0,0]}
function px(value){const number=Number.parseFloat(String(value||'0'));return Number.isFinite(number)?number:0}
function sourceControlIndex(predicate){return (chatItem?.controls||[]).findIndex(predicate)}
function elementFor(root,index){return index>=0?root.querySelector(`[data-control-index="${index}"]`):null}
function makeImage(library,index,parent){const image=document.createElement('img');image.src=asset(library,index);image.draggable=false;image.className='ui-img';parent.append(image);return image}
function threePieceButton(text,parent,{type,leftIndex,middleIndex,rightIndex,width,height}){
  const button=document.createElement('div');button.className=`dx-generated-button dx-button-${type}`;button.style.cssText=`position:absolute;width:${width}px;height:${height}px;font-family:"${SOURCE_FONT}",sans-serif`;parent.append(button);
  const [lw]=assetSize('Interface',leftIndex),[rw]=assetSize('Interface',rightIndex);
  const left=makeImage('Interface',leftIndex,button);left.style.left='0';left.style.top='0';
  const middle=makeImage('Interface',middleIndex,button);middle.style.left=`${lw}px`;middle.style.top='0';middle.style.width=`${Math.max(0,width-lw-rw)}px`;middle.classList.add('dx-button-middle');
  const right=makeImage('Interface',rightIndex,button);right.style.right='0';right.style.left='auto';right.style.top='0';
  const label=document.createElement('div');label.className='dx-button-label';label.textContent=text;button.append(label);return{button,label,middle,leftWidth:lw,rightWidth:rw};
}
function smallButton(text,parent){const height=assetSize('Interface',41)[1];const parts=threePieceButton(text,parent,{type:'SmallButton',leftIndex:41,middleIndex:43,rightIndex:42,width:50,height});parts.button.style.cursor='pointer';return parts.button}
function sourceTabWidth(text){
  const canvas=sourceTabWidth.canvas||(sourceTabWidth.canvas=document.createElement('canvas'));const context=canvas.getContext('2d');context.font=`9px "${SOURCE_FONT}", sans-serif`;return Math.max(60,Math.ceil(context.measureText(text).width));
}
function selectedTabButton(text,parent){
  const tabHeight=assetSize('Interface',19)[1];const width=sourceTabWidth(text);const parts=threePieceButton(text,parent,{type:'SelectedTab',leftIndex:56,middleIndex:58,rightIndex:57,width,height:tabHeight});parts.button.classList.add('chat-options-local-tab-button');parts.button.style.left='0';parts.button.style.top='0';parts.button.style.pointerEvents='none';return parts.button;
}
const checkboxLanguage={
  TransparentCheckBox:'ChatOptionsPanelTransparentLabel',AlertCheckBox:'ChatOptionsPanelShowAlertLabel',HideTabCheckBox:'ChatOptionsPanelHideTabLabel',ReverseListCheckBox:'ChatOptionsPanelReverseLabel',CleanUpCheckBox:'ChatOptionsPanelCleanUpLabel',FadeOutCheckBox:'ChatOptionsPanelFadeOutLabel',
  LocalCheckBox:'ChatOptionsPanelLocalChatLabel',WhisperCheckBox:'ChatOptionsPanelWhisperChatLabel',GroupCheckBox:'ChatOptionsPanelGroupChatLabel',GuildCheckBox:'ChatOptionsPanelGuildChatLabel',ShoutCheckBox:'ChatOptionsPanelShoutChatLabel',GlobalCheckBox:'ChatOptionsPanelGlobalChatLabel',ObserverCheckBox:'ChatOptionsPanelObserverChatLabel',HintCheckBox:'ChatOptionsPanelHintTextLabel',SystemCheckBox:'ChatOptionsPanelSystemTextLabel',GainsCheckBox:'ChatOptionsPanelGainsTextLabel',
};
function checkBox(name,anchorX,y,parent,tab){
  const element=document.createElement('div');element.className='dx-checkbox chat-options-local-checkbox';element.style.cssText=`position:absolute;top:${y}px;cursor:pointer;font-family:"${SOURCE_FONT}",sans-serif`;element.dataset.sourceCheckbox=name;element.dataset.checked=String(tab.checked[name]);parent.append(element);
  const label=document.createElement('span');label.textContent=language(checkboxLanguage[name]);element.append(label);
  const box=document.createElement('img');box.src=asset('GameInter',tab.checked[name]?162:161);box.draggable=false;element.append(box);
  const place=()=>{element.style.left=`${Math.round(anchorX-element.offsetWidth)}px`};place();queueMicrotask(place);
  element.addEventListener('click',()=>{tab.checked[name]=!tab.checked[name];element.dataset.checked=String(tab.checked[name]);box.src=asset('GameInter',tab.checked[name]?162:161)});
}
function renderChatTabChildren(tab,tabRoot,tabButton,tabHeight){
  const width=200,height=200-tabHeight+1,contentY=tabHeight-1;
  tabRoot.style.cssText=`position:absolute;left:0;top:${contentY}px;width:${width}px;height:${height}px;background:rgba(16,8,8,.5);border:1px solid rgb(198,166,99);overflow:hidden;font-family:"${SOURCE_FONT}",sans-serif`;
  const textPanel=document.createElement('div');textPanel.className='chat-options-local-text-panel';textPanel.dataset.sourceType='DXControl';textPanel.dataset.runtimeMessages='none';textPanel.style.cssText=`position:absolute;left:${RESIZE_BUFFER}px;top:${RESIZE_BUFFER}px;width:${Math.max(0,width-14-1-RESIZE_BUFFER*2)}px;height:${Math.max(0,height-RESIZE_BUFFER*2)}px;overflow:hidden`;tabRoot.append(textPanel);
  const scroll=document.createElement('div');scroll.className='dx-scrollbar vertical chat-options-local-scrollbar';scroll.dataset.sourceType='DXVScrollBar';scroll.dataset.neutralRuntime='true';scroll.style.cssText=`position:absolute;left:${width-14-RESIZE_BUFFER}px;top:${RESIZE_BUFFER}px;width:14px;height:${Math.max(0,height-RESIZE_BUFFER*2)}px`;tabRoot.append(scroll);
  const up=makeImage('Interface',44,scroll);up.style.left='1px';up.style.top='1px';
  const down=makeImage('Interface',46,scroll);down.style.left='1px';down.style.top=`${Math.max(1,height-RESIZE_BUFFER*2-13)}px`;
  const thumb=makeImage('Interface',45,scroll);thumb.style.left='1px';thumb.style.top='16px';thumb.classList.add('dx-scroll-thumb');
  const alert=makeImage('GameInter',240,tabButton);alert.style.left='2px';alert.style.top='2px';alert.style.display='none';alert.dataset.sourceType='DXImageControl';alert.dataset.sourceVisible='false';
}
function renderFloatingTab(tab){
  if(tab.floating?.isConnected)return;
  const root=document.createElement('div');root.className='chat-options-local-tab-control';root.dataset.localChatTabId=String(tab.id);root.dataset.sourceType='DXTabControl';root.dataset.localStateOnly='true';root.style.cssText=`position:absolute;left:0;top:0;width:200px;height:200px;z-index:45;pointer-events:auto;font-family:"${SOURCE_FONT}",sans-serif`;stage.append(root);
  const tabButton=selectedTabButton(tab.name,root);const tabHeight=assetSize('Interface',19)[1];const tabRoot=document.createElement('div');tabRoot.className='chat-options-local-chat-tab';tabRoot.dataset.sourceType='ChatTab';tabRoot.dataset.sourceOpacity='0.5';tabRoot.dataset.allowResize='true';root.append(tabRoot);renderChatTabChildren(tab,tabRoot,tabButton,tabHeight);tab.floating=root;
}
function removeTab(id){const index=state.tabs.findIndex(tab=>tab.id===id);if(index<0)return;const[removed]=state.tabs.splice(index,1);removed.floating?.remove();if(state.selectedId===id){const next=state.tabs[index]||state.tabs[index-1]||null;state.selectedId=next?.id??null}document.querySelectorAll('#w-chat-options').forEach(renderChatOptionsState)}
function selectTab(id){state.selectedId=id;document.querySelectorAll('#w-chat-options').forEach(renderChatOptionsState)}
function renderListItem(tab,listBox,index){
  const item=document.createElement('div');item.className='chat-options-local-list-item';item.dataset.localChatListItem=String(tab.id);item.dataset.sourceType='DXListBoxItem';item.style.cssText=`position:absolute;left:0;top:${index*16}px;height:16px;width:${Math.max(0,px(listBox.style.width)-15)}px;box-sizing:border-box;cursor:pointer;color:rgb(198,166,99);background:transparent;font-size:9px;font-family:"${SOURCE_FONT}",sans-serif`;
  if(tab.id===state.selectedId){item.style.color='#fff';item.style.background='rgb(128,64,64)'}item.textContent=tab.name;item.addEventListener('click',()=>selectTab(tab.id));listBox.append(item);
}
function renderPanel(tab,root,layout,listNode){
  const panel=document.createElement('div');panel.className='chat-options-local-panel';panel.dataset.localChatPanel=String(tab.id);panel.dataset.sourceType='ChatOptionsPanel';panel.dataset.localStateOnly='true';
  const x=listNode.localX+listNode.width+5,y=listNode.localY,width=Math.max(0,layout.clientArea.width-x),height=layout.clientArea.height;panel.style.cssText=`position:absolute;left:${x}px;top:${y}px;width:${width}px;height:${height}px;overflow:visible;font-family:"${SOURCE_FONT}",sans-serif`;root.append(panel);
  const chatName=document.createElement('div');chatName.textContent=language('ChatOptionsPanelChatNameLabel');chatName.style.cssText=`position:absolute;top:1px;color:#fff;text-shadow:1px 1px #000;font:11px "${SOURCE_FONT}",sans-serif;white-space:nowrap`;panel.append(chatName);queueMicrotask(()=>{chatName.style.left=`${Math.round(74-chatName.offsetWidth)}px`});
  const textBox=document.createElement('div');textBox.className='dx-textbox chat-options-local-name';textBox.dataset.sourceType='DXTextBox';textBox.style.cssText='position:absolute;left:74px;top:1px;width:80px;height:20px';const input=document.createElement('input');input.value=tab.name;input.style.cssText=`width:100%;height:100%;box-sizing:border-box;background:#000;color:#fff;border:0;outline:0;font-family:"${SOURCE_FONT}",sans-serif`;textBox.append(input);panel.append(textBox);
  input.addEventListener('input',()=>{tab.name=input.value;const floatingLabel=tab.floating?.querySelector('.chat-options-local-tab-button .dx-button-label');if(floatingLabel)floatingLabel.textContent=tab.name;renderChatOptionsState(root)});
  const remove=smallButton(language('ChatOptionsPanelRemoveLabel'),panel);remove.dataset.sourceAction='RemoveButton.MouseClick';remove.style.left='164px';remove.style.top='0';remove.addEventListener('click',()=>removeTab(tab.id));
  for(const [name,anchor,y] of [['TransparentCheckBox',100,40],['AlertCheckBox',216,40],['HideTabCheckBox',100,65],['ReverseListCheckBox',216,65],['CleanUpCheckBox',100,90],['FadeOutCheckBox',216,90],['LocalCheckBox',100,130],['WhisperCheckBox',216,130],['GroupCheckBox',100,155],['GuildCheckBox',216,155],['ShoutCheckBox',100,180],['GlobalCheckBox',216,180],['ObserverCheckBox',100,205],['HintCheckBox',216,205],['SystemCheckBox',100,230],['GainsCheckBox',216,230]])checkBox(name,anchor,y,panel,tab);
}
function renderChatOptionsState(root){
  if(!spec||!chatItem||!template||!root?.isConnected)return;root.querySelectorAll('.chat-options-local-list-item,.chat-options-local-panel').forEach(node=>node.remove());
  const layout=buildWindowLayout(spec,chatItem),listIndex=sourceControlIndex(control=>control.name==='ListBox'),listBox=elementFor(root,listIndex),listNode=layout.nodes[listIndex];if(!listBox||!listNode)return;state.tabs.forEach((tab,index)=>renderListItem(tab,listBox,index));const selected=state.tabs.find(tab=>tab.id===state.selectedId);if(selected)renderPanel(selected,root,layout,listNode);
}
function addLocalTab(root){
  if(!template?.localStateOnly)return;const id=state.nextId++,name=`Window ${state.tabs.length}`,checked={};for(const key of template.checkedTrue||[])checked[key]=true;for(const key of template.checkedFalse||[])checked[key]=false;const tab={id,name,checked,floating:null};state.tabs.push(tab);state.selectedId=id;renderFloatingTab(tab);renderChatOptionsState(root);
}
function attach(root){
  if(!spec||!chatItem||!template||root.dataset.chatOptionsLocalAddAttached==='true')return;const addIndex=sourceControlIndex(control=>String(control.properties?.Label||'').includes('ChatOptionsDialogButtonAdd')),add=elementFor(root,addIndex);if(!add)return;root.dataset.chatOptionsLocalAddAttached='true';root.dataset.constructorPrecreatedLocalTabs=String(state.tabs.length);add.dataset.sourceLocalAction='AddNewTab(null)';add.addEventListener('click',event=>{event.preventDefault();event.stopPropagation();addLocalTab(root)});renderChatOptionsState(root);
}
function scan(node){if(!(node instanceof Element))return;if(node.id==='w-chat-options')queueMicrotask(()=>attach(node));node.querySelectorAll?.('#w-chat-options').forEach(root=>queueMicrotask(()=>attach(root)))}
new MutationObserver(records=>records.forEach(record=>record.addedNodes.forEach(scan))).observe(stage,{childList:true,subtree:true});
fetch('ui-source-spec.json',{cache:'no-store'}).then(response=>{if(!response.ok)throw new Error(`ui-source-spec.json ${response.status}`);return response.json()}).then(value=>{spec=value;chatItem=(spec.windows||[]).find(item=>item.field==='ChatOptionsBox');template=chatItem?.chatOptionsAddNewTabTemplate||null;if(!template?.passed)throw new Error('Chat Options AddNewTab source template missing/not PASS');document.querySelectorAll('#w-chat-options').forEach(attach);console.info('ORIGINS Chat Options AddNewTab local source runtime active; constructor tabs remain 0')}).catch(error=>console.error('Chat Options local runtime unavailable',error));
