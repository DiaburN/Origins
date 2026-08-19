// Apply source-neutral projections for runtime-dependent overflow contracts.
// This does not invent the missing runtime data; it only reproduces deterministic
// source state such as BeforeDraw hiding and literal partial dimensions.
const stage=document.querySelector('#stage');
let spec=null;
function itemFor(root){if(!spec||!root?.id?.startsWith('w-'))return null;const id=root.id.slice(2);return [...(spec.windows||[]),...(spec.nestedWindows||[])].find(item=>item.id===id)||null}
function apply(root){
  const item=itemFor(root);if(!item)return;const controls=item.controls||[];
  for(const element of root.querySelectorAll('[data-control-index]')){
    const index=Number.parseInt(element.dataset.controlIndex||'',10);if(!Number.isInteger(index))continue;
    const control=controls[index];if(!control)continue;
    if(control.sourceNeutralVisible===false){element.hidden=true;element.dataset.sourceNeutralVisible='false'}
    if(Number.isFinite(Number(control.sourceResolvedWidth))){element.style.width=`${Number(control.sourceResolvedWidth)}px`;element.dataset.sourceResolvedWidth=String(control.sourceResolvedWidth)}
    if(Number.isFinite(Number(control.sourceResolvedHeight))){element.style.height=`${Number(control.sourceResolvedHeight)}px`;element.dataset.sourceResolvedHeight=String(control.sourceResolvedHeight)}
    if(control.overflowContract?.kind)element.dataset.sourceOverflowContract=control.overflowContract.kind;
  }
  if(item.sourceClass==='GroupLFGInputWindow')root.dataset.sourceDynamicHeightContract=String(item.dynamicHeightContract||'');
}
function scan(node){if(!(node instanceof Element))return;if(node.matches?.('.window,.generic-window'))queueMicrotask(()=>apply(node));node.querySelectorAll?.('.window,.generic-window').forEach(root=>queueMicrotask(()=>apply(root)))}
new MutationObserver(records=>records.forEach(record=>record.addedNodes.forEach(scan))).observe(stage,{childList:true,subtree:true});
fetch('ui-source-spec.json',{cache:'no-store'}).then(r=>{if(!r.ok)throw new Error(`ui-source-spec.json ${r.status}`);return r.json()}).then(value=>{spec=value;stage.querySelectorAll('.window,.generic-window').forEach(apply);console.info('ORIGINS source overflow/neutral projection contracts active')}).catch(error=>console.error('Unable to load overflow contract manifest',error));