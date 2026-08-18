// DXControl.IsEnabled is derived from the control's own Enabled flag AND its
// parent chain. Enforce that invariant at the source-control boundary so a child
// cannot receive input through a disabled Zircon parent. Initializers use
// `Enabled = ...`; IsEnabled is the computed runtime result, not the source flag.
const stage=document.querySelector('#stage');
let spec=null;
function boolFrom(raw,fallback=true){const v=String(raw??'').trim().toLowerCase();return v==='true'?true:v==='false'?false:fallback}
function itemFor(root){if(!spec||!root?.id?.startsWith('w-'))return null;const id=root.id.slice(2);return [...(spec.windows||[]),...(spec.nestedWindows||[])].find(item=>item.id===id)||null}
function parentName(control){const raw=String(control?.properties?.Parent??'this').trim();return /^[A-Za-z_][A-Za-z0-9_]*$/.test(raw)&&raw!=='this'?raw:null}
function ownEnabled(properties){const p=properties||{};return boolFrom(p.Enabled,p.IsEnabled===undefined?true:boolFrom(p.IsEnabled,true))}
function computedEnabled(item,control,seen=new Set()){
  if(!item||!control)return true;
  const name=String(control.name||'');if(name&&seen.has(name))return ownEnabled(control.properties);if(name)seen.add(name);
  if(!ownEnabled(control.properties))return false;
  const parent=parentName(control);
  if(!parent)return ownEnabled(item.root||{});
  const parentControl=(item.controls||[]).find(candidate=>candidate.name===parent);
  return parentControl?computedEnabled(item,parentControl,seen):ownEnabled(item.root||{});
}
function sourceControl(element){
  const root=element.closest('.window,.generic-window');if(!root)return null;const item=itemFor(root);if(!item)return null;
  const index=Number.parseInt(element.dataset.controlIndex||'',10);if(!Number.isInteger(index))return null;
  const control=item.controls?.[index];return control?{root,item,control,index}:null;
}
function apply(root){
  const item=itemFor(root);if(!item)return;
  for(const element of root.querySelectorAll('[data-control-index]')){
    const index=Number.parseInt(element.dataset.controlIndex||'',10);if(!Number.isInteger(index))continue;const control=item.controls?.[index];if(!control)continue;
    const enabled=computedEnabled(item,control);element.dataset.sourceOwnEnabled=String(ownEnabled(control.properties));element.dataset.sourceEnabled=String(enabled);
    element.setAttribute('aria-disabled',String(!enabled));
    if(!enabled)element.classList.add('source-disabled-control');else element.classList.remove('source-disabled-control');
  }
}
for(const type of ['pointerdown','pointerup','click','dblclick','contextmenu'])stage.addEventListener(type,event=>{
  if(!(event.target instanceof Element))return;
  const element=event.target.closest('[data-control-index]');if(!element)return;
  const resolved=sourceControl(element);if(!resolved)return;
  if(computedEnabled(resolved.item,resolved.control))return;
  event.preventDefault();event.stopImmediatePropagation();resolved.root.dataset.lastBlockedDisabledControl=resolved.control.name||'';
},true);
function scan(node){if(!(node instanceof Element))return;if(node.matches?.('.window,.generic-window'))queueMicrotask(()=>apply(node));node.querySelectorAll?.('.window,.generic-window').forEach(root=>queueMicrotask(()=>apply(root)))}
new MutationObserver(records=>records.forEach(record=>record.addedNodes.forEach(scan))).observe(stage,{childList:true,subtree:true});
fetch('ui-source-spec.json',{cache:'no-store'}).then(r=>{if(!r.ok)throw new Error(`ui-source-spec.json ${r.status}`);return r.json()}).then(value=>{spec=value;stage.querySelectorAll('.window,.generic-window').forEach(apply);console.info('ORIGINS DXControl Enabled/parent-chain IsEnabled input guard active')}).catch(error=>console.error('Unable to load enabled-state manifest',error));
