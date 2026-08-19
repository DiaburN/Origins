// Source-faithful MonsterDialog expanded/collapsed state. Runtime monster stats
// remain empty; this only reproduces constructor Config default and toggle UI.
const stage=document.querySelector('#stage');
let spec=null;
const pad=value=>String(value).padStart(5,'0');
const asset=(library,index)=>`assets/${library}/${pad(index)}.png`;
function itemFor(root){if(!spec||!root?.id?.startsWith('w-'))return null;const id=root.id.slice(2);return spec.windows?.find(item=>item.id===id)||null}
function descendants(controls,parentName){
  const result=new Set([parentName]);let changed=true;
  while(changed){changed=false;for(const control of controls){const parent=String(control.properties?.Parent??'').trim();if(result.has(parent)&&!result.has(control.name)){result.add(control.name);changed=true}}}
  return result;
}
function setState(root,expanded){
  const item=itemFor(root);if(!item)return;const controls=item.controls||[];
  root.style.height=`${expanded?175:54}px`;root.dataset.sourceMonsterExpanded=String(expanded);
  const button=root.querySelector('[data-control-name="ExpandButton"]');if(button){const image=button instanceof HTMLImageElement?button:button.querySelector('img');if(image)image.src=asset('Interface',expanded?44:46)}
  const names=descendants(controls,'DetailsPanel');
  for(const element of root.querySelectorAll('[data-control-index]')){
    const index=Number.parseInt(element.dataset.controlIndex||'',10);if(!Number.isInteger(index))continue;const control=controls[index];if(control&&names.has(control.name))element.hidden=!expanded;
  }
}
function install(root){
  if(!(root instanceof Element)||root.id!=='w-monster'||root.dataset.sourceMonsterToggle==='true')return;
  const item=itemFor(root);if(!item?.constructorFinalState)return;root.dataset.sourceMonsterToggle='true';setState(root,true);
  const button=root.querySelector('[data-control-name="ExpandButton"]');button?.addEventListener('click',event=>{event.preventDefault();event.stopPropagation();setState(root,root.dataset.sourceMonsterExpanded!=='true')});
  root.dataset.runtimeMonsterData='neutral/no fabricated monster stats';
}
function scan(node){if(!(node instanceof Element))return;if(node.id==='w-monster')queueMicrotask(()=>install(node));node.querySelectorAll?.('#w-monster').forEach(root=>queueMicrotask(()=>install(root)))}
new MutationObserver(records=>records.forEach(record=>record.addedNodes.forEach(scan))).observe(stage,{childList:true,subtree:true});
fetch('ui-source-spec.json',{cache:'no-store'}).then(r=>{if(!r.ok)throw new Error(`ui-source-spec.json ${r.status}`);return r.json()}).then(value=>{spec=value;const root=document.querySelector('#w-monster');if(root)install(root);console.info('ORIGINS MonsterDialog expand/collapse runtime active')}).catch(error=>console.error('Unable to load MonsterDialog fidelity manifest',error));