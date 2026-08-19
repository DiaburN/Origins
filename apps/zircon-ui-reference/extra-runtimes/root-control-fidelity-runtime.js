// Apply root-level DXControl defaults that are not represented by a child node:
// generic DXWindow roots are Movable=true by constructor; image-backed
// DXImageControl roots inherit Movable=false unless a dialog explicitly sets it.
const stage=document.querySelector('#stage');
let spec=null;

function boolFrom(raw,fallback){const v=String(raw??'').trim().toLowerCase();return v==='true'?true:v==='false'?false:fallback}
function floatFrom(raw,fallback){const v=String(raw??'').trim().replace(/[fFdDmM]$/,'');return /^-?(?:\d+(?:\.\d*)?|\.\d+)$/.test(v)?Number(v):fallback}
function itemFor(root){if(!spec||!root?.id?.startsWith('w-'))return null;const id=root.id.slice(2);return [...(spec.windows||[]),...(spec.nestedWindows||[])].find(item=>item.id===id)||null}
function movable(root,item){const fallback=root.classList.contains('generic-window');return boolFrom(item?.root?.Movable,fallback)}
function applyRoot(root){
  const item=itemFor(root);if(!item)return;
  const canMove=movable(root,item);root.dataset.sourceMovable=String(canMove);
  const opacity=Math.max(0,Math.min(1,floatFrom(item.root?.Opacity,1)));root.style.opacity=String(opacity);root.dataset.sourceRootOpacity=String(opacity);
  const enabled=boolFrom(item.root?.IsEnabled,true);root.dataset.sourceRootEnabled=String(enabled);
}
function isInteractive(target){return target instanceof Element&&Boolean(target.closest('[data-control-index],button,input,textarea,select,a,.ui-button,.close,.dx-checkbox,.dx-scrollbar,.dx-combobox,.dx-numberbox,.dx-soundbar'))}

// window-runtime.js installs its drag listener on each root in bubble phase. A
// capture guard on the stage suppresses only background/title dragging for roots
// that Zircon marks non-movable, while leaving source controls clickable.
stage.addEventListener('pointerdown',event=>{
  if(event.button!==0||isInteractive(event.target))return;
  const root=event.target instanceof Element?event.target.closest('.window,.generic-window'):null;if(!root)return;
  const item=itemFor(root);if(!item||movable(root,item))return;
  event.preventDefault();event.stopPropagation();root.dataset.sourceBlockedSyntheticDrag='true';
},true);
function scan(node){if(!(node instanceof Element))return;if(node.matches?.('.window,.generic-window'))queueMicrotask(()=>applyRoot(node));node.querySelectorAll?.('.window,.generic-window').forEach(root=>queueMicrotask(()=>applyRoot(root)))}
new MutationObserver(records=>records.forEach(record=>record.addedNodes.forEach(scan))).observe(stage,{childList:true,subtree:true});
fetch('ui-source-spec.json',{cache:'no-store'}).then(r=>{if(!r.ok)throw new Error(`ui-source-spec.json ${r.status}`);return r.json()}).then(value=>{spec=value;stage.querySelectorAll('.window,.generic-window').forEach(applyRoot);console.info('ORIGINS source root opacity/mobility guard active')}).catch(error=>console.error('Unable to load root control fidelity manifest',error));