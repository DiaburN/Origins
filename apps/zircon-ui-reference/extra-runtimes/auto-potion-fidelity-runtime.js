// Source-faithful AutoPotionDialog local row behavior. Eight deterministic rows
// are generated into the manifest by augment_auto_potion_reference.py. Linked
// ItemInfo and C.AutoPotionLinkChanged server effects remain runtime-only.
const stage=document.querySelector('#stage');
const pad=value=>String(value).padStart(5,'0');
const asset=(library,index)=>`assets/${library}/${pad(index)}.png`;
const ROWS=8;
function control(root,name){return root?.querySelector?.(`[data-control-name="${CSS.escape(name)}"]`)||null}
function rowName(index){return `AutoPotionRow${String(index+1).padStart(2,'0')}`}
function numberBox(root,index,kind){return control(root,`${rowName(index)}${kind}TargetBox`)}
function checkBox(root,index){return control(root,`${rowName(index)}EnabledCheckBox`)}
function itemCell(root,index){return control(root,`${rowName(index)}ItemCell`)}
function readNumber(box){const raw=box?.dataset?.value??box?.querySelector?.('.dx-number-value')?.textContent??'0';const value=Number(raw);return Number.isFinite(value)?Math.max(0,Math.min(50000,Math.trunc(value))):0}
function setNumber(box,value){if(!box)return;value=Math.max(0,Math.min(50000,Math.trunc(value)));box.dataset.value=String(value);const field=box.querySelector('.dx-number-value');if(field)field.textContent=String(value)}
function readChecked(box){if(!box)return false;const explicit=box.dataset.sourceChecked;if(explicit==='true'||explicit==='false')return explicit==='true';const image=box.querySelector(':scope > img');return Boolean(image&&/GameInter\/00162\.png$/.test(image.src))}
function setChecked(box,value){if(!box)return;box.dataset.sourceChecked=String(Boolean(value));const image=box.querySelector(':scope > img');if(image)image.src=asset('GameInter',value?162:161)}
function readState(root,index){return {health:readNumber(numberBox(root,index,'Health')),mana:readNumber(numberBox(root,index,'Mana')),enabled:readChecked(checkBox(root,index)),quickInfo:itemCell(root,index)?.dataset.sourceQuickInfoIndex??''}}
function applyState(root,index,state){setNumber(numberBox(root,index,'Health'),state.health);setNumber(numberBox(root,index,'Mana'),state.mana);setChecked(checkBox(root,index),state.enabled);const cell=itemCell(root,index);if(cell)cell.dataset.sourceQuickInfoIndex=state.quickInfo||''}
function pending(root,index){const slots=new Set(String(root.dataset.sourcePendingAutoPotionSlots||'').split(',').filter(Boolean));slots.add(String(index));root.dataset.sourcePendingAutoPotionSlots=[...slots].sort((a,b)=>Number(a)-Number(b)).join(',');root.dataset.sourceNetworkAction='C.AutoPotionLinkChanged';root.dataset.sourceNetworkActionExecuted='false'}
function swapRows(root,a,b){if(a<0||a>=ROWS||b<0||b>=ROWS)return;const first=readState(root,a),second=readState(root,b);root.dataset.sourceAutoPotionUpdating='true';applyState(root,a,second);applyState(root,b,first);root.dataset.sourceAutoPotionUpdating='false';pending(root,a);pending(root,b);root.dataset.sourceLastAutoPotionSwap=`${a}<->${b}`}
function bindRow(root,index){
  const row=rowName(index);const up=control(root,`${row}UpButton`),down=control(root,`${row}DownButton`),hp=numberBox(root,index,'Health'),mp=numberBox(root,index,'Mana'),enabled=checkBox(root,index),cell=itemCell(root,index);
  if(cell){cell.dataset.sourceQuickInfo='runtime Globals.ItemInfoList / ClientAutoPotionLink';cell.dataset.sourceQuickInfoIndex=''}
  for(const box of [hp,mp]){
    if(!box||box.dataset.sourceAutoPotionObserved==='true')continue;box.dataset.sourceAutoPotionObserved='true';
    const observer=new MutationObserver(records=>{if(root.dataset.sourceAutoPotionUpdating==='true')return;if(records.some(record=>record.attributeName==='data-value'))pending(root,index)});observer.observe(box,{attributes:true,attributeFilter:['data-value']});
  }
  if(enabled&&enabled.dataset.sourceAutoPotionBound!=='true'){
    enabled.dataset.sourceAutoPotionBound='true';enabled.addEventListener('click',()=>queueMicrotask(()=>{if(root.dataset.sourceAutoPotionUpdating==='true')return;const image=enabled.querySelector(':scope > img');const checked=Boolean(image&&/GameInter\/00162\.png$/.test(image.src));enabled.dataset.sourceChecked=String(checked);pending(root,index)}));
  }
  if(up&&up.dataset.sourceAutoPotionBound!=='true'){
    up.dataset.sourceAutoPotionBound='true';up.addEventListener('click',event=>{if(index===0)return;event.preventDefault();event.stopImmediatePropagation();swapRows(root,index,index-1)},true);
  }
  if(down&&down.dataset.sourceAutoPotionBound!=='true'){
    down.dataset.sourceAutoPotionBound='true';down.addEventListener('click',event=>{if(index===ROWS-1)return;event.preventDefault();event.stopImmediatePropagation();swapRows(root,index,index+1)},true);
  }
}
function install(root){
  if(!root||root.id!=='w-auto-potion'||root.dataset.sourceAutoPotionRuntime==='true')return;root.dataset.sourceAutoPotionRuntime='true';root.dataset.sourceAutoPotionRowCount=String(ROWS);root.dataset.sourceAutoPotionUpdating='true';
  for(let i=0;i<ROWS;i++){applyState(root,i,{health:0,mana:0,enabled:false,quickInfo:''});bindRow(root,i)}
  root.dataset.sourceAutoPotionUpdating='false';root.dataset.sourceAutoPotionLinksInvented='false';root.dataset.sourceAutoPotionObserver='unknown-runtime';
  const scroll=control(root,'ScrollBar');if(scroll){scroll.dataset.sourceMaxValue='398';scroll.dataset.sourceVisibleSize='398';scroll.dataset.sourceScrollable='false'}
}
function scan(node){if(!(node instanceof Element))return;if(node.id==='w-auto-potion')queueMicrotask(()=>install(node));node.querySelectorAll?.('#w-auto-potion').forEach(root=>queueMicrotask(()=>install(root)))}
new MutationObserver(records=>records.forEach(record=>record.addedNodes.forEach(scan))).observe(stage,{childList:true,subtree:true});
install(document.querySelector('#w-auto-potion'));
console.info('ORIGINS AutoPotion source runtime active: 8 local rows, reorder/HP/MP/Enabled; item/server data neutral');
