// Source-faithful DXComboBox showing/selection mechanics. Options are rendered
// only when the manifest contains source-extracted comboOptions; runtime-built
// options remain intentionally empty rather than fabricated.
const stage=document.querySelector('#stage');
let spec=null;
const PRIMARY='rgb(198,166,99)';
function intFrom(raw,fallback){const value=String(raw??'').trim();return /^-?\d+$/.test(value)?Number(value):fallback}
function itemFor(root){if(!spec||!root?.id?.startsWith('w-'))return null;const id=root.id.slice(2);return [...(spec.windows||[]),...(spec.nestedWindows||[])].find(item=>item.id===id)||null}
function sourceControl(element){
  const root=element.closest('.window,.generic-window');if(!root)return null;const item=itemFor(root);if(!item)return null;
  const index=Number.parseInt(element.dataset.controlIndex||'',10);if(!Number.isInteger(index))return null;
  const control=item.controls?.[index];return control?.type==='DXComboBox'?{root,item,control}:null;
}
function closeDropdown(element){
  const id=element.dataset.sourceComboDropdownId;if(id)document.getElementById(id)?.remove();
  element.dataset.sourceComboShowing='false';element.style.height=`${intFrom(element.dataset.sourceNormalHeight,16)}px`;
}
function dropdownPosition(element,dropdown,normalHeight){
  const stageRect=stage.getBoundingClientRect(),box=element.getBoundingClientRect();
  dropdown.style.left=`${Math.round(box.left-stageRect.left)}px`;
  dropdown.style.top=`${Math.round(box.top-stageRect.top+normalHeight+2)}px`;
  dropdown.style.width=`${Math.round(box.width)}px`;
}
function applyInitialSelection(element,control){
  const options=Array.isArray(control.comboOptions)?control.comboOptions:[];
  const index=Number(control.comboSelectedOptionIndex);
  if(!Number.isInteger(index)||index<0||index>=options.length)return;
  const option=options[index],selected=element.querySelector(':scope > span');
  if(selected)selected.textContent=String(option.label??'');
  element.dataset.sourceSelectedIndex=String(index);
  element.dataset.sourceSelectedValue=String(option.valueExpression??option.value??'');
  element.dataset.sourceInitialSelection='constructor SelectItem(...)';
}
function showDropdown(element,resolved){
  closeDropdown(element);
  const p=resolved.control.properties||{};
  const normalHeight=intFrom(p.NormalHeight,16),dropDownHeight=Math.max(normalHeight,intFrom(p.DropDownHeight,123));
  const options=Array.isArray(resolved.control.comboOptions)?resolved.control.comboOptions:[];
  const rowHeight=20;
  const contentHeight=options.length*rowHeight;
  const totalHeight=Math.min(contentHeight+normalHeight+2,dropDownHeight);
  element.style.height=`${Math.max(normalHeight,totalHeight)}px`;
  element.dataset.sourceComboShowing='true';
  element.dataset.sourceNormalHeight=String(normalHeight);element.dataset.sourceDropDownHeight=String(dropDownHeight);
  element.dataset.sourceComboOptionCount=String(options.length);
  element.dataset.sourceComboOptionsInvented='false';

  const dropdown=document.createElement('div');
  dropdown.className='source-combo-dropdown';
  dropdown.id=`source-combo-${crypto.randomUUID?.()||Math.random().toString(36).slice(2)}`;
  dropdown.style.position='absolute';dropdown.style.height=`${Math.max(2,totalHeight-normalHeight-2)}px`;
  dropdown.style.background='#000';dropdown.style.border=`1px solid ${PRIMARY}`;dropdown.style.overflow='hidden';dropdown.style.zIndex='10000';
  dropdown.dataset.sourceParentControl=resolved.control.name||'';
  dropdown.dataset.sourceParentWindow=resolved.item.id||resolved.item.field||'';
  element.dataset.sourceComboDropdownId=dropdown.id;
  stage.append(dropdown);dropdownPosition(element,dropdown,normalHeight);

  const selected=element.querySelector(':scope > span');
  options.forEach((option,index)=>{
    const row=document.createElement('div');row.className='source-combo-option';row.textContent=String(option.label??'');
    row.style.height=`${rowHeight}px`;row.style.lineHeight=`${rowHeight}px`;row.style.padding='0 4px';row.style.fontSize='9px';row.style.color='#fff';row.style.whiteSpace='nowrap';row.style.overflow='hidden';row.style.textOverflow='ellipsis';row.style.cursor='pointer';
    row.dataset.optionIndex=String(index);row.dataset.sourceValue=String(option.valueExpression??option.value??'');
    row.addEventListener('pointerenter',()=>{row.style.background='rgb(25,20,0)'});row.addEventListener('pointerleave',()=>{row.style.background='transparent'});
    row.addEventListener('click',event=>{
      event.preventDefault();event.stopPropagation();if(selected)selected.textContent=String(option.label??'');
      element.dataset.sourceSelectedIndex=String(index);element.dataset.sourceSelectedValue=String(option.valueExpression??option.value??'');
      closeDropdown(element);
      element.dispatchEvent(new CustomEvent('origins:source-combo-selected',{bubbles:true,detail:{index,option}}));
    });
    dropdown.append(row);
  });
}
function install(element){
  if(!(element instanceof Element)||element.dataset.sourceComboRuntime==='true')return;
  const resolved=sourceControl(element);if(!resolved)return;
  element.dataset.sourceComboRuntime='true';
  const p=resolved.control.properties||{},normalHeight=intFrom(p.NormalHeight,16),dropDownHeight=Math.max(normalHeight,intFrom(p.DropDownHeight,123));
  element.dataset.sourceNormalHeight=String(normalHeight);element.dataset.sourceDropDownHeight=String(dropDownHeight);element.dataset.sourceComboShowing='false';
  element.style.height=`${normalHeight}px`;
  applyInitialSelection(element,resolved.control);
  const arrow=[...element.querySelectorAll('img')].find(image=>/GameInter\/00795\.png$/.test(image.src))||element.querySelector('img:last-of-type');
  if(arrow){
    arrow.dataset.sourceComboDownArrow='GameInter#795';arrow.style.pointerEvents='auto';
    arrow.addEventListener('click',event=>{
      event.preventDefault();event.stopImmediatePropagation();
      if(element.dataset.sourceComboShowing==='true')closeDropdown(element);else showDropdown(element,resolved);
    },true);
  }
  element.addEventListener('keydown',event=>{if(event.key==='Escape'&&element.dataset.sourceComboShowing==='true'){event.preventDefault();closeDropdown(element)}});
}
function scan(root){
  if(!(root instanceof Element))return;
  const candidates=[];if(root.matches?.('.dx-combobox[data-control-index]'))candidates.push(root);root.querySelectorAll?.('.dx-combobox[data-control-index]').forEach(element=>candidates.push(element));
  candidates.forEach(element=>queueMicrotask(()=>install(element)));
}
new MutationObserver(records=>records.forEach(record=>record.addedNodes.forEach(scan))).observe(stage,{childList:true,subtree:true});
window.addEventListener('resize',()=>stage.querySelectorAll('.dx-combobox[data-source-combo-showing="true"]').forEach(element=>{const id=element.dataset.sourceComboDropdownId,dropdown=id&&document.getElementById(id);if(dropdown)dropdownPosition(element,dropdown,intFrom(element.dataset.sourceNormalHeight,16))}));
stage.addEventListener('pointerdown',event=>{for(const element of stage.querySelectorAll('.dx-combobox[data-source-combo-showing="true"]')){const id=element.dataset.sourceComboDropdownId,dropdown=id&&document.getElementById(id);if(element.contains(event.target)||dropdown?.contains(event.target))continue;closeDropdown(element)}},true);
fetch('ui-source-spec.json',{cache:'no-store'}).then(r=>{if(!r.ok)throw new Error(`ui-source-spec.json ${r.status}`);return r.json()}).then(value=>{spec=value;stage.querySelectorAll('.dx-combobox[data-control-index]').forEach(install);console.info('ORIGINS DXComboBox source showing runtime active; static options/initial selections source-backed, runtime options neutral')}).catch(error=>console.error('Unable to load DXComboBox manifest',error));
