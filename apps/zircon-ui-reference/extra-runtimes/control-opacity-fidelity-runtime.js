// DXControl.Opacity applies to every control; DXImageControl additionally has
// ImageOpacity. Project the deterministic literal composition into the DOM.
const stage=document.querySelector('#stage');
let spec=null;
function numberFrom(raw,fallback=1){const value=String(raw??'').trim().replace(/[fFdDmM]$/,'');return /^-?(?:\d+(?:\.\d*)?|\.\d+)$/.test(value)?Number(value):fallback}
function clamp(value){return Math.max(0,Math.min(1,value))}
function itemFor(root){if(!spec||!root?.id?.startsWith('w-'))return null;const id=root.id.slice(2);return [...(spec.windows||[]),...(spec.nestedWindows||[])].find(item=>item.id===id)||null}
function apply(root){
  const item=itemFor(root);if(!item)return;const controls=item.controls||[];
  for(const element of root.querySelectorAll('[data-control-index]')){
    const index=Number.parseInt(element.dataset.controlIndex||'',10);if(!Number.isInteger(index))continue;const control=controls[index];if(!control)continue;
    const p=control.properties||{},controlOpacity=clamp(numberFrom(p.Opacity,1));
    const imageOpacity=(control.type==='DXImageControl'||control.type==='DXAnimatedControl')?clamp(numberFrom(p.ImageOpacity,1)):1;
    const effective=clamp(controlOpacity*imageOpacity);
    element.style.opacity=String(effective);
    element.dataset.sourceControlOpacity=String(controlOpacity);element.dataset.sourceImageOpacity=String(imageOpacity);element.dataset.sourceEffectiveOpacity=String(effective);
  }
}
function scan(node){if(!(node instanceof Element))return;if(node.matches?.('.window,.generic-window'))queueMicrotask(()=>apply(node));node.querySelectorAll?.('.window,.generic-window').forEach(root=>queueMicrotask(()=>apply(root)))}
new MutationObserver(records=>records.forEach(record=>record.addedNodes.forEach(scan))).observe(stage,{childList:true,subtree:true});
fetch('ui-source-spec.json',{cache:'no-store'}).then(r=>{if(!r.ok)throw new Error(`ui-source-spec.json ${r.status}`);return r.json()}).then(value=>{spec=value;stage.querySelectorAll('.window,.generic-window').forEach(apply);console.info('ORIGINS DXControl/DXImageControl opacity composition active')}).catch(error=>console.error('Unable to load opacity fidelity manifest',error));