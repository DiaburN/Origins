// Reproduce per-instance DXVScrollBar / DXHScrollBar child skins.
// Some Zircon dialogs override the default Interface 44/46/45 controls (for
// example Group LFG uses 61/62/60 and a transparent, borderless root).
const stage=document.querySelector('#stage');
let spec=null;
const pad=value=>String(value).padStart(5,'0');
const asset=(library,index)=>`assets/${library}/${pad(index)}.png`;
const PRIMARY='rgb(198,166,99)';

function boolFrom(raw,fallback){const v=String(raw??'').trim().toLowerCase();return v==='true'?true:v==='false'?false:fallback}
function itemFor(root){if(!spec||!root?.id?.startsWith('w-'))return null;const id=root.id.slice(2);return [...(spec.windows||[]),...(spec.nestedWindows||[])].find(item=>item.id===id)||null}
function colour(raw,fallback){const v=String(raw??'').trim();if(/Color\.Empty\b/.test(v))return 'transparent';if(/Color\.Black\b/.test(v))return '#000';if(/Constants\.PrimaryColour/.test(v))return PRIMARY;let m=v.match(/Color\.FromArgb\(\s*(?:\d+\s*,\s*)?(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)/);return m?`rgb(${m[1]},${m[2]},${m[3]})`:fallback}
function childSpec(raw,defaultIndex){
  const text=String(raw??'');
  const indexMatch=text.match(/\bIndex\s*=\s*(-?\d+)/);
  const libraryMatch=text.match(/\bLibraryFile\s*=\s*LibraryFile\.([A-Za-z0-9_]+)/);
  return {index:indexMatch?Number(indexMatch[1]):defaultIndex,library:libraryMatch?.[1]||'Interface'};
}
function applyChildImage(image,spec){
  if(!image)return;
  const disabled=spec.index<0||spec.library==='None';
  if(disabled){image.removeAttribute('src');image.style.display='none';image.dataset.sourceArtworkDisabled='true';return}
  image.src=asset(spec.library,spec.index);image.style.display='';delete image.dataset.sourceArtworkDisabled;
}
function applyScrollbar(element,control){
  if(!(element instanceof Element))return;
  const p=control.properties||{},vertical=control.type==='DXVScrollBar';
  const previous=childSpec(vertical?p.UpButton:p.LeftButton,44);
  const next=childSpec(vertical?p.DownButton:p.RightButton,46);
  const thumb=childSpec(p.PositionBar,45);
  const previousImage=element.querySelector(':scope > .dx-scroll-prev');
  const nextImage=element.querySelector(':scope > .dx-scroll-next');
  const thumbImage=element.querySelector(':scope > .dx-scroll-thumb');
  applyChildImage(previousImage,previous);
  applyChildImage(nextImage,next);
  applyChildImage(thumbImage,thumb);

  const border=boolFrom(p.Border,true);
  element.style.border=border?`1px solid ${colour(p.BorderColour,PRIMARY)}`:'none';
  element.style.background=colour(p.BackColour,'#000');
  element.dataset.sourcePreviousSkin=`${previous.library}#${previous.index}`;
  element.dataset.sourceNextSkin=`${next.library}#${next.index}`;
  element.dataset.sourceThumbSkin=`${thumb.library}#${thumb.index}`;
  element.dataset.sourceScrollRoot=`border=${border}; back=${String(p.BackColour??'constructor:black')}`;
}
function apply(root){
  const item=itemFor(root);if(!item)return;const controls=item.controls||[];
  for(const element of root.querySelectorAll('[data-control-index][data-control-type="DXVScrollBar"],[data-control-index][data-control-type="DXHScrollBar"]')){
    const index=Number.parseInt(element.dataset.controlIndex||'',10);if(!Number.isInteger(index))continue;const control=controls[index];if(control)applyScrollbar(element,control);
  }
}
function scan(node){if(!(node instanceof Element))return;if(node.matches?.('.window,.generic-window'))queueMicrotask(()=>apply(node));node.querySelectorAll?.('.window,.generic-window').forEach(root=>queueMicrotask(()=>apply(root)))}
new MutationObserver(records=>records.forEach(record=>record.addedNodes.forEach(scan))).observe(stage,{childList:true,subtree:true});
fetch('ui-source-spec.json',{cache:'no-store'}).then(r=>{if(!r.ok)throw new Error(`ui-source-spec.json ${r.status}`);return r.json()}).then(value=>{spec=value;stage.querySelectorAll('.window,.generic-window').forEach(apply);console.info('ORIGINS per-instance Zircon scrollbar skins active')}).catch(error=>console.error('Unable to load scrollbar fidelity manifest',error));