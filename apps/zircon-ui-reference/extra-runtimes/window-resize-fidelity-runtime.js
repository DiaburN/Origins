// Source-faithful DXControl resize behavior for the GameScene windows that set
// AllowResize=true. Zircon uses a 9px edge/corner buffer, not a synthetic HTML
// resize handle. Runtime game data is not involved.
const stage=document.querySelector('#stage');
let spec=null;
let state=null;
const RESIZE_BUFFER=9;
const CELL_STEP=35;
const CELL_SIZE=36;
const INACTIVE='rgb(99,83,50)';

function boolFrom(raw,fallback){const v=String(raw??'').trim().toLowerCase();return v==='true'?true:v==='false'?false:fallback}
function itemFor(root){if(!spec||!root?.id?.startsWith('w-'))return null;const id=root.id.slice(2);return [...(spec.windows||[]),...(spec.nestedWindows||[])].find(item=>item.id===id)||null}
function rootPx(root,name){return Number.parseFloat(root.style[name]||'0')||0}
function element(root,name){return root.querySelector(`[data-control-name="${CSS.escape(name)}"]`)}
function clamp(v,min,max){return Math.min(max,Math.max(min,v))}
function stageSize(){return [stage.clientWidth||1024,stage.clientHeight||768]}

function edgeAt(root,event,item){
  if(!boolFrom(item?.root?.AllowResize,false))return null;
  const rect=root.getBoundingClientRect();
  const canW=boolFrom(item.root?.CanResizeWidth,true),canH=boolFrom(item.root?.CanResizeHeight,true);
  const x=event.clientX-rect.left,y=event.clientY-rect.top;
  const left=canW&&x<RESIZE_BUFFER,right=canW&&rect.width-x<RESIZE_BUFFER;
  const top=canH&&y<RESIZE_BUFFER,bottom=canH&&rect.height-y<RESIZE_BUFFER;
  return left||right||top||bottom?{left,right,top,bottom}:null;
}
function cursor(edges){
  if((edges.left&&edges.top)||(edges.right&&edges.bottom))return'nwse-resize';
  if((edges.right&&edges.top)||(edges.left&&edges.bottom))return'nesw-resize';
  if(edges.left||edges.right)return'ew-resize';
  return'ns-resize';
}

function acceptableBelt(width,height){
  // BeltDialog.GetAcceptableResize(): first convert requested root Size to the
  // source ClientArea for HasTopBorder/HasTitle/HasFooter=false.
  const areaW=width-18,areaH=height-12;
  let x=Math.ceil((areaW-10)/CELL_SIZE),y=Math.ceil((areaH-10)/CELL_SIZE);
  if(areaH>areaW)x=0;else y=0;
  x=clamp(x,1,10);y=clamp(y,1,10);
  let clientW=x*CELL_STEP+1,clientH=y*CELL_STEP+1;
  if(x>=y)clientW+=10;else clientH+=10;
  return [clientW+18,clientH+18];
}
function acceptable(item,width,height,startHeight){
  width=Math.max(RESIZE_BUFFER*2,width);height=Math.max(RESIZE_BUFFER*2,height);
  if(item.id==='belt')return acceptableBelt(width,height);
  if(item.id==='minimap')return [width,Math.max(31,height)]; // DXWindow.HeaderSize
  if(item.id==='chat-input')return [width,startHeight]; // CanResizeHeight=false
  return [width,height];
}

