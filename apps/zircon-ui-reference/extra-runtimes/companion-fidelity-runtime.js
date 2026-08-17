// CompanionDialog mixed custom draw: only the deterministic empty-slot helper
// artwork is projected here. Companion body, item data and bars stay runtime.
const stage=document.querySelector('#stage');
let spec=null;
const pad=value=>String(value).padStart(5,'0');
const asset=(library,index)=>`assets/${library}/${pad(index)}.png`;
function itemFor(root){if(!spec||root?.id!=='w-companion')return null;return spec.windows?.find(item=>item.id==='companion')||null}
function apply(root){
  if(!(root instanceof Element)||root.id!=='w-companion')return;const item=itemFor(root);if(!item)return;const controls=item.controls||[];
  for(const element of root.querySelectorAll('[data-control-index]')){
    const i=Number.parseInt(element.dataset.controlIndex||'',10);if(!Number.isInteger(i))continue;const control=controls[i],hint=control?.emptyPlaceholderAsset;if(!hint)continue;
    let image=element.querySelector(':scope > .source-companion-empty-slot');
    if(!image){image=document.createElement('img');image.className='source-companion-empty-slot';image.draggable=false;image.style.position='absolute';image.style.pointerEvents='none';element.append(image)}
    image.src=asset(hint.library,hint.index);image.style.opacity=String(hint.opacity);
    const place=()=>{const w=image.naturalWidth||0,h=image.naturalHeight||0;image.style.left=`${Math.round(((element.clientWidth||36)-w)/2)}px`;image.style.top=`${Math.round(((element.clientHeight||36)-h)/2)}px`};
    if(image.complete)queueMicrotask(place);else image.addEventListener('load',place,{once:true});
    element.dataset.sourceEmptyPlaceholder=`${hint.library}#${hint.index}@${hint.opacity}`;
  }
  root.dataset.runtimeCompanionData='neutral/no fabricated companion model, items, bars or values';
}
function scan(node){if(!(node instanceof Element))return;if(node.id==='w-companion')queueMicrotask(()=>apply(node));node.querySelectorAll?.('#w-companion').forEach(root=>queueMicrotask(()=>apply(root)))}
new MutationObserver(records=>records.forEach(record=>record.addedNodes.forEach(scan))).observe(stage,{childList:true,subtree:true});
fetch('ui-source-spec.json',{cache:'no-store'}).then(r=>{if(!r.ok)throw new Error(`ui-source-spec.json ${r.status}`);return r.json()}).then(value=>{spec=value;const root=document.querySelector('#w-companion');if(root)apply(root);console.info('ORIGINS Companion deterministic empty-slot artwork active')}).catch(error=>console.error('Unable to load Companion fidelity manifest',error));