// NPCDialog overrides DXWindow.Draw() and composes its own GameInter frame.
// Neutral reference = header 380 + footer 382, zero runtime rows/page text.
const stage=document.querySelector('#stage');
let spec=null;
const pad=value=>String(value).padStart(5,'0');
const asset=(library,index)=>`assets/${library}/${pad(index)}.png`;
function itemFor(root){if(!spec||root?.id!=='w-npc')return null;return spec.windows?.find(item=>item.id==='npc')||null}
function control(root,name){return root.querySelector(`[data-control-name="${CSS.escape(name)}"]`)}
function frameImage(root,index,x,y){const img=document.createElement('img');img.src=asset('GameInter',index);img.className='ui-img source-npc-frame-piece';img.draggable=false;img.style.left=`${x}px`;img.style.top=`${y}px`;img.style.pointerEvents='none';root.prepend(img);return img}
function renderFrame(root,item){
  root.querySelectorAll(':scope > .source-window-frame-piece,:scope > .source-npc-frame-piece').forEach(el=>el.remove());
  root.querySelectorAll(':scope > .close:not([data-control-index])').forEach(el=>el.remove());
  root.style.width='380px';root.style.height='204px';root.style.background='transparent';root.style.boxShadow='0 0 8px rgba(0,0,0,.5)';
  frameImage(root,380,0,0);frameImage(root,382,0,140);
  const header=root.querySelector(':scope > .generic-window-header');if(header)header.style.display='none';
  const container=control(root,'PageTextContainer');if(container){container.style.left='15px';container.style.top='45px';container.style.width='350px';container.style.height='145px'}
  const text=control(root,'PageText');if(text){text.textContent='';text.style.width='350px';text.style.height='0px';text.dataset.runtimeNpcPageText='neutral'}
  const scrollbar=control(root,'ScrollBar');if(scrollbar){scrollbar.style.left='350px';scrollbar.style.top='45px';scrollbar.style.width='14px';scrollbar.style.height='145px'}
  const close=control(root,'CloseButton');if(close){close.style.left='345px';close.style.top='3px'}
  root.dataset.sourceNpcFrame='GameInter 380 + 0*381 + 382';root.dataset.runtimeNpcData='neutral/no fabricated NPC page or buttons';
}
function install(root){if(!(root instanceof Element)||root.id!=='w-npc')return;const item=itemFor(root);if(!item?.npcCustomFrame)return;renderFrame(root,item)}
function scan(node){if(!(node instanceof Element))return;if(node.id==='w-npc')queueMicrotask(()=>install(node));node.querySelectorAll?.('#w-npc').forEach(root=>queueMicrotask(()=>install(root)))}
new MutationObserver(records=>records.forEach(record=>record.addedNodes.forEach(scan))).observe(stage,{childList:true,subtree:true});
fetch('ui-source-spec.json',{cache:'no-store'}).then(r=>{if(!r.ok)throw new Error(`ui-source-spec.json ${r.status}`);return r.json()}).then(value=>{spec=value;const root=document.querySelector('#w-npc');if(root)install(root);console.info('ORIGINS NPCDialog custom GameInter frame active')}).catch(error=>console.error('Unable to load NPCDialog fidelity manifest',error));