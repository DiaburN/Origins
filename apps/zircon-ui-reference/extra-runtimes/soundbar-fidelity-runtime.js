// Source-faithful DXSoundBar runtime. Uses GameInter 4740-4746 and the embedded
// DXHScrollBar contract (Size=195x18, Value 0..100, Change=1, ScrollWidth=145).
const stage=document.querySelector('#stage');
let spec=null;
const pad=value=>String(value).padStart(5,'0');
const asset=(library,index)=>`assets/${library}/${pad(index)}.png`;
const MIN=0,MAX=100,CHANGE=1,SCROLLBAR_X=5,SCROLL_WIDTH=145,POSITION_BASE_X=16;
function itemFor(root){if(!spec||!root?.id?.startsWith('w-'))return null;const id=root.id.slice(2);return [...(spec.windows||[]),...(spec.nestedWindows||[])].find(item=>item.id===id)||null}
function sourceControl(element){const root=element.closest('.window,.generic-window');const item=itemFor(root);if(!root||!item)return null;const index=Number(element.dataset.controlIndex);if(!Number.isInteger(index))return null;const control=item.controls?.[index];return control?.type==='DXSoundBar'?{root,item,control}:null}
function clamp(value){return Math.max(MIN,Math.min(MAX,Math.round(Number(value)||0)))}
function parts(element){
  const images=[...element.querySelectorAll(':scope > img')];
  return {
    icon:images.find(img=>/GameInter\/(04740|04741)\.png$/.test(img.src))||images[0],
    outer:images.find(img=>/GameInter\/04743\.png$/.test(img.src)),
    inner:images.find(img=>/GameInter\/04742\.png$/.test(img.src)),
    slider:images.find(img=>/GameInter\/(04745|04746)\.png$/.test(img.src))||images.at(-1),
  };
}
function state(element){return {value:clamp(element.dataset.sourceSoundValue??element.dataset.sourceConfigValue??element.dataset.value??0),muted:(element.dataset.sourceSoundMuted??element.dataset.sourceConfigMuted)==='true'}}
function render(element,{value,muted},emit=false){
  value=clamp(value);muted=Boolean(muted);const p=parts(element);
  element.dataset.sourceSoundValue=String(value);element.dataset.value=String(value);element.dataset.sourceSoundMuted=String(muted);element.dataset.sourceSoundRange='0..100';element.dataset.sourceSoundChange=String(CHANGE);element.dataset.sourceSoundScrollWidth=String(SCROLL_WIDTH);
  if(p.icon){p.icon.src=asset('GameInter',muted?4740:4741);p.icon.dataset.sourceSoundIcon=muted?'4740 muted':'4741 unmuted';p.icon.style.pointerEvents='auto'}
  if(p.outer){p.outer.style.left='20px';p.outer.style.top='3px';p.outer.dataset.sourceSoundOuter='GameInter#4743'}
  if(p.inner){p.inner.style.left='22px';p.inner.style.top='5px';p.inner.style.clipPath=`inset(0 ${100-value}% 0 0)`;p.inner.dataset.sourceSoundInner='GameInter#4742';p.inner.dataset.sourceFillPercent=String(value)}
  if(p.slider){p.slider.src=asset('GameInter',4746);p.slider.style.left=`${SCROLLBAR_X+POSITION_BASE_X+Math.round(SCROLL_WIDTH*(value/100))}px`;p.slider.style.top='1px';p.slider.style.pointerEvents='auto';p.slider.style.cursor='ew-resize';p.slider.dataset.sourceSoundSlider='GameInter#4746 hover/normal; pressed #4745'}
  if(emit)element.dispatchEvent(new CustomEvent('origins:source-sound-changed',{bubbles:true,detail:{value,muted}}));
}
function valueFromClientX(element,clientX){const rect=element.getBoundingClientRect();const local=clientX-rect.left-SCROLLBAR_X;const sliderWidth=parts(element).slider?.getBoundingClientRect().width||16;return clamp((local-(sliderWidth+sliderWidth/2))*100/SCROLL_WIDTH)}
function install(element){
  if(!(element instanceof Element)||element.dataset.sourceSoundRuntime==='true')return;const resolved=sourceControl(element);if(!resolved)return;element.dataset.sourceSoundRuntime='true';
  const initialValue=clamp(element.dataset.sourceConfigValue??element.dataset.value??0),initialMuted=(element.dataset.sourceConfigMuted??'false')==='true';render(element,{value:initialValue,muted:initialMuted});
  const p=parts(element);
  p.icon?.addEventListener('click',event=>{event.preventDefault();event.stopImmediatePropagation();const s=state(element);render(element,{value:s.value,muted:!s.muted},true)},true);
  let dragging=false;
  p.slider?.addEventListener('pointerdown',event=>{event.preventDefault();event.stopImmediatePropagation();dragging=true;p.slider.src=asset('GameInter',4745);p.slider.setPointerCapture?.(event.pointerId)});
  p.slider?.addEventListener('pointermove',event=>{if(!dragging)return;event.preventDefault();const s=state(element);render(element,{value:valueFromClientX(element,event.clientX),muted:s.muted},true)});
  p.slider?.addEventListener('pointerup',event=>{dragging=false;p.slider.src=asset('GameInter',4746);p.slider.releasePointerCapture?.(event.pointerId)});
  element.addEventListener('pointerdown',event=>{if(event.target===p.icon||event.target===p.slider)return;event.preventDefault();const s=state(element);render(element,{value:valueFromClientX(element,event.clientX),muted:s.muted},true)});
  element.addEventListener('wheel',event=>{event.preventDefault();event.stopPropagation();const s=state(element);render(element,{value:s.value+(event.deltaY>0?-CHANGE:CHANGE),muted:s.muted},true)},{passive:false});
  element.addEventListener('origins:source-config-sound-default',event=>{event.stopPropagation();render(element,{value:event.detail?.value??0,muted:event.detail?.muted??false})});
}
function scan(node){if(!(node instanceof Element))return;if(node.matches?.('.dx-soundbar[data-control-index]'))queueMicrotask(()=>install(node));node.querySelectorAll?.('.dx-soundbar[data-control-index]').forEach(el=>queueMicrotask(()=>install(el)))}
new MutationObserver(records=>records.forEach(record=>record.addedNodes.forEach(scan))).observe(stage,{childList:true,subtree:true});
fetch('ui-source-spec.json',{cache:'no-store'}).then(r=>{if(!r.ok)throw new Error(`ui-source-spec.json ${r.status}`);return r.json()}).then(value=>{spec=value;stage.querySelectorAll('.dx-soundbar[data-control-index]').forEach(install);console.info('ORIGINS DXSoundBar source runtime active: 4740-4746, 0..100, click/wheel/drag/mute')}).catch(error=>console.error('Unable to load DXSoundBar manifest',error));
