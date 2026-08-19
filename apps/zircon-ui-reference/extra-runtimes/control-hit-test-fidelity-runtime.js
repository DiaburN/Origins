// DXControl hit-test semantics: non-controls and PassThrough overlays render but
// do not consume mouse input. This lets the correct parent receive drag/click.
const stage=document.querySelector('#stage');
let spec=null;
function boolFrom(raw,fallback){const v=String(raw??'').trim().toLowerCase();return v==='true'?true:v==='false'?false:fallback}
function itemFor(root){if(!spec||!root?.id?.startsWith('w-'))return null;const id=root.id.slice(2);return [...(spec.windows||[]),...(spec.nestedWindows||[])].find(item=>item.id===id)||null}
function apply(root){
  const item=itemFor(root);if(!item)return;const controls=item.controls||[];
  for(const element of root.querySelectorAll('[data-control-index]')){
    const index=Number.parseInt(element.dataset.controlIndex||'',10);if(!Number.isInteger(index))continue;const control=controls[index];if(!control)continue;
    const p=control.properties||{},isControl=boolFrom(p.IsControl,true),passThrough=boolFrom(p.PassThrough,false);
    element.dataset.sourceIsControl=String(isControl);element.dataset.sourcePassThrough=String(passThrough);
    if(!isControl||passThrough)element.style.pointerEvents='none';
  }
}
function scan(node){if(!(node instanceof Element))return;if(node.matches?.('.window,.generic-window'))queueMicrotask(()=>apply(node));node.querySelectorAll?.('.window,.generic-window').forEach(root=>queueMicrotask(()=>apply(root)))}
new MutationObserver(records=>records.forEach(record=>record.addedNodes.forEach(scan))).observe(stage,{childList:true,subtree:true});
fetch('ui-source-spec.json',{cache:'no-store'}).then(r=>{if(!r.ok)throw new Error(`ui-source-spec.json ${r.status}`);return r.json()}).then(value=>{spec=value;stage.querySelectorAll('.window,.generic-window').forEach(apply);console.info('ORIGINS DXControl IsControl/PassThrough hit-test fidelity active')}).catch(error=>console.error('Unable to load hit-test manifest',error));