function beltKey(cell,slot){
  const label=document.createElement('span');label.className='source-belt-key';label.textContent=String((slot+1)%10);
  label.style.cssText='position:absolute;left:-2px;top:-1px;font-size:10.6667px;font-style:italic;color:rgb(198,166,99);text-shadow:0 -1px #000,-1px 0 #000,1px 0 #000,0 1px #000;pointer-events:none;z-index:3';
  cell.append(label);
}
function reflowBelt(root){
  const grid=element(root,'Grid');if(!grid)return;
  const W=root.offsetWidth,H=root.offsetHeight;
  const horizontal=H<=W;
  const count=clamp(Math.round(((horizontal?W:H)-29)/CELL_STEP),1,10);
  const cols=horizontal?count:1,rows=horizontal?1:count;
  const width=cols*CELL_STEP+1,height=rows*CELL_STEP+1;
  grid.style.left='9px';grid.style.top='9px';grid.style.width=`${width}px`;grid.style.height=`${height}px`;grid.style.gridTemplateColumns=`repeat(${cols},36px)`;
  grid.replaceChildren();
  for(let i=0;i<count;i++){
    const cell=document.createElement('div');cell.className='generic-cell';cell.dataset.slot=String(i);cell.style.border=`1px solid ${INACTIVE}`;cell.style.position='relative';
    beltKey(cell,i);grid.append(cell);
  }
  root.dataset.sourceBeltResize=`${cols}x${rows}`;
}
function reflowMiniMap(root){
  const W=root.offsetWidth,H=root.offsetHeight;
  const panel=element(root,'Panel');if(panel){panel.style.left='3px';panel.style.top='31px';panel.style.width=`${Math.max(0,W-6)}px`;panel.style.height=`${Math.max(0,H-28)}px`}
  let y=31;
  for(const name of ['SizeButton','TransparencyButton','BigMapButton']){
    const button=element(root,name);if(!button)continue;
    const bw=button.offsetWidth||20,bh=button.offsetHeight||20;button.style.left=`${Math.max(0,W-bw-3)}px`;button.style.top=`${y}px`;y+=bh;
  }
  root.dataset.sourceMiniMapResize=`${W}x${H}`;
}
function reflowChat(root){
  const W=root.offsetWidth;
  const mode=element(root,'ChatModeButton'),text=element(root,'TextBox'),options=element(root,'OptionsButton');
  const modeW=mode?.offsetWidth||60,optionsW=options?.offsetWidth||50;
  const clientW=W-18,textW=Math.max(0,clientW-modeW-10-optionsW);
  if(mode){mode.style.left='9px';mode.style.top='8px'}
  if(text){text.style.left=`${9+modeW+5}px`;text.style.top='9px';text.style.width=`${textW}px`;text.style.height='100px'}
  if(options){options.style.left=`${9+textW+modeW+10}px`;options.style.top='8px'}
  root.dataset.sourceChatResize=`width=${W}; text=${textW}`;
}
function reflowQuestTracker(root){
  const W=root.offsetWidth,H=root.offsetHeight;
  const scroll=element(root,'ScrollBar'),panel=element(root,'TextPanel');
  const innerH=Math.max(0,H-RESIZE_BUFFER*2);
  if(panel){panel.style.left='0px';panel.style.top='9px';panel.style.width=`${Math.max(0,W-24)}px`;panel.style.height=`${innerH}px`}
  if(scroll){scroll.style.left=`${Math.max(0,W-23)}px`;scroll.style.top='9px';scroll.style.width='14px';scroll.style.height=`${innerH}px`;scroll.dataset.sourceVisibleSize=String(innerH)}
  root.dataset.sourceQuestTrackerResize=`${W}x${H}`;
}
function reflow(root,item){
  if(item.id==='belt')reflowBelt(root);
  else if(item.id==='minimap')reflowMiniMap(root);
  else if(item.id==='chat-input')reflowChat(root);
  else if(item.id==='quest-tracker')reflowQuestTracker(root);
  root.dispatchEvent(new CustomEvent('origins:source-resize',{bubbles:false,detail:{width:root.offsetWidth,height:root.offsetHeight}}));
}

