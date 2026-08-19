// Exact neutral DXItemGrid/DXItemCell colour/state corrections.
// Item contents remain runtime data and are intentionally never fabricated.
const stage=document.querySelector('#stage');
let spec=null;
const INACTIVE='rgb(99,83,50)';
const LIME='#00ff00';
function boolFrom(raw,fallback=false){const v=String(raw??'').trim().toLowerCase();return v==='true'?true:v==='false'?false:fallback}
function colour(raw,fallback){
  const v=String(raw??'');
  if(/Constants\.InactiveBorderColour/.test(v))return INACTIVE;
  if(/Color\.Lime\b/.test(v))return LIME;
  if(/Color\.Empty\b/.test(v))return 'transparent';
  let m=v.match(/Color\.FromArgb\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)/);if(m)return `rgba(${m[2]},${m[3]},${m[4]},${Number(m[1])/255})`;
  m=v.match(/Color\.FromArgb\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)/);return m?`rgb(${m[1]},${m[2]},${m[3]})`:fallback;
}
function itemFor(root){if(!spec||!root?.id?.startsWith('w-'))return null;const id=root.id.slice(2);return [...(spec.windows||[]),...(spec.nestedWindows||[])].find(item=>item.id===id)||null}
function styleGrid(element,control){
  element.style.border='none';element.style.background='rgb(24,12,12)';
  element.querySelectorAll(':scope > .dx-item-grid-line').forEach(line=>line.style.background=INACTIVE);
  element.dataset.sourceGridBackColour='rgb(24,12,12)';
  element.dataset.sourceGridBorderColour=INACTIVE;
  element.dataset.sourceGridLines='DXItemGrid.OnClearTexture exact inactive border lines';
  const p=control.properties||{};element.dataset.sourceGridReadOnly=String(boolFrom(p.ReadOnly,false));element.dataset.sourceGridAllowLink=String(boolFrom(p.AllowLink,true));
}
function styleCell(element,control){
  const p=control.properties||{};
  const hidden=boolFrom(p.Hidden,false),enabled=boolFrom(p.Enabled,true),locked=boolFrom(p.Locked,false),selected=boolFrom(p.Selected,false),fixed=boolFrom(p.FixedBorder,false),fixedColour=boolFrom(p.FixedBorderColour,false);
  const explicitColour=colour(p.BorderColour,INACTIVE);
  const restore=()=>{
    if(hidden){element.style.border='none';element.style.background='transparent';return}
    if(!enabled)element.style.background='rgba(0,125,125,0.4901960784)';
    else if(locked||selected)element.style.background='rgba(255,125,125,0.4901960784)';
    else element.style.background=colour(p.BackColour,'transparent');
    const border=locked||selected||fixed;
    const borderColour=fixedColour?explicitColour:(locked||selected?LIME:INACTIVE);
    element.style.border=border?`1px solid ${borderColour}`:'none';
  };
  restore();
  element.dataset.sourceCellHidden=String(hidden);element.dataset.sourceCellEnabled=String(enabled);element.dataset.sourceCellLocked=String(locked);element.dataset.sourceCellSelected=String(selected);element.dataset.sourceCellFixedBorder=String(fixed);element.dataset.sourceCellFixedBorderColour=String(fixedColour);
  if(element.dataset.exactItemCellHover!=='true'){
    element.dataset.exactItemCellHover='true';
    element.addEventListener('pointerenter',()=>{if(hidden)return;const c=fixedColour?explicitColour:LIME;element.style.border=`1px solid ${c}`});
    element.addEventListener('pointerleave',restore);
  }
}
function apply(root){
  const item=itemFor(root);if(!item)return;const controls=item.controls||[];
  for(const element of root.querySelectorAll('[data-control-index]')){
    const i=Number.parseInt(element.dataset.controlIndex||'',10);if(!Number.isInteger(i))continue;const control=controls[i];if(!control)continue;
    if(control.type==='DXItemGrid')styleGrid(element,control);else if(control.type==='DXItemCell')styleCell(element,control);
  }
}
function scan(node){if(!(node instanceof Element))return;if(node.matches?.('.window,.generic-window'))queueMicrotask(()=>apply(node));node.querySelectorAll?.('.window,.generic-window').forEach(root=>queueMicrotask(()=>apply(root)))}
new MutationObserver(records=>records.forEach(record=>record.addedNodes.forEach(scan))).observe(stage,{childList:true,subtree:true});
fetch('ui-source-spec.json',{cache:'no-store'}).then(r=>{if(!r.ok)throw new Error(`ui-source-spec.json ${r.status}`);return r.json()}).then(value=>{spec=value;stage.querySelectorAll('.window,.generic-window').forEach(apply);console.info('ORIGINS exact DXItemGrid/DXItemCell neutral colour-state pass active')}).catch(error=>console.error('Unable to load item fidelity manifest',error));