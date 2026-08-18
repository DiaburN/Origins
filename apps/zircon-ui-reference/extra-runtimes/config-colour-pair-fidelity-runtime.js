// Source-faithful DXColourControlPair state for DXConfigWindow. The 13 pairs are
// expanded into 26 DXColourControl children by augment_colour_control_pairs.py.
// Checked-in Config.cs Color expressions drive the neutral swatches. Picker RGB
// changes are local only; renderer/chat side effects are not fabricated.
const stage=document.querySelector('#stage');
let spec=null,currentTarget=null;
function control(root,name){return root?.querySelector?.(`[data-control-name="${CSS.escape(name)}"]`)||null}
function sourceItem(){return spec?.windows?.find(item=>item.field==='ConfigBox')||null}
function cssFromDotNet(expression){
  const raw=String(expression??'').trim();if(!raw||raw==='Color.Empty')return 'transparent';
  let match=raw.match(/^Color\.FromArgb\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)$/);if(match)return `rgba(${match[2]}, ${match[3]}, ${match[4]}, ${Number(match[1])/255})`;
  match=raw.match(/^Color\.FromArgb\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)$/);if(match)return `rgb(${match[1]}, ${match[2]}, ${match[3]})`;
  match=raw.match(/^Color\.([A-Za-z]+)$/);if(match)return match[1].replace(/([a-z])([A-Z])/g,'$1-$2').toLowerCase();
  return 'transparent';
}
function rgbFromElement(element){
  const value=getComputedStyle(element).backgroundColor;const m=value.match(/rgba?\(\s*(\d+)\D+(\d+)\D+(\d+)/);return m?[Number(m[1]),Number(m[2]),Number(m[3])]:[0,0,0]
}
function applySwatch(element,expression,source='Config.cs'){if(!element)return;element.style.backgroundColor=cssFromDotNet(expression);element.dataset.sourceColourExpression=String(expression??'Color.Empty');element.dataset.sourceColourOrigin=source;element.dataset.sourceColourInvented='false'}
function setNumber(root,name,value){const box=control(root,name);if(!box)return;box.dataset.value=String(value);const field=box.querySelector('.dx-number-value');if(field)field.textContent=String(value);box.dispatchEvent(new CustomEvent('origins:source-number-value',{bubbles:true,detail:{value}}))}
function pickerItem(){return spec?.nestedWindows?.find(item=>item.sourceClass==='DXColourPicker')||null}
function openPicker(target){
  const item=pickerItem();if(!item)return null;let picker=document.querySelector(`#w-${CSS.escape(item.id)}`);if(!picker){document.querySelector(`[data-window-id="${CSS.escape(item.id)}"]`)?.click();picker=document.querySelector(`#w-${CSS.escape(item.id)}`)}
  if(!picker)return null;currentTarget=target;picker.dataset.sourceConfigColourTarget=target.dataset.controlName||'';picker.dataset.sourceAllowNoColour='runtime DXColourControl.Target contract; not assumed';const [r,g,b]=rgbFromElement(target);queueMicrotask(()=>{setNumber(picker,'RedBox',r);setNumber(picker,'GreenBox',g);setNumber(picker,'BlueBox',b);picker.dataset.selectedColour=`${r},${g},${b}`});return picker;
}
function bindPicker(picker){if(!picker||picker.dataset.sourceConfigColourBound==='true')return;picker.dataset.sourceConfigColourBound='true';const select=control(picker,'SelectButton'),empty=control(picker,'EmptyButton');
  select?.addEventListener('click',()=>{if(!currentTarget)return;const selected=String(picker.dataset.selectedColour||'').match(/^(\d+),(\d+),(\d+)$/);if(selected){const expression=`Color.FromArgb(${selected[1]}, ${selected[2]}, ${selected[3]})`;applySwatch(currentTarget,expression,'DXColourPicker local selection');const root=currentTarget.closest('#w-config');const property=currentTarget.dataset.sourceConfigProperty;if(root&&property)root.dataset[`config${property}`]=expression;root&&(root.dataset.sourceColourEngineEffectExecuted='false')}currentTarget=null},true);
  empty?.addEventListener('click',()=>{if(!currentTarget)return;applySwatch(currentTarget,'Color.Empty','DXColourPicker local empty');const root=currentTarget.closest('#w-config');const property=currentTarget.dataset.sourceConfigProperty;if(root&&property)root.dataset[`config${property}`]='Color.Empty';currentTarget=null},true);
}
function install(root){
  if(!root||root.id!=='w-config'||root.dataset.sourceColourPairsRuntime==='true'||!spec)return;root.dataset.sourceColourPairsRuntime='true';const item=sourceItem();if(!item)return;
  const swatches=(item.controls||[]).filter(c=>c.type==='DXColourControl'&&String(c.name||'').includes('__'));
  for(const source of swatches){const el=control(root,source.name);if(!el)continue;const binding=(source.sourceConfigBindings||[])[0];if(binding){el.dataset.sourceConfigProperty=binding.configProperty;el.dataset.sourceConfigKind=binding.kind;applySwatch(el,binding.default,'checked-in Config.cs default')}if(el.dataset.sourceColourPickerBound!=='true'){el.dataset.sourceColourPickerBound='true';el.addEventListener('click',event=>{event.preventDefault();event.stopImmediatePropagation();const picker=openPicker(el);if(picker)queueMicrotask(()=>bindPicker(picker))},true)}}
  const reset=control(root,'ResetColoursButton');if(reset&&reset.dataset.sourceColourResetBound!=='true'){reset.dataset.sourceColourResetBound='true';reset.addEventListener('click',event=>{event.preventDefault();event.stopImmediatePropagation();for(const source of swatches){const el=control(root,source.name),binding=(source.sourceConfigBindings||[])[0];if(!el||!binding)continue;applySwatch(el,binding.default,'ResetColoursButton source default');root.dataset[`config${binding.configProperty}`]=String(binding.default??'Color.Empty')}root.dataset.sourceColourReset='13 DXColourControlPair defaults restored';root.dataset.sourceColourEngineEffectExecuted='false'},true)}
  root.dataset.sourceColourPairCount='13';root.dataset.sourceColourSwatchCount=String(swatches.length);root.dataset.sourceColourPaletteInvented='false';
}
function scan(node){if(!(node instanceof Element))return;if(node.id==='w-config')queueMicrotask(()=>install(node));if(node.dataset?.nestedSourceClass==='DXColourPicker')queueMicrotask(()=>bindPicker(node));node.querySelectorAll?.('#w-config').forEach(root=>queueMicrotask(()=>install(root)));node.querySelectorAll?.('[data-nested-source-class="DXColourPicker"]').forEach(p=>queueMicrotask(()=>bindPicker(p)))}
new MutationObserver(records=>records.forEach(record=>record.addedNodes.forEach(scan))).observe(stage,{childList:true,subtree:true});
fetch('ui-source-spec.json',{cache:'no-store'}).then(r=>{if(!r.ok)throw new Error(`ui-source-spec.json ${r.status}`);return r.json()}).then(value=>{spec=value;install(document.querySelector('#w-config'));stage.querySelectorAll('[data-nested-source-class="DXColourPicker"]').forEach(bindPicker);console.info('ORIGINS Config colour-pair source runtime active: 13 pairs / 26 swatches / source defaults + picker + reset')}).catch(error=>console.error('Unable to load Config colour-pair manifest',error));
