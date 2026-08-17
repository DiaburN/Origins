// DXControl drops mouse input while IsEnabled=false. Enforce that invariant at
// the source-control boundary so no specialized/generic renderer can accidentally
// execute a click handler for a disabled Zircon control.
const stage=document.querySelector('#stage');
let spec=null;
function boolFrom(raw,fallback=true){const v=String(raw??'').trim().toLowerCase();return v==='true'?true:v==='false'?false:fallback}
function itemFor(root){if(!spec||!root?.id?.startsWith('w-'))return null;const id=root.id.slice(2);return [...(spec.windows||[]),...(spec.nestedWindows||[])].find(item=>item.id===id)||null}
function sourceControl(element){
  const root=element.closest('.window,.generic-window');if(!root)return null;const item=itemFor(root);if(!item)return null;
  const index=Number.parseInt(element.dataset.controlIndex||'',10);if(!Number.isInteger(index))return null;
  const control=item.controls?.[index];return control?{root,item,control}:null;
}
function apply(root){
  const item=itemFor(root);if(!item)return;
  for(const element of root.querySelectorAll('[data-control-index]')){
    const index=Number.parseInt(element.dataset.controlIndex||'',10);if(!Number.isInteger(index))continue;const control=item.controls?.[index];if(!control)continue;
    element.dataset.sourceEnabled=String(boolFrom(control.properties?.IsEnabled,true));
  }
}
for(const type of ['pointerdown','pointerup','click','dblclick','contextmenu'])stage.addEventListener(type,event=>{
  if(!(event.target instanceof Element))return;
  const element=event.target.closest('[data-control-index]');if(!element)return;
  const resolved=sourceControl(element);if(!resolved)return;
  if(boolFrom(resolved.control.properties?.IsEnabled,true))return;
  event.preventDefault();event.stopImmediatePropagation();resolved.root.dataset.lastBlockedDisabledControl=resolved.control.name||'';
},true);
function scan(node){if(!(node instanceof Element))return;if(node.matches?.('.window,.generic-window'))queueMicrotask(()=>apply(node));node.querySelectorAll?.('.window,.generic-window').forEach(root=>queueMicrotask(()=>apply(root)))}
new MutationObserver(records=>records.forEach(record=>record.addedNodes.forEach(scan))).observe(stage,{childList:true,subtree:true});
fetch('ui-source-spec.json',{cache:'no-store'}).then(r=>{if(!r.ok)throw new Error(`ui-source-spec.json ${r.status}`);return r.json()}).then(value=>{spec=value;stage.querySelectorAll('.window,.generic-window').forEach(apply);console.info('ORIGINS DXControl IsEnabled input guard active')}).catch(error=>console.error('Unable to load enabled-state manifest',error));