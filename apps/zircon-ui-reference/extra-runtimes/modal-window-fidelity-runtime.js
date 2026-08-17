// DXWindow.Modal blocks interaction with controls/windows behind the top modal.
// Resolve it from the final manifest so nested MessageBox/Input/ItemAmount and
// any future source modal automatically get the same behavior.
const stage=document.querySelector('#stage');
let spec=null;
function boolFrom(raw,fallback=false){const v=String(raw??'').trim().toLowerCase();return v==='true'?true:v==='false'?false:fallback}
function itemFor(root){if(!spec||!root?.id?.startsWith('w-'))return null;const id=root.id.slice(2);return [...(spec.windows||[]),...(spec.nestedWindows||[])].find(item=>item.id===id)||null}
function mark(root){const item=itemFor(root);if(!item)return;const modal=boolFrom(item.root?.Modal,false);root.dataset.sourceModal=String(modal);if(modal)root.setAttribute('aria-modal','true')}
function modals(){return [...stage.querySelectorAll('.window[data-source-modal="true"],.generic-window[data-source-modal="true"]')].filter(root=>root.isConnected&&!root.hidden&&getComputedStyle(root).display!=='none')}
function z(root){const value=Number.parseInt(getComputedStyle(root).zIndex||root.style.zIndex||'0',10);return Number.isFinite(value)?value:0}
function topModal(){return modals().sort((a,b)=>z(a)-z(b)||[...stage.children].indexOf(a)-[...stage.children].indexOf(b)).at(-1)||null}
function block(event){
  const modal=topModal();if(!modal||!(event.target instanceof Node)||modal.contains(event.target))return;
  // The catalog is QA tooling outside #stage; this listener only sees stage
  // input, exactly where game windows/control interaction lives.
  event.preventDefault();event.stopImmediatePropagation();modal.dataset.lastBlockedModalEvent=event.type;
}
for(const type of ['pointerdown','pointerup','click','dblclick','contextmenu','wheel'])stage.addEventListener(type,block,true);
function scan(node){if(!(node instanceof Element))return;if(node.matches?.('.window,.generic-window'))queueMicrotask(()=>mark(node));node.querySelectorAll?.('.window,.generic-window').forEach(root=>queueMicrotask(()=>mark(root)))}
new MutationObserver(records=>records.forEach(record=>record.addedNodes.forEach(scan))).observe(stage,{childList:true,subtree:true});
fetch('ui-source-spec.json',{cache:'no-store'}).then(r=>{if(!r.ok)throw new Error(`ui-source-spec.json ${r.status}`);return r.json()}).then(value=>{spec=value;stage.querySelectorAll('.window,.generic-window').forEach(mark);console.info('ORIGINS DXWindow.Modal input blocking active')}).catch(error=>console.error('Unable to load modal-window manifest',error));