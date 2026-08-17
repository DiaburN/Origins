import { buildWindowLayout } from './layout-resolver-derived.js';

// Source-faithful DXAnimatedControl reference runtime.
// Zircon timing: frameDelay = AnimationDelay / FrameCount; Loop=false stops on
// BaseIndex + FrameCount - 1. Image offset is re-read for every current frame
// because DXAnimatedControl changes Index and DXImageControl.OnIndexChanged then
// recomputes DisplayArea using Library.GetOffSet(Index) when UseOffSet=true.

const stage=document.querySelector('#stage');
let sourceSpec=null;
const active=new Map();
const pad=value=>String(value).padStart(5,'0');
const asset=(library,index)=>`assets/${library}/${pad(index)}.png`;

function boolFrom(raw,fallback=true){
  const value=String(raw??'').trim().toLowerCase();
  if(value==='true')return true;if(value==='false')return false;return fallback;
}
function intFrom(raw){
  const value=String(raw??'').trim();return /^-?\d+$/.test(value)?Number(value):null;
}
function libraryFrom(raw){return String(raw??'').match(/LibraryFile\.([A-Za-z0-9_]+)/)?.[1]||null}
function delayMs(raw){
  const text=String(raw??'').trim();
  let match=text.match(/TimeSpan\.FromMilliseconds\(\s*([0-9.]+)\s*\)/);if(match)return Number(match[1]);
  match=text.match(/TimeSpan\.FromSeconds\(\s*([0-9.]+)\s*\)/);if(match)return Number(match[1])*1000;
  match=text.match(/TimeSpan\.FromMinutes\(\s*([0-9.]+)\s*\)/);if(match)return Number(match[1])*60000;
  return 0;
}
function meta(library,index){return sourceSpec?.assetMeta?.[library]?.[String(index)]||null}
function itemForRoot(root){
  if(!sourceSpec||!root?.id?.startsWith('w-'))return null;
  const id=root.id.slice(2);return [...(sourceSpec.windows||[]),...(sourceSpec.nestedWindows||[])].find(item=>item.id===id)||null;
}
function imageFor(root,index){
  const element=root.querySelector(`[data-control-index="${index}"]`);
  if(element instanceof HTMLImageElement)return element;
  return element?.querySelector?.('img')||null;
}
function intersect(a,b){
  const left=Math.max(a.left,b.left),top=Math.max(a.top,b.top),right=Math.min(a.right,b.right),bottom=Math.min(a.bottom,b.bottom);
  return {left,top,right,bottom,width:Math.max(0,right-left),height:Math.max(0,bottom-top)};
}
function parentClip(node){
  let parent=node.parent,clip=null;
  while(parent){
    const area={left:parent.x,top:parent.y,right:parent.x+parent.width,bottom:parent.y+parent.height};
    clip=clip?intersect(clip,area):area;parent=parent.parent;
  }
  return clip;
}
function applyFrameGeometry(element,node,library,index,useOffset){
  const frame=meta(library,index)||{};
  const offsetX=useOffset?Number(frame.offsetX||0):0,offsetY=useOffset?Number(frame.offsetY||0):0;
  const baseAppliedX=Number(node.sourceImageOffsetX||0),baseAppliedY=Number(node.sourceImageOffsetY||0);
  const left=node.x+offsetX-baseAppliedX,top=node.y+offsetY-baseAppliedY;
  element.style.left=`${Math.round(left)}px`;element.style.top=`${Math.round(top)}px`;
  element.dataset.sourceAnimationOffset=`${offsetX},${offsetY}`;
  if(frame.width)element.dataset.sourceAnimationFrameWidth=String(frame.width);
  if(frame.height)element.dataset.sourceAnimationFrameHeight=String(frame.height);

  const clip=parentClip(node);
  if(clip&&frame.width&&frame.height){
    const box={left,top,right:left+frame.width,bottom:top+frame.height};const visible=intersect(box,clip);
    if(visible.width<=0||visible.height<=0){element.style.visibility='hidden';return}
    element.style.visibility='';
    const insetTop=Math.max(0,visible.top-box.top),insetRight=Math.max(0,box.right-visible.right),insetBottom=Math.max(0,box.bottom-visible.bottom),insetLeft=Math.max(0,visible.left-box.left);
    element.style.clipPath=(insetTop||insetRight||insetBottom||insetLeft)?`inset(${insetTop}px ${insetRight}px ${insetBottom}px ${insetLeft}px)`:'';
  }
}
function installAnimation(root,item,layout,controlIndex){
  const control=item.controls?.[controlIndex],node=layout.nodes?.[controlIndex];
  if(!control||!node||control.type!=='DXAnimatedControl')return;
  const p=control.properties||{},library=libraryFrom(p.LibraryFile),base=intFrom(p.BaseIndex),count=intFrom(p.FrameCount);
  const animated=boolFrom(p.Animated,true),loop=boolFrom(p.Loop,true),totalDelay=delayMs(p.AnimationDelay),useOffset=boolFrom(p.UseOffSet,false);
  if(!library||base===null||base<0||!count||count<=1||!animated||!totalDelay)return;
  const element=imageFor(root,controlIndex);if(!element)return;
  const key=`${root.id}:${controlIndex}`;if(active.has(key))return;
  const start=performance.now();
  element.dataset.sourceAnimationPolicy='DXAnimatedControl.Process';
  element.dataset.sourceAnimationRange=`${base}-${base+count-1}`;
  element.dataset.sourceAnimationDelayMs=String(totalDelay);element.dataset.sourceAnimationLoop=String(loop);

  const tick=now=>{
    if(!root.isConnected||!element.isConnected){active.delete(key);return}
    const elapsed=Math.max(0,now-start);let frame;
    if(!loop&&elapsed>=totalDelay)frame=count-1;
    else {
      const local=loop?(elapsed%totalDelay):elapsed;
      const frameDelay=totalDelay/count;
      frame=Math.min(count-1,Math.floor(local/frameDelay));
    }
    const index=base+frame;
    if(element.dataset.sourceAnimationIndex!==String(index)){
      element.src=asset(library,index);element.dataset.sourceAnimationIndex=String(index);
      applyFrameGeometry(element,node,library,index,useOffset);
    }
    if(!loop&&elapsed>=totalDelay){element.dataset.sourceAnimationComplete='true';active.delete(key);return}
    const handle=requestAnimationFrame(tick);active.set(key,handle);
  };
  active.set(key,requestAnimationFrame(tick));
}
function installRoot(root){
  if(!sourceSpec||!root?.id?.startsWith('w-'))return;
  const item=itemForRoot(root);if(!item)return;
  const layout=buildWindowLayout(sourceSpec,item);
  for(let index=0;index<(item.controls||[]).length;index++)installAnimation(root,item,layout,index);
}

new MutationObserver(records=>{
  for(const record of records)for(const node of record.addedNodes){
    if(!(node instanceof Element))continue;
    if(node.matches?.('.window,.generic-window'))queueMicrotask(()=>installRoot(node));
    node.querySelectorAll?.('.window,.generic-window').forEach(root=>queueMicrotask(()=>installRoot(root)));
  }
}).observe(stage,{childList:true,subtree:true});

fetch('ui-source-spec.json',{cache:'no-store'})
  .then(response=>{if(!response.ok)throw new Error(`ui-source-spec.json ${response.status}`);return response.json()})
  .then(spec=>{sourceSpec=spec;stage.querySelectorAll('.window,.generic-window').forEach(installRoot);console.info(`ORIGINS DXAnimatedControl runtime active; source controls=${spec.renderCoverageAudit?.animatedControls||0}`)})
  .catch(error=>console.error('Unable to load Zircon animation manifest',error));
