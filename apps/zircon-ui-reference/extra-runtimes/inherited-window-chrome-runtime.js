// Consume source-derived inherited DXWindow child state promoted during build.
const stage=document.querySelector('#stage');
let spec=null;
function boolFrom(raw,fallback){const v=String(raw??'').trim().toLowerCase();return v==='true'?true:v==='false'?false:fallback}
function itemFor(root){if(!spec||!root?.id?.startsWith('w-'))return null;const id=root.id.slice(2);return [...(spec.windows||[]),...(spec.nestedWindows||[])].find(item=>item.id===id)||null}
function apply(root){
  if(!(root instanceof Element)||!root.classList.contains('generic-window'))return;
  const item=itemFor(root);if(!item)return;const p=item.root||{};
  const close=root.querySelector(':scope > .close,:scope > .nested-close-button');
  if(close&&p.CloseButtonVisible!==undefined){const visible=boolFrom(p.CloseButtonVisible,true);close.style.display=visible?'':'none';close.dataset.sourceInheritedVisible=String(visible)}
  if(close&&p.CloseButtonEnabled!==undefined){const enabled=boolFrom(p.CloseButtonEnabled,true);close.style.pointerEvents=enabled?'':'none';close.style.filter=enabled?'':`brightness(${51/217})`;close.dataset.sourceInheritedEnabled=String(enabled)}
  const title=root.querySelector(':scope > .generic-window-header');
  if(title&&p.TitleLabelVisible!==undefined){const visible=boolFrom(p.TitleLabelVisible,true);title.style.display=visible?'':'none';title.dataset.sourceInheritedVisible=String(visible)}
}
function scan(node){if(!(node instanceof Element))return;if(node.matches?.('.generic-window'))queueMicrotask(()=>apply(node));node.querySelectorAll?.('.generic-window').forEach(root=>queueMicrotask(()=>apply(root)))}
new MutationObserver(records=>records.forEach(record=>record.addedNodes.forEach(scan))).observe(stage,{childList:true,subtree:true});
fetch('ui-source-spec.json',{cache:'no-store'}).then(r=>{if(!r.ok)throw new Error(`ui-source-spec.json ${r.status}`);return r.json()}).then(value=>{spec=value;stage.querySelectorAll('.generic-window').forEach(apply);console.info('ORIGINS inherited DXWindow CloseButton/TitleLabel source state active')}).catch(error=>console.error('Unable to load inherited window chrome manifest',error));