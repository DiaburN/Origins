// Reflow exact DXWindow Interface pieces whenever a source window changes size.
// This supports runtime states such as Monster expand/collapse and later resize.
const stage=document.querySelector('#stage');
let spec=null;
const pad=value=>String(value).padStart(5,'0');
const asset=(library,index)=>`assets/${library}/${pad(index)}.png`;
function boolFrom(raw,fallback){const v=String(raw??'').trim().toLowerCase();return v==='true'?true:v==='false'?false:fallback}
function itemFor(root){if(!spec||!root?.id?.startsWith('w-'))return null;const id=root.id.slice(2);return [...(spec.windows||[]),...(spec.nestedWindows||[])].find(item=>item.id===id)||null}
function size(index){const value=spec?.assetSizes?.Interface?.[String(index)];return Array.isArray(value)?[Number(value[0]),Number(value[1])]:[0,0]}
function piece(root,index,x,y,width=null,height=null){
  const el=document.createElement('img');el.src=asset('Interface',index);el.className='ui-img source-window-frame-piece';el.draggable=false;el.style.position='absolute';el.style.left=`${Math.round(x)}px`;el.style.top=`${Math.round(y)}px`;el.style.pointerEvents='none';
  if(width!==null){el.style.width=`${Math.max(0,Math.round(width))}px`;el.style.objectFit='fill'}if(height!==null){el.style.height=`${Math.max(0,Math.round(height))}px`;el.style.objectFit='fill'}
  root.prepend(el);return el;
}
function reflow(root){
  if(!(root instanceof Element)||!root.classList.contains('generic-window'))return;const item=itemFor(root);if(!item)return;
  const p=item.root||{},W=Math.round(root.getBoundingClientRect().width||parseFloat(root.style.width)||0),H=Math.round(root.getBoundingClientRect().height||parseFloat(root.style.height)||0);if(W<=0||H<=0)return;
  root.querySelectorAll(':scope > .source-window-frame-piece').forEach(el=>el.remove());
  const hasTop=boolFrom(p.HasTopBorder,true),hasTitle=boolFrom(p.HasTitle,true),hasFooter=boolFrom(p.HasFooter,false),slim=boolFrom(p.SlimFooter,false);
  const topIndex=hasTop?0:2,[,topH]=size(topIndex),[sideW]=size(1);piece(root,topIndex,0,0,W,topH);let y=topH;piece(root,1,0,y,sideW,Math.max(0,H-y));piece(root,1,Math.max(0,W-sideW),y,sideW,Math.max(0,H-y));
  if(hasTitle){const [,titleH]=size(3);piece(root,3,sideW,y,Math.max(0,W-sideW*2),titleH);y+=titleH;piece(root,4,0,y-3);const [rw]=size(5);piece(root,5,Math.max(0,W-rw),y-3)}
  const lc=hasTop?11:25,rc=hasTop?12:26;piece(root,lc,0,0);const [rcw]=size(rc);piece(root,rc,Math.max(0,W-rcw),0);
  if(!hasFooter){
    let blank=0;if(slim){const [,sh]=size(126);piece(root,126,0,Math.max(0,H-sh),W,sh);blank=Math.max(0,sh-2)}
    const [,bh]=size(2);piece(root,2,0,Math.max(0,H-bh-blank),W,bh);const [,lh]=size(8);piece(root,8,0,Math.max(0,H-lh-blank));const [rw,rh]=size(9);piece(root,9,Math.max(0,W-rw),Math.max(0,H-rh-blank));
  }else{
    const [,fh]=size(126);piece(root,126,0,Math.max(0,H-fh),W,fh);let off=fh;const [,ih]=size(10);piece(root,10,sideW,Math.max(0,H-ih-off),Math.max(0,W-sideW*2),ih);off+=ih;const [,bh]=size(2);piece(root,2,0,Math.max(0,H-off-bh),W,bh);off+=bh;const [,lh]=size(6);piece(root,6,0,Math.max(0,H-off-lh+3));const [rw,rh]=size(7);piece(root,7,Math.max(0,W-rw),Math.max(0,H-off-rh+3));
  }
  const close=root.querySelector(':scope > .close,:scope > .nested-close-button');if(close){const [cw]=size(15);close.style.left=`${Math.max(0,W-cw-3)}px`;close.style.top='3px'}
  root.dataset.sourceFrameReflow=`${W}x${H}`;
}
function scan(node){if(!(node instanceof Element))return;if(node.matches?.('.generic-window'))queueMicrotask(()=>reflow(node));node.querySelectorAll?.('.generic-window').forEach(root=>queueMicrotask(()=>reflow(root)))}
const observer=new MutationObserver(records=>{for(const record of records){if(record.type==='childList')record.addedNodes.forEach(scan);else if(record.type==='attributes'&&record.target instanceof Element&&record.target.matches('.generic-window'))queueMicrotask(()=>reflow(record.target))}});
observer.observe(stage,{childList:true,subtree:true,attributes:true,attributeFilter:['style']});
fetch('ui-source-spec.json',{cache:'no-store'}).then(r=>{if(!r.ok)throw new Error(`ui-source-spec.json ${r.status}`);return r.json()}).then(value=>{spec=value;stage.querySelectorAll('.generic-window').forEach(reflow);console.info('ORIGINS exact DXWindow frame reflow active')}).catch(error=>console.error('Unable to load window frame reflow manifest',error));