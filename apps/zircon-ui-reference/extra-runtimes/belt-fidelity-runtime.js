// BeltDialog.OnClientAreaChanged source fidelity: one local DXLabel per Grid.Grid cell.
// This runtime never creates item/player/server data; it only mirrors the local hotkey label template.
const stage=document.querySelector('#stage');
let sourceSpec=null;
function beltItem(){return (sourceSpec?.windows||[]).find(item=>item.field==='BeltBox')||null}
function install(root){
  if(!(root instanceof Element)||root.id!=='w-belt'||!sourceSpec)return;
  const item=beltItem(),template=item?.beltHotkeyLabelTemplate;
  if(template?.passed!==true||template.fixedCountInvented!==false)return;
  const cells=[...root.querySelectorAll('.generic-grid .generic-cell')];
  cells.forEach((cell,index)=>{
    cell.style.position=cell.style.position||'relative';
    let label=cell.querySelector(':scope > .belt-source-hotkey-label');
    if(!label){label=document.createElement('div');label.className='belt-source-hotkey-label';cell.append(label)}
    label.textContent=String((index+1)%10);
    label.style.position='absolute';label.style.left='-2px';label.style.top='-1px';label.style.width='100%';label.style.height='100%';label.style.display='flex';label.style.alignItems='center';label.style.justifyContent='center';label.style.fontSize='10.6667px';label.style.fontStyle='italic';label.style.pointerEvents='none';label.dataset.sourceExpression='((i + 1) % 10).ToString()';label.dataset.sourceGridSlot=String(index);
  });
  root.dataset.sourceBeltHotkeyLabels=String(cells.length);
}
function scan(node){if(!(node instanceof Element))return;if(node.id==='w-belt')queueMicrotask(()=>install(node));const root=node.querySelector?.('#w-belt');if(root)queueMicrotask(()=>install(root))}
new MutationObserver(records=>{for(const record of records)for(const node of record.addedNodes)scan(node)}).observe(stage,{childList:true,subtree:true});
fetch('ui-source-spec.json',{cache:'no-store'}).then(response=>{if(!response.ok)throw new Error(`ui-source-spec.json ${response.status}`);return response.json()}).then(spec=>{sourceSpec=spec;const root=document.querySelector('#w-belt');if(root)install(root);console.info('ORIGINS Belt fidelity: local Grid.Grid hotkey labels source template active')}).catch(error=>console.error('Unable to load Belt fidelity manifest',error));
