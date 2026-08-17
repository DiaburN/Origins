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

// ---------------------------------------------------------------------------
// Source-neutral desktop + repeated small-control fidelity
// ---------------------------------------------------------------------------
// This reference has no live MapObject.User, chat history, map texture, belt
// contents or item rows. Keep those surfaces neutral rather than baking sample
// player/game data into the source reconstruction.
const PRIMARY='#c6a663';
const BLACK='#000000';

function literalInt(raw,fallback=0){
  const value=String(raw??'').trim();return /^-?\d+$/.test(value)?Number(value):fallback;
}
function sourceColour(raw,fallback){
  const value=String(raw??'').trim();
  if(!value)return fallback;
  if(/Constants\.PrimaryColour/.test(value))return PRIMARY;
  if(/Color\.Empty\b/.test(value))return 'transparent';
  const named={Black:'#000000',White:'#ffffff',Cyan:'#00ffff',Red:'#ff0000',Green:'#008000',Yellow:'#ffff00',Lime:'#00ff00',Gray:'#808080',Grey:'#808080',Silver:'#c0c0c0'};
  const key=value.match(/Color\.([A-Za-z]+)/)?.[1];
  if(key&&named[key])return named[key];
  let match=value.match(/Color\.FromArgb\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)/);
  if(match)return `rgba(${match[2]},${match[3]},${match[4]},${Number(match[1])/255})`;
  match=value.match(/Color\.FromArgb\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)/);
  return match?`rgb(${match[1]},${match[2]},${match[3]})`:fallback;
}
function controlText(control){
  if(typeof control?.resolvedText==='string')return control.resolvedText;
  const p=control?.properties||{};
  for(const raw of [p.Label,p.Text]){
    const text=String(raw??'');
    const quoted=text.match(/(?:Text\s*=\s*)?"([^"]*)"/);if(quoted)return quoted[1];
  }
  return '';
}
function neutralDesktop(){
  stage.classList.add('source-neutral-desktop');
  stage.querySelectorAll(':scope > .runtime-label,:scope > .chat,:scope > .minimap,:scope > .belt').forEach(element=>element.remove());

  // MainPanel.BeforeDraw owns these fills. Without MapObject.User values the
  // neutral source state must not render them at 100%.
  const runtimeMainImages=new Set(['00052.png','00054.png','00058.png']);
  for(const element of stage.querySelectorAll(':scope > img.ui-img')){
    const file=String(element.getAttribute('src')||'').split('/').pop();
    if(runtimeMainImages.has(file))element.remove();
    // MC vs SC is class-dependent. The handcrafted desktop previously chose MC.
    if(file==='00062.png'&&Number.parseFloat(element.style.top||'0')>=700)element.remove();
  }
  stage.dataset.mainPanelRuntimeState='neutral: no player stats, HP/MP/FP fills, class-specific MC/SC or sample messages';
}

