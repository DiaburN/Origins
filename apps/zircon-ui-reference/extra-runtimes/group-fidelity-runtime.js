// Source-faithful GroupDialog neutral/base behavior. Group membership, LFG rows
// and AllowGroup acknowledgement are server/runtime data and are never fabricated.
const stage=document.querySelector('#stage');
let spec=null;
const pad=value=>String(value).padStart(5,'0');
const asset=(library,index)=>`assets/${library}/${pad(index)}.png`;
function control(root,name){return root?.querySelector?.(`[data-control-name="${CSS.escape(name)}"]`)||null}
function setEnabled(element,value){if(!element)return;element.dataset.sourceDynamicEnabled=String(Boolean(value));element.dispatchEvent(new CustomEvent('origins:source-enabled-changed',{bubbles:true}))}
function setChecked(box,value){if(!box)return;box.dataset.sourceChecked=String(Boolean(value));const image=box.querySelector(':scope > img');if(image)image.src=asset('GameInter',value?162:161)}
function nested(className){return spec?.nestedWindows?.find(item=>item.sourceClass===className)||null}
function openNested(className){const item=nested(className);if(!item)return null;const existing=document.querySelector(`#w-${CSS.escape(item.id)}`);if(existing)return existing;document.querySelector(`[data-window-id="${CSS.escape(item.id)}"]`)?.click();return document.querySelector(`#w-${CSS.escape(item.id)}`)}
function install(root){
  if(!root||root.id!=='w-group'||root.dataset.sourceGroupBaseRuntime==='true'||!spec)return;
  root.dataset.sourceGroupBaseRuntime='true';root.dataset.sourceGroupMembers='0 neutral; runtime ClientPlayerInfo list';root.dataset.sourceGroupMembersInvented='false';root.dataset.sourceAllowGroup='false until server acknowledgement';root.dataset.sourceLfgRows='runtime ClientLookingForGroup';root.dataset.sourceLfgRowsInvented='false';
  const allow=control(root,'AllowGroupBox');if(allow){setChecked(allow,false);allow.dataset.sourceReadonlyCustomClick='true';allow.addEventListener('click',event=>{event.preventDefault();event.stopImmediatePropagation();setChecked(allow,false);root.dataset.sourceNetworkAction='C.GroupSwitch { Allow = true }';root.dataset.sourceNetworkActionExecuted='false'},true)}
  setEnabled(control(root,'RemoveButton'),false);setEnabled(control(root,'OptionsButton'),false);
  for(const row of root.querySelectorAll('[data-control-name^="LFGRows"],[data-control-name*="GroupLFGRow"]')){row.hidden=true;row.dataset.sourceRuntimeVisible='ClientLookingForGroup only'}
  const add=control(root,'AddButton');if(add&&add.dataset.sourceGroupAddBound!=='true'){
    add.dataset.sourceGroupAddBound='true';add.addEventListener('click',event=>{event.preventDefault();event.stopImmediatePropagation();const modal=openNested('DXInputWindow');if(!modal)return;modal.dataset.sourceModal='true';modal.dataset.sourceGroupInvite='true';modal.dataset.sourceConstructorMessage='CEnvir.Language.GroupDialogAddButtonConfirmMessage';modal.dataset.sourceConstructorCaption='CEnvir.Language.GroupDialogAddButtonConfirmCaption';modal.dataset.sourceValidation='Globals.CharacterReg';modal.dataset.sourceNetworkAction='C.GroupInvite';modal.dataset.sourceNetworkActionExecuted='false';const confirm=[...modal.querySelectorAll('[data-control-name]')].find(el=>String(el.dataset.controlName||'').endsWith('ConfirmButton'));setEnabled(confirm,false)},true)
  }
}
function scan(node){if(!(node instanceof Element))return;if(node.id==='w-group')queueMicrotask(()=>install(node));node.querySelectorAll?.('#w-group').forEach(root=>queueMicrotask(()=>install(root)))}
new MutationObserver(records=>records.forEach(record=>record.addedNodes.forEach(scan))).observe(stage,{childList:true,subtree:true});
fetch('ui-source-spec.json',{cache:'no-store'}).then(r=>{if(!r.ok)throw new Error(`ui-source-spec.json ${r.status}`);return r.json()}).then(value=>{spec=value;install(document.querySelector('#w-group'));console.info('ORIGINS Group source runtime active: 0 members, AllowGroup server-acknowledged, Add uses source DXInputWindow')}).catch(error=>console.error('Unable to load Group source manifest',error));
