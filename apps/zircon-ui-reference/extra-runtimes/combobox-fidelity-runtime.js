// Source-faithful DXComboBox showing/selection mechanics. Options are rendered
// only when the manifest contains source-extracted comboOptions; runtime-built
// options remain intentionally empty rather than fabricated.
//
// The opened list reproduces DXListBox + DXVScrollBar rather than using native
// browser scrolling: 14px scrollbar, Interface 44/46/45, Change=15, source
// clipping, source hover/selected colours and ActiveScene-level positioning.
const stage=document.querySelector('#stage');
let spec=null;
const PRIMARY='rgb(198,166,99)';
const ROW_HEIGHT=16;
const SCROLL_WIDTH=14;
const SCROLL_CHANGE=15;
const pad=value=>String(value).padStart(5,'0');
const asset=(library,index)=>`assets/${library}/${pad(index)}.png`;
function intFrom(raw,fallback){const value=String(raw??'').trim();return /^-?\d+$/.test(value)?Number(value):fallback}
function itemFor(root){if(!spec||!root?.id?.startsWith('w-'))return null;const id=root.id.slice(2);return [...(spec.windows||[]),...(spec.nestedWindows||[])].find(item=>item.id===id)||null}
function sourceControl(element){
  const root=element.closest('.window,.generic-window');if(!root)return null;const item=itemFor(root);if(!item)return null;
  const index=Number.parseInt(element.dataset.controlIndex||'',10);if(!Number.isInteger(index))return null;
  const control=item.controls?.[index];return control?.type==='DXComboBox'?{root,item,control}:null;
}
function selectedLabel(element){
  let selected=element.querySelector(':scope > span.source-combo-selected-label,:scope > span');
  if(selected)return selected;
  selected=document.createElement('span');selected.className='source-combo-selected-label';
  selected.style.position='absolute';selected.style.left='0';selected.style.top='-1px';selected.style.right='18px';selected.style.height='16px';
  selected.style.lineHeight='16px';selected.style.whiteSpace='nowrap';selected.style.overflow='hidden';selected.style.textOverflow='ellipsis';selected.style.color='#fff';selected.style.fontSize='9px';selected.style.pointerEvents='none';
  element.prepend(selected);return selected;
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
  const option=options[index],selected=selectedLabel(element);
  selected.textContent=String(option.label??'');
  element.dataset.sourceSelectedIndex=String(index);
  element.dataset.sourceSelectedValue=String(option.valueExpression??option.value??'');
  element.dataset.sourceInitialSelection='constructor SelectItem(...)';
}
function createSourceScrollbar(dropdown,viewport,content,maxValue,visibleSize){
  const scroll=document.createElement('div');scroll.className='source-combo-scrollbar';
  Object.assign(scroll.style,{position:'absolute',right:'0px',top:'0px',width:`${SCROLL_WIDTH}px`,height:'100%',background:'#000',border:`1px solid ${PRIMARY}`,boxSizing:'border-box'});
  scroll.dataset.sourceType='DXVScrollBar';scroll.dataset.sourceChange=String(SCROLL_CHANGE);scroll.dataset.sourceVisibleSize=String(visibleSize);scroll.dataset.sourceMaxValue=String(maxValue);
  dropdown.append(scroll);

  const makeButton=(index,className)=>{const img=document.createElement('img');img.src=asset('Interface',index);img.draggable=false;img.className=className;img.style.position='absolute';img.style.left='1px';img.style.pointerEvents='auto';scroll.append(img);return img};
  const up=makeButton(44,'source-combo-scroll-up');up.style.top='1px';
  const down=makeButton(46,'source-combo-scroll-down');down.style.bottom='0px';
  const thumb=makeButton(45,'source-combo-scroll-thumb');thumb.style.top='16px';thumb.style.cursor='ns-resize';
  let value=0,dragStartY=0,dragStartValue=0;
  const maxScroll=Math.max(0,maxValue-visibleSize);
  const scrollHeight=Math.max(0,visibleSize-50);
  function clamp(next){return Math.max(0,Math.min(maxScroll,Math.round(next)))}
  function render(){
    value=clamp(value);content.style.transform=`translateY(${-value}px)`;scroll.dataset.value=String(value);
    const enabled=maxScroll>0;up.style.opacity=value>0?'1':'.45';down.style.opacity=value<maxScroll?'1':'.45';thumb.style.opacity=enabled?'1':'.45';
    const y=maxScroll===0?16:16+Math.round(scrollHeight*(value/maxScroll));thumb.style.top=`${y}px`;
  }
  function setValue(next){value=clamp(next);render()}
  up.addEventListener('click',event=>{event.preventDefault();event.stopPropagation();setValue(value-SCROLL_CHANGE)});
  down.addEventListener('click',event=>{event.preventDefault();event.stopPropagation();setValue(value+SCROLL_CHANGE)});
  dropdown.addEventListener('wheel',event=>{event.preventDefault();event.stopPropagation();setValue(value+(event.deltaY>0?SCROLL_CHANGE:-SCROLL_CHANGE))},{passive:false});
  scroll.addEventListener('pointerdown',event=>{
    if(event.target===up||event.target===down||event.target===thumb)return;
    event.preventDefault();event.stopPropagation();
    const rect=scroll.getBoundingClientRect(),thumbHeight=Math.max(1,thumb.getBoundingClientRect().height||12);
    const localY=event.clientY-rect.top;
    const denominator=Math.max(1,scrollHeight);
    setValue((localY-(thumbHeight+thumbHeight/2))*maxScroll/denominator);
  });
  thumb.addEventListener('pointerdown',event=>{event.preventDefault();event.stopPropagation();dragStartY=event.clientY;dragStartValue=value;thumb.setPointerCapture?.(event.pointerId)});
  thumb.addEventListener('pointermove',event=>{if(!thumb.hasPointerCapture?.(event.pointerId))return;event.preventDefault();const delta=event.clientY-dragStartY;setValue(dragStartValue+(scrollHeight?delta*maxScroll/scrollHeight:0))});
  thumb.addEventListener('pointerup',event=>thumb.releasePointerCapture?.(event.pointerId));
  render();
  return {scroll,setValue};
}
function showDropdown(element,resolved){
  closeDropdown(element);
  const p=resolved.control.properties||{};
  const normalHeight=intFrom(p.NormalHeight,16),dropDownHeight=Math.max(normalHeight,intFrom(p.DropDownHeight,123));
  const options=Array.isArray(resolved.control.comboOptions)?resolved.control.comboOptions:[];
  // DXListBox MaxValue is the summed item height. Its items use their label height;
  // the default combo/list font resolves to the same compact 16px row used here.
  const maxValue=options.length*ROW_HEIGHT;
  const totalHeight=Math.min(maxValue+normalHeight+2,dropDownHeight);
  const listHeight=Math.max(0,totalHeight-normalHeight-2);
  element.style.height=`${Math.max(normalHeight,totalHeight)}px`;
  element.dataset.sourceComboShowing='true';
  element.dataset.sourceNormalHeight=String(normalHeight);element.dataset.sourceDropDownHeight=String(dropDownHeight);
  element.dataset.sourceComboOptionCount=String(options.length);element.dataset.sourceComboOptionsInvented='false';
  element.dataset.sourceListBoxMaxValue=String(maxValue);element.dataset.sourceListBoxVisibleSize=String(listHeight);element.dataset.sourceScrollChange=String(SCROLL_CHANGE);

  const dropdown=document.createElement('div');dropdown.className='source-combo-dropdown';
  dropdown.id=`source-combo-${crypto.randomUUID?.()||Math.random().toString(36).slice(2)}`;
  Object.assign(dropdown.style,{position:'absolute',height:`${listHeight}px`,background:'#000',border:`1px solid ${PRIMARY}`,overflow:'hidden',zIndex:'10000',boxSizing:'border-box'});
  dropdown.dataset.sourceType='DXListBox';dropdown.dataset.sourceParentControl=resolved.control.name||'';dropdown.dataset.sourceParentWindow=resolved.item.id||resolved.item.field||'';
  element.dataset.sourceComboDropdownId=dropdown.id;stage.append(dropdown);dropdownPosition(element,dropdown,normalHeight);

  const viewport=document.createElement('div');viewport.className='source-combo-list-viewport';
  Object.assign(viewport.style,{position:'absolute',left:'0',top:'0',bottom:'0',right:`${SCROLL_WIDTH+1}px`,overflow:'hidden'});dropdown.append(viewport);
  const content=document.createElement('div');content.className='source-combo-list-content';Object.assign(content.style,{position:'absolute',left:'0',right:'0',top:'0'});viewport.append(content);
  const selected=selectedLabel(element);
  options.forEach((option,index)=>{
    const row=document.createElement('div');row.className='source-combo-option';row.textContent=String(option.label??'');
    Object.assign(row.style,{height:`${ROW_HEIGHT}px`,lineHeight:`${ROW_HEIGHT}px`,padding:'0 2px',boxSizing:'border-box',fontSize:'9px',color:PRIMARY,whiteSpace:'nowrap',overflow:'hidden',textOverflow:'ellipsis',cursor:'pointer',background:'transparent'});
    row.dataset.optionIndex=String(index);row.dataset.sourceValue=String(option.valueExpression??option.value??'');
    const current=Number(element.dataset.sourceSelectedIndex)===index;
    if(current){row.dataset.selected='true';row.style.color='#fff';row.style.background='rgba(128,64,64,.5)'}
    row.addEventListener('pointerenter',()=>{if(row.dataset.selected!=='true'){row.style.color=PRIMARY;row.style.background='rgba(64,32,32,.25)'}});
    row.addEventListener('pointerleave',()=>{if(row.dataset.selected!=='true'){row.style.color=PRIMARY;row.style.background='transparent'}});
    row.addEventListener('click',event=>{
      event.preventDefault();event.stopPropagation();selected.textContent=String(option.label??'');
      element.dataset.sourceSelectedIndex=String(index);element.dataset.sourceSelectedValue=String(option.valueExpression??option.value??'');
      closeDropdown(element);element.dispatchEvent(new CustomEvent('origins:source-combo-selected',{bubbles:true,detail:{index,option}}));
    });
    content.append(row);
  });
  createSourceScrollbar(dropdown,viewport,content,maxValue,listHeight);
}
function install(element){
  if(!(element instanceof Element)||element.dataset.sourceComboRuntime==='true')return;
  const resolved=sourceControl(element);if(!resolved)return;
  element.dataset.sourceComboRuntime='true';
  const p=resolved.control.properties||{},normalHeight=intFrom(p.NormalHeight,16),dropDownHeight=Math.max(normalHeight,intFrom(p.DropDownHeight,123));
  element.dataset.sourceNormalHeight=String(normalHeight);element.dataset.sourceDropDownHeight=String(dropDownHeight);element.dataset.sourceComboShowing='false';
  element.style.height=`${normalHeight}px`;selectedLabel(element);applyInitialSelection(element,resolved.control);
  const arrow=[...element.querySelectorAll('img')].find(image=>/GameInter\/00795\.png$/.test(image.src))||element.querySelector('img:last-of-type');
  if(arrow){
    arrow.dataset.sourceComboDownArrow='GameInter#795';arrow.style.pointerEvents='auto';
    arrow.addEventListener('click',event=>{event.preventDefault();event.stopImmediatePropagation();if(element.dataset.sourceComboShowing==='true')closeDropdown(element);else showDropdown(element,resolved)},true);
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
fetch('ui-source-spec.json',{cache:'no-store'}).then(r=>{if(!r.ok)throw new Error(`ui-source-spec.json ${r.status}`);return r.json()}).then(value=>{spec=value;stage.querySelectorAll('.dx-combobox[data-control-index]').forEach(install);console.info('ORIGINS DXComboBox source runtime: DXListBox + Interface 44/46/45 scrollbar, Change=15, source selections; runtime options neutral')}).catch(error=>console.error('Unable to load DXComboBox manifest',error));
