// Deterministic ChatTextBox behavior from Zircon. The actual chat contents,
// PM recipient, linked items and network send remain runtime user/server data.
const stage=document.querySelector('#stage');
const catalog=document.querySelector('#window-list');
const MODES=['Local','Whisper','Group','Guild','Shout','Global','Observer'];
let mode=0;

function control(root,name){return root.querySelector(`[data-control-name="${CSS.escape(name)}"]`)}
function labelFor(button){return button?.querySelector?.(':scope > .dx-button-label,:scope > .source-button-label')||null}
function setMode(root,value){
  mode=((value%MODES.length)+MODES.length)%MODES.length;
  const button=control(root,'ChatModeButton'),label=labelFor(button);
  if(label)label.textContent=MODES[mode];
  if(button){button.dataset.sourceChatMode=MODES[mode];button.title=''}
  root.dataset.sourceChatMode=MODES[mode];
}
function toggleCatalogWindow(id){
  const existing=stage.querySelector(`#w-${CSS.escape(id)}`);
  if(existing){existing.remove();return}
  catalog?.querySelector(`[data-window-id="${CSS.escape(id)}"]`)?.click();
}
function install(root){
  if(!(root instanceof Element)||root.id!=='w-chat-input'||root.dataset.sourceChatRuntime==='true')return;
  root.dataset.sourceChatRuntime='true';root.dataset.runtimeChatData='neutral/no fabricated chat text, PM recipient or linked items';
  setMode(root,0);
  const modeButton=control(root,'ChatModeButton');
  modeButton?.addEventListener('click',event=>{event.preventDefault();event.stopPropagation();setMode(root,mode+1)});
  const options=control(root,'OptionsButton');
  options?.addEventListener('click',event=>{event.preventDefault();event.stopPropagation();toggleCatalogWindow('chat-options')});
}
function scan(node){if(!(node instanceof Element))return;if(node.id==='w-chat-input')queueMicrotask(()=>install(node));node.querySelectorAll?.('#w-chat-input').forEach(root=>queueMicrotask(()=>install(root)))}
new MutationObserver(records=>records.forEach(record=>record.addedNodes.forEach(scan))).observe(stage,{childList:true,subtree:true});
const current=document.querySelector('#w-chat-input');if(current)install(current);
console.info('ORIGINS ChatTextBox deterministic Local→Observer mode runtime active');