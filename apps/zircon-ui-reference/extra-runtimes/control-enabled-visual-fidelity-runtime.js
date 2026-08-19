// Keep visual disabled state aligned with the source-enabled input guard.
// DXImageControl/DXButton source rendering applies grayscale + ~75/255 brightness
// when disabled. This pass follows the effective data-source-enabled value,
// including runtime Enabled overrides, without changing hit-test behavior.
const stage=document.querySelector('#stage');
const DISABLED_BRIGHTNESS=75/255;
function applyElement(element){
  if(!(element instanceof Element)||!element.hasAttribute('data-source-enabled'))return;
  const enabled=element.dataset.sourceEnabled!=='false';
  const images=[];
  if(element instanceof HTMLImageElement)images.push(element);
  element.querySelectorAll?.(':scope > img').forEach(image=>images.push(image));
  for(const image of images){
    if(image.dataset.sourceEnabledVisualBaseFilter===undefined)image.dataset.sourceEnabledVisualBaseFilter=image.style.filter||'';
    const base=image.dataset.sourceEnabledVisualBaseFilter||'';
    const disabledFilter=`grayscale(1) brightness(${DISABLED_BRIGHTNESS})`;
    image.style.filter=enabled?base:[base,disabledFilter].filter(Boolean).join(' ');
    image.dataset.sourceEffectiveEnabled=String(enabled);
  }
  element.dataset.sourceDisabledVisual=String(!enabled);
}
function applyRoot(root){
  if(!(root instanceof Element))return;
  if(root.hasAttribute('data-source-enabled'))applyElement(root);
  root.querySelectorAll?.('[data-source-enabled]').forEach(applyElement);
}
stage.addEventListener('origins:source-enabled-changed',event=>{
  const root=event.target instanceof Element?event.target.closest('.window,.generic-window'):null;
  if(root)queueMicrotask(()=>applyRoot(root));
});
new MutationObserver(records=>{
  for(const record of records){
    if(record.type==='attributes'&&record.target instanceof Element){applyElement(record.target);continue}
    record.addedNodes.forEach(node=>{if(node instanceof Element)queueMicrotask(()=>applyRoot(node))});
  }
}).observe(stage,{childList:true,subtree:true,attributes:true,attributeFilter:['data-source-enabled']});
stage.querySelectorAll('.window,.generic-window').forEach(applyRoot);
console.info('ORIGINS effective Enabled visual fidelity active: source-disabled imagery follows computed/dynamic IsEnabled');