function checkboxLabelColour(control){
  const raw=String(control?.properties?.Label??'');
  const match=raw.match(/ForeColour\s*=\s*([^,}\n]+)/);
  return sourceColour(match?.[1],PRIMARY);
}
function installCheckBox(element,control){
  if(!(element instanceof Element)||element.dataset.sourceCheckboxFidelity==='true')return;
  const p=control?.properties||{};
  const label=element.querySelector(':scope > span');
  const box=element.querySelector(':scope > img');
  if(!label||!box)return;

  const padding=Math.max(0,literalInt(p.LabelBoxPadding,0));
  const readOnly=boolFrom(p.ReadOnly,false);
  const enabled=boolFrom(p.IsEnabled,true);
  label.textContent=controlText(control);
  label.style.position='absolute';label.style.left='0';label.style.top='0';
  label.style.color=checkboxLabelColour(control);
  label.style.fontSize='10.6667px';label.style.lineHeight='14px';
  label.style.textShadow=`1px 0 ${BLACK},0 1px ${BLACK},-1px 0 ${BLACK},0 -1px ${BLACK}`;
  box.style.position='absolute';box.style.margin='0';
  element.style.display='block';element.style.gap='0';element.style.padding='0';
  element.dataset.sourceCheckboxFidelity='true';
  element.dataset.sourceReadOnly=String(readOnly);element.dataset.sourceEnabled=String(enabled);element.dataset.sourceLabelBoxPadding=String(padding);

  const place=()=>{
    const labelWidth=Math.ceil(label.getBoundingClientRect().width);
    const boxWidth=box.naturalWidth||box.width||16,boxHeight=box.naturalHeight||box.height||16;
    box.style.left=`${labelWidth+padding}px`;box.style.top='1px';
    element.style.width=`${labelWidth+padding+boxWidth}px`;element.style.height=`${boxHeight}px`;
  };
  if(box.complete)queueMicrotask(place);else box.addEventListener('load',place,{once:true});
  requestAnimationFrame(place);

  element.addEventListener('click',event=>{
    if(enabled&&!readOnly)return;
    event.preventDefault();event.stopImmediatePropagation();
  },true);
}
function installColourControl(element,control){
  if(!(element instanceof Element))return;
  const p=control?.properties||{};
  element.style.border=`1px solid ${PRIMARY}`;
  element.style.background=sourceColour(p.BackColour,'#000000');
  element.dataset.sourceAllowNoColour=String(boolFrom(p.AllowNoColour,false));
  element.dataset.sourceColourControl='DXColourControl: DrawTexture=true, Border=true, Size default 40x15';
}
function cleanRuntimeReviewText(root){
  root.querySelectorAll('.dx-tree-runtime').forEach(element=>{element.textContent='';element.dataset.runtimeRows='not fabricated'});
  root.querySelectorAll('.runtime-palette-area > span').forEach(element=>element.remove());
  root.querySelectorAll('.generic-source-badge').forEach(element=>element.remove());
  const heading=root.querySelector(':scope > .generic-window-header');
  if(heading&&root.dataset.nestedSourceClass&&heading.textContent.trim()===root.dataset.nestedSourceClass)heading.textContent='';
}
function installSourceFidelity(root){
  if(!sourceSpec||!(root instanceof Element)||!root.id?.startsWith('w-'))return;
  const item=itemForRoot(root);if(!item)return;
  const controls=item.controls||[];
  for(const element of root.querySelectorAll('[data-control-index]')){
    const index=Number.parseInt(element.dataset.controlIndex||'',10);if(!Number.isInteger(index))continue;
    const control=controls[index];if(!control)continue;
    if(control.type==='DXCheckBox')installCheckBox(element,control);
    else if(control.type==='DXColourControl')installColourControl(element,control);
  }
  cleanRuntimeReviewText(root);
}
function fidelityScan(node){
  neutralDesktop();
  if(!(node instanceof Element))return;
  if(node.matches?.('.window,.generic-window'))queueMicrotask(()=>installSourceFidelity(node));
  node.querySelectorAll?.('.window,.generic-window').forEach(root=>queueMicrotask(()=>installSourceFidelity(root)));
}

const fidelityStyle=document.createElement('style');
fidelityStyle.textContent='.stage.source-neutral-desktop:before{display:none!important}.stage.source-neutral-desktop .generic-source-badge{display:none!important}';
document.head.append(fidelityStyle);
neutralDesktop();

new MutationObserver(records=>{
  for(const record of records)for(const node of record.addedNodes){
    if(!(node instanceof Element))continue;
    if(node.matches?.('.window,.generic-window'))queueMicrotask(()=>installRoot(node));
    node.querySelectorAll?.('.window,.generic-window').forEach(root=>queueMicrotask(()=>installRoot(root)));
    fidelityScan(node);
  }
}).observe(stage,{childList:true,subtree:true});

fetch('ui-source-spec.json',{cache:'no-store'})
  .then(response=>{if(!response.ok)throw new Error(`ui-source-spec.json ${response.status}`);return response.json()})
  .then(spec=>{
    sourceSpec=spec;
    neutralDesktop();
    stage.querySelectorAll('.window,.generic-window').forEach(root=>{installRoot(root);installSourceFidelity(root)});
    console.info(`ORIGINS DXAnimatedControl runtime active; source controls=${spec.renderCoverageAudit?.animatedControls||0}`);
    console.info('ORIGINS source-neutral desktop + DXCheckBox/DXColourControl fidelity runtime active');
  })
  .catch(error=>console.error('Unable to load Zircon animation/fidelity manifest',error));