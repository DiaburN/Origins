// Source-derived behaviors for the GameScene controls that are visible at
// startup. No live player/map/buff/group/timer payloads are fabricated.
const stage=document.querySelector('#stage');
let spec=null;
const pad=value=>String(value).padStart(5,'0');
const asset=(library,index)=>`assets/${library}/${pad(index)}.png`;

function floatFrom(raw,fallback){const v=String(raw??'').trim().replace(/[fFdDmM]$/,'');return /^-?(?:\d+(?:\.\d*)?|\.\d+)$/.test(v)?Number(v):fallback}
function itemFor(root){if(!spec||!root?.id?.startsWith('w-'))return null;const id=root.id.slice(2);return [...(spec.windows||[]),...(spec.nestedWindows||[])].find(item=>item.id===id)||null}
function sizeOf(index){const s=spec?.assetSizes?.Interface?.[String(index)];return Array.isArray(s)&&s.length===2?[Number(s[0]),Number(s[1])]:[0,0]}
function imageIndex(element){return Number(String(element?.getAttribute?.('src')||'').match(/Interface\/(\d+)\.png$/)?.[1]||-1)}

function hideBuiltInClose(root){
  // DXWindow creates CloseButton internally; the source constructors for Belt,
  // MiniMap and Buff explicitly set CloseButton.Visible=false.
  root.querySelectorAll(':scope > .close').forEach(element=>element.style.display='none');
  root.dataset.sourceCloseButtonVisible='false';
}
function applyRootOpacity(root){
  const item=itemFor(root);if(!item)return;const opacity=Math.max(0,Math.min(1,floatFrom(item.root?.Opacity,1)));
  root.style.opacity=String(opacity);root.dataset.sourceRootOpacity=String(opacity);
}

function installBelt(root){
  if(!root)return;hideBuiltInClose(root);applyRootOpacity(root);
  for(const cell of root.querySelectorAll('.dx-item-grid-cell-source')){
    if(cell.querySelector(':scope > .source-belt-key'))continue;
    const slot=Number.parseInt(cell.dataset.slot||'',10);if(!Number.isInteger(slot))continue;
    const label=document.createElement('span');label.className='source-belt-key';label.textContent=String((slot+1)%10);
    label.style.position='absolute';label.style.left='-2px';label.style.top='-1px';label.style.fontSize='10.6667px';label.style.fontStyle='italic';label.style.color='rgb(198,166,99)';label.style.textShadow='0 -1px #000,-1px 0 #000,1px 0 #000,0 1px #000';label.style.pointerEvents='none';label.style.zIndex='3';
    cell.append(label);
  }
  root.dataset.sourceBeltKeys='BeltDialog.OnClientAreaChanged: ((slot+1)%10), FontSize(8F) italic, (-2,-1)';
}

