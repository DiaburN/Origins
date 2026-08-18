// Source-faithful Group -> GroupLFGInputWindow local flow. Existing LFG records,
// members and server updates stay runtime-only; the no-existing-LFG branch is the
// truthful neutral reference state.
const stage=document.querySelector('#stage');
let spec=null;
function control(root,name){return root?.querySelector?.(`[data-control-name="${CSS.escape(name)}"]`)||null}
function setButtonEnabled(button,enabled){if(!button)return;button.dataset.sourceDynamicEnabled=String(enabled);button.setAttribute('aria-disabled',String(!enabled));button.style.pointerEvents=enabled?'auto':'none';button.style.opacity=enabled?'1':'.55'}
function setButtonText(button,text){if(!button)return;const label=button.querySelector('.dx-button-label');if(label)label.textContent=text;button.dataset.sourceDynamicLabel=text}
function nestedItem(){return spec?.nestedWindows?.find(item=>item.sourceClass==='GroupLFGInputWindow')||null}
function openNested(){
  const item=nestedItem();if(!item)return null;
  let root=document.querySelector(`#w-${CSS.escape(item.id)}`);if(root)return root;
  document.querySelector(`[data-window-id="${CSS.escape(item.id)}"]`)?.click();
  return document.querySelector(`#w-${CSS.escape(item.id)}`);
}
function numberValue(box){const value=Number(box?.dataset?.value??4);return Number.isFinite(value)?Math.max(2,Math.min(15,Math.trunc(value))):4}
function setNumber(box,value){
  if(!box)return;value=Math.max(2,Math.min(15,Math.trunc(value)));box.dataset.value=String(value);box.dataset.sourceMinValue='2';box.dataset.sourceMaxValue='Globals.GroupLimit=15';box.dataset.sourceChange='1';
  const field=box.querySelector('.dx-number-value');if(field)field.textContent=String(value);
}
function bindCount(box){
  if(!box||box.dataset.sourceGroupCountBound==='true')return;box.dataset.sourceGroupCountBound='true';setNumber(box,4);
  const images=[...box.querySelectorAll('img')];
  const down=images.find(image=>/GameInter\/01011\.png$/.test(image.src));
  const up=images.find(image=>/GameInter\/01010\.png$/.test(image.src));
  down?.addEventListener('click',event=>{event.preventDefault();event.stopImmediatePropagation();setNumber(box,numberValue(box)-1)},true);
  up?.addEventListener('click',event=>{event.preventDefault();event.stopImmediatePropagation();setNumber(box,numberValue(box)+1)},true);
}
function prepareModal(root){
  if(!root||root.dataset.sourceGroupLfgPrepared==='true')return;
  root.dataset.sourceGroupLfgPrepared='true';root.dataset.sourceModal='true';root.setAttribute('aria-modal','true');
  root.dataset.sourceExistingLfg='none (runtime unavailable)';root.dataset.sourceGroupMembers='runtime-only';root.dataset.sourceLfgDuration='Globals.LookingForGroupMinutes=60';
  const name=control(root,'NameTextBox'),count=control(root,'CountNumberBox'),type=control(root,'TypeComboBox');
  const enable=control(root,'EnableButton'),disable=control(root,'DisableButton');
  setButtonText(enable,'Enable');setButtonEnabled(enable,false);setButtonEnabled(disable,false);bindCount(count);
  if(type){type.dataset.sourceInitialValue='PvE';type.dataset.sourceOptions='PvE,PvP'}
  if(name){
    name.contentEditable='true';name.spellcheck=false;name.setAttribute('role','textbox');name.dataset.sourceMinLength='2';name.dataset.sourceMaxLength='16';name.dataset.sourceRuntimeEditable='true';
    name.addEventListener('input',()=>{const length=(name.textContent||'').length;setButtonEnabled(enable,length>=2&&length<=16)});
    name.addEventListener('keydown',event=>{if(event.key==='Escape'){event.preventDefault();root.remove()}else if(event.key==='Enter'&&enable?.dataset.sourceDynamicEnabled==='true'){event.preventDefault();enable.click()}});
  }
  enable?.addEventListener('click',event=>{
    if(enable.dataset.sourceDynamicEnabled!=='true'){event.preventDefault();event.stopImmediatePropagation();return}
    event.preventDefault();event.stopImmediatePropagation();root.dataset.sourceNetworkAction='C.GroupLFGUpdate Enabled=true';root.dataset.sourceNetworkActionExecuted='false';root.remove();
  },true);
  disable?.addEventListener('click',event=>{event.preventDefault();event.stopImmediatePropagation()},true);
}
function installGroup(root){
  if(!root||root.id!=='w-group'||root.dataset.sourceGroupLfgRuntime==='true')return;
  root.dataset.sourceGroupLfgRuntime='true';
  control(root,'LFGButton')?.addEventListener('click',event=>{
    event.preventDefault();event.stopImmediatePropagation();
    const modal=openNested();if(modal)queueMicrotask(()=>prepareModal(modal));
  },true);
}
function scan(node){if(!(node instanceof Element))return;if(node.id==='w-group')queueMicrotask(()=>installGroup(node));if(node.dataset?.nestedSourceClass==='GroupLFGInputWindow')queueMicrotask(()=>prepareModal(node));node.querySelectorAll?.('#w-group').forEach(root=>queueMicrotask(()=>installGroup(root)));node.querySelectorAll?.('[data-nested-source-class="GroupLFGInputWindow"]').forEach(root=>queueMicrotask(()=>prepareModal(root)))}
new MutationObserver(records=>records.forEach(record=>record.addedNodes.forEach(scan))).observe(stage,{childList:true,subtree:true});
fetch('ui-source-spec.json',{cache:'no-store'}).then(r=>{if(!r.ok)throw new Error(`ui-source-spec.json ${r.status}`);return r.json()}).then(value=>{spec=value;installGroup(document.querySelector('#w-group'));stage.querySelectorAll('[data-nested-source-class="GroupLFGInputWindow"]').forEach(prepareModal);console.info('ORIGINS Group LFG source flow active: PvE/Count4/name validation; live group/server data neutral')}).catch(error=>console.error('Unable to load Group LFG manifest',error));