function startResize(event,root,item,edges){
  const [stageW,stageH]=stageSize();
  state={root,item,edges,pointerId:event.pointerId,startX:event.clientX,startY:event.clientY,left:rootPx(root,'left'),top:rootPx(root,'top'),width:root.offsetWidth,height:root.offsetHeight,stageW,stageH};
  root.dataset.sourceResizing='true';root.style.cursor=cursor(edges);
  root.setPointerCapture?.(event.pointerId);
  event.preventDefault();event.stopImmediatePropagation();
}
function moveResize(event){
  if(!state||event.pointerId!==state.pointerId)return;
  const s=state,dx=event.clientX-s.startX,dy=event.clientY-s.startY;
  let left=s.left,top=s.top,width=s.width,height=s.height;
  if(s.edges.left){left=s.left+dx;width=s.width-dx}else if(s.edges.right)width=s.width+dx;
  if(s.edges.top){top=s.top+dy;height=s.height-dy}else if(s.edges.bottom)height=s.height+dy;
  if(left<0){width+=left;left=0}if(top<0){height+=top;top=0}
  if(left+width>s.stageW)width=s.stageW-left;if(top+height>s.stageH)height=s.stageH-top;
  const oldW=width,oldH=height;[width,height]=acceptable(s.item,width,height,s.height);
  if(s.edges.left)left-=width-oldW;if(s.edges.top)top-=height-oldH;
  left=clamp(left,0,Math.max(0,s.stageW-width));top=clamp(top,0,Math.max(0,s.stageH-height));
  s.root.style.left=`${Math.round(left)}px`;s.root.style.top=`${Math.round(top)}px`;s.root.style.width=`${Math.round(width)}px`;s.root.style.height=`${Math.round(height)}px`;
  reflow(s.root,s.item);event.preventDefault();
}
function endResize(event){
  if(!state||event.pointerId!==state.pointerId)return;
  const root=state.root;root.releasePointerCapture?.(event.pointerId);root.dataset.sourceResizing='false';root.style.cursor='';state=null;event.preventDefault();
}

stage.addEventListener('pointerdown',event=>{
  if(event.button!==0||state)return;
  const root=event.target instanceof Element?event.target.closest('.window,.generic-window'):null;if(!root)return;
  const item=itemFor(root),edges=edgeAt(root,event,item);if(edges)startResize(event,root,item,edges);
},true);
stage.addEventListener('pointermove',event=>{
  if(state){moveResize(event);return}
  const root=event.target instanceof Element?event.target.closest('.window,.generic-window'):null;if(!root)return;
  const item=itemFor(root),edges=edgeAt(root,event,item);if(edges)root.style.cursor=cursor(edges);else if(root.dataset.sourceResizing!=='true')root.style.cursor='';
},true);
stage.addEventListener('pointerup',endResize,true);stage.addEventListener('pointercancel',endResize,true);

function installRoot(root){const item=itemFor(root);if(!item||!boolFrom(item.root?.AllowResize,false))return;root.dataset.sourceAllowResize='true';root.dataset.sourceResizeBuffer=String(RESIZE_BUFFER);reflow(root,item);
  if(item.id==='quest-tracker'&&root.dataset.sourceQuestHover!=='true'){
    root.dataset.sourceQuestHover='true';root.addEventListener('pointerenter',()=>root.style.opacity='0.3');root.addEventListener('pointerleave',()=>root.style.opacity='0');
  }
}
function scan(node){if(!(node instanceof Element))return;if(node.matches?.('.window,.generic-window'))queueMicrotask(()=>installRoot(node));node.querySelectorAll?.('.window,.generic-window').forEach(root=>queueMicrotask(()=>installRoot(root)))}
new MutationObserver(records=>records.forEach(record=>record.addedNodes.forEach(scan))).observe(stage,{childList:true,subtree:true});
fetch('ui-source-spec.json',{cache:'no-store'}).then(r=>{if(!r.ok)throw new Error(`ui-source-spec.json ${r.status}`);return r.json()}).then(value=>{spec=value;stage.querySelectorAll('.window,.generic-window').forEach(installRoot);console.info('ORIGINS Zircon 9px edge/corner resize runtime active')}).catch(error=>console.error('Unable to load source resize manifest',error));