function resizeMiniMapFrame(root,width,height){
  const pieces=[...root.querySelectorAll(':scope > .source-window-frame-piece')];
  const byIndex=index=>pieces.filter(element=>imageIndex(element)===index);
  const [topW,topH]=sizeOf(0),[sideW]=sizeOf(1),[,bottomH]=sizeOf(2),[,titleH]=sizeOf(3);
  for(const top of byIndex(0)){top.style.width=`${width}px`;top.style.height=`${topH}px`}
  const sides=byIndex(1);if(sides[0]){sides[0].style.left='0';sides[0].style.height=`${Math.max(0,height-topH)}px`}if(sides[1]){sides[1].style.left=`${Math.max(0,width-sideW)}px`;sides[1].style.height=`${Math.max(0,height-topH)}px`}
  for(const fill of byIndex(3)){fill.style.left=`${sideW}px`;fill.style.width=`${Math.max(0,width-sideW*2)}px`;fill.style.height=`${titleH}px`}
  const rightAt=(index,x,y=null)=>{const [w]=sizeOf(index);for(const piece of byIndex(index)){piece.style.left=`${Math.max(0,x-w)}px`;if(y!==null)piece.style.top=`${y}px`}};
  rightAt(5,width,topH+titleH-3);rightAt(12,width,0);
  for(const bottom of byIndex(2)){bottom.style.top=`${Math.max(0,height-bottomH)}px`;bottom.style.width=`${width}px`}
  const [,leftBottomH]=sizeOf(8);for(const piece of byIndex(8))piece.style.top=`${Math.max(0,height-leftBottomH)}px`;
  const [,rightBottomH]=sizeOf(9);rightAt(9,width,Math.max(0,height-rightBottomH));
}
function control(root,name){return root.querySelector(`[data-control-name="${name}"]`)}
function setMiniButtons(root,visible){for(const name of ['SizeButton','TransparencyButton','BigMapButton']){const element=control(root,name);if(element)element.hidden=!visible}}
function placeMiniButtons(root){
  const area=control(root,'Panel');const top=area?Number.parseFloat(area.style.top||'0'):0;
  let y=top;
  for(const name of ['SizeButton','TransparencyButton','BigMapButton']){
    const element=control(root,name);if(!element)continue;
    const width=element.offsetWidth||element.naturalWidth||Number.parseFloat(element.style.width||'0');const height=element.offsetHeight||element.naturalHeight||Number.parseFloat(element.style.height||'0');
    element.style.left=`${Math.max(0,root.offsetWidth-width-3)}px`;element.style.top=`${y}px`;y+=height;
  }
}
function setMiniMapSize(root,large){
  const oldWidth=root.offsetWidth||200,oldHeight=root.offsetHeight||200;const right=Number.parseFloat(root.style.left||'0')+oldWidth;const width=large?300:200,height=large?300:200;
  root.style.width=`${width}px`;root.style.height=`${height}px`;root.style.left=`${right-width}px`;
  resizeMiniMapFrame(root,width,height);
  const panel=control(root,'Panel');if(panel){panel.style.width=`${Math.max(0,(panel.offsetWidth||0)+(width-oldWidth))}px`;panel.style.height=`${Math.max(0,(panel.offsetHeight||0)+(height-oldHeight))}px`}
  placeMiniButtons(root);root.dataset.sourceMiniMapLarge=String(large);root.dataset.sourceMiniMapSize=`${width}x${height}`;
}
function installMiniMap(root){
  if(!root||root.dataset.sourceMiniMapRuntime==='true')return;
  root.dataset.sourceMiniMapRuntime='true';hideBuiltInClose(root);applyRootOpacity(root);setMiniButtons(root,false);
  root.addEventListener('pointerenter',()=>setMiniButtons(root,true));root.addEventListener('pointerleave',()=>setMiniButtons(root,false));
  const transparency=control(root,'TransparencyButton');if(transparency)transparency.addEventListener('click',event=>{
    event.preventDefault();event.stopPropagation();const transparent=root.dataset.sourceMiniMapTransparent!=='true';root.dataset.sourceMiniMapTransparent=String(transparent);root.style.opacity=transparent?'0.5':'1';
    const image=transparency instanceof HTMLImageElement?transparency:transparency.querySelector('img');if(image)image.src=asset('GameInter',transparent?131:130);
  });
  const size=control(root,'SizeButton');if(size)size.addEventListener('click',event=>{event.preventDefault();event.stopPropagation();setMiniMapSize(root,root.dataset.sourceMiniMapLarge!=='true')});
  placeMiniButtons(root);
}
function apply(){
  const belt=document.querySelector('#w-belt');if(belt)installBelt(belt);
  const mini=document.querySelector('#w-minimap');if(mini)installMiniMap(mini);
  const buffs=document.querySelector('#w-buffs');if(buffs){hideBuiltInClose(buffs);applyRootOpacity(buffs)}
}
new MutationObserver(()=>queueMicrotask(apply)).observe(stage,{childList:true,subtree:true});
fetch('ui-source-spec.json',{cache:'no-store'}).then(r=>{if(!r.ok)throw new Error(`ui-source-spec.json ${r.status}`);return r.json()}).then(value=>{spec=value;apply();console.info('ORIGINS source default-HUD details: Belt keys + MiniMap hover/size/transparency + Buff opacity')}).catch(error=>console.error('Unable to load default HUD detail manifest',error));