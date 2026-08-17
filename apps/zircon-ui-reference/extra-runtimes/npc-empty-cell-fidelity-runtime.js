// Two NPC dialogs manually draw Interface #31 at 20% opacity when their linked
// item cell is empty. Linked item contents remain runtime and are not fabricated.
const stage=document.querySelector('#stage');
const pad=value=>String(value).padStart(5,'0');
const asset=(library,index)=>`assets/${library}/${pad(index)}.png`;
const TARGETS=new Set(['w-npc-wedding-ring','w-npc-accessory-reset']);
function apply(root){
  if(!(root instanceof Element)||!TARGETS.has(root.id))return;
  const cell=root.querySelector('.dx-item-grid-cell-source,.generic-cell,[data-control-type="DXItemCell"]');if(!cell)return;
  let image=cell.querySelector(':scope > .source-npc-empty-cell-hint');
  if(!image){image=document.createElement('img');image.className='source-npc-empty-cell-hint';image.draggable=false;image.style.position='absolute';image.style.pointerEvents='none';image.style.opacity='0.2';cell.append(image)}
  image.src=asset('Interface',31);
  const place=()=>{const w=image.naturalWidth||0,h=image.naturalHeight||0;image.style.left=`${Math.round(((cell.clientWidth||36)-w)/2)}px`;image.style.top=`${Math.round(((cell.clientHeight||36)-h)/2)}px`};
  if(image.complete)queueMicrotask(place);else image.addEventListener('load',place,{once:true});
  cell.dataset.sourceEmptyHint='Interface#31@0.2';root.dataset.runtimeLinkedItem='neutral/no fabricated item';
}
function scan(node){if(!(node instanceof Element))return;if(TARGETS.has(node.id))queueMicrotask(()=>apply(node));node.querySelectorAll?.('.window,.generic-window').forEach(root=>{if(TARGETS.has(root.id))queueMicrotask(()=>apply(root))})}
new MutationObserver(records=>records.forEach(record=>record.addedNodes.forEach(scan))).observe(stage,{childList:true,subtree:true});
for(const id of TARGETS){const root=document.querySelector(`#${id}`);if(root)apply(root)}
console.info('ORIGINS deterministic NPC empty-cell Interface#31 hints active');