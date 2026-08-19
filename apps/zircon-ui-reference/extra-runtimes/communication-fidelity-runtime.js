// Source-faithful CommunicationDialog tab state. Friend/mail/block lists and
// read-mail payloads remain runtime-only; no fake messages or contacts are added.
const stage=document.querySelector('#stage');
const pad=value=>String(value).padStart(5,'0');
const asset=(library,index)=>`assets/${library}/${pad(index)}.png`;
function control(root,name){return root?.querySelector?.(`[data-control-name="${CSS.escape(name)}"]`)||null}
function setVisible(element,visible){if(!element)return;element.hidden=!visible;element.dataset.sourceDynamicVisible=String(visible)}
function setBackground(root,index){
  const element=control(root,'BackgroundImage');if(!element)return;
  const image=element instanceof HTMLImageElement?element:element.querySelector('img');if(image)image.src=asset('Interface',index);
  element.dataset.sourceDynamicIndex=String(index);root.dataset.sourceCommunicationBackground=String(index);
}
function clearReadState(root){
  setVisible(control(root,'ReadTab'),false);
  setVisible(control(root,'ReadReplyButton'),false);
  setVisible(control(root,'ReadDeleteButton'),false);
  root.dataset.sourceReadMail='null';
  root.dataset.sourceReadMailInvented='false';
}
function setTab(root,name){
  const friend=name==='FriendTab',received=name==='ReceivedTab',send=name==='SendTab',block=name==='BlockTab';
  setBackground(root,friend?201:received?202:send?203:204);
  setVisible(control(root,'FriendAddButton'),friend);
  setVisible(control(root,'FriendRemoveButton'),friend);
  setVisible(control(root,'SendButton'),send);
  setVisible(control(root,'BlockAddButton'),block);
  setVisible(control(root,'BlockRemoveButton'),block);
  setVisible(control(root,'ReceivedCollectAllButton'),received);
  setVisible(control(root,'ReceivedDeleteAll'),received);
  setVisible(control(root,'ReceivedNewButton'),received);
  clearReadState(root);
  if(send){
    // Source clears draft fields whenever SendTab is clicked. Keep them empty,
    // including gold=0, rather than preserving/fabricating a draft.
    for(const field of ['SendRecipientBox','SendSubjectBox','SendMessageBox']){
      const element=control(root,field);if(element){element.textContent='';element.dataset.sourceClearedOnSendTab='true'}
    }
    const gold=control(root,'SendGoldBox');if(gold){gold.dataset.value='0';const value=gold.querySelector('.dx-number-value');if(value)value.textContent='0'}
  }
  root.dataset.sourceCommunicationTab=name;
  root.dataset.sourceCommunicationRuntimeLists='FriendList/ReceivedMailList/BlockList runtime-only';
}
function install(root){
  if(!root||root.id!=='w-communication'||root.dataset.sourceCommunicationRuntime==='true')return;
  root.dataset.sourceCommunicationRuntime='true';
  root.dataset.sourceMailInvented='false';root.dataset.sourceFriendDataInvented='false';root.dataset.sourceBlockedDataInvented='false';
  // DXTabControl selects its first usable tab; Communication creates FriendTab first.
  setTab(root,'FriendTab');
  for(const name of ['FriendTab','ReceivedTab','SendTab','BlockTab']){
    const tab=control(root,name);tab?.addEventListener('click',()=>setTab(root,name),true);
  }
  const newButton=control(root,'ReceivedNewButton');newButton?.addEventListener('click',()=>setTab(root,'SendTab'),true);
}
function scan(node){if(!(node instanceof Element))return;if(node.id==='w-communication')queueMicrotask(()=>install(node));node.querySelectorAll?.('#w-communication').forEach(root=>queueMicrotask(()=>install(root)))}
new MutationObserver(records=>records.forEach(record=>record.addedNodes.forEach(scan))).observe(stage,{childList:true,subtree:true});
install(document.querySelector('#w-communication'));
console.info('ORIGINS CommunicationDialog fidelity runtime active: Friend/Received/Send/Block states source-backed; live mail/contact data neutral');
