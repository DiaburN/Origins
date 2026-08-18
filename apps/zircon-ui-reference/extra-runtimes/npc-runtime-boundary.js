// Shared runtime-data boundary for all GameScene NPC-category windows. Source
// chrome, deterministic empty-slot artwork and local controls remain untouched;
// linked items, goods, prices, refinement/socket results and NPC page content are
// runtime/server data and are never fabricated.
const stage=document.querySelector('#stage');
let spec=null;
function itemFor(root){if(!spec||!root?.id?.startsWith('w-'))return null;const id=root.id.slice(2);return (spec.windows||[]).find(item=>item.id===id)||null}
function literal(raw){const text=String(raw??'').trim();if(text==='string.Empty')return '';if(/^"(?:\\.|[^"\\])*"$/.test(text)){try{return JSON.parse(text)}catch{return text.slice(1,-1)}}return null}
function runtimeLabel(control){if(control?.resolvedText!==undefined&&control?.resolvedText!==null)return false;const p=control?.properties||{},raw=p.Text??p.Label??p.Title;if(raw===undefined)return true;if(literal(raw)!==null)return false;if(/^CEnvir\.Language\./.test(String(raw).trim()))return false;return true}
function install(root){
  const item=itemFor(root);if(!item||item.category!=='npc'||root.dataset.sourceNpcRuntimeBoundary==='true')return;root.dataset.sourceNpcRuntimeBoundary='true';root.dataset.sourceNpcData='runtime NPC/page/item/server state';root.dataset.sourceNpcDataInvented='false';root.dataset.sourceNpcServerResultInvented='false';root.dataset.sourceNpcSourceClass=item.sourceClass||item.class||'';
  for(const element of root.querySelectorAll('[data-control-index]')){
    const index=Number.parseInt(element.dataset.controlIndex||'',10);if(!Number.isInteger(index))continue;const control=item.controls?.[index];if(!control)continue;
    if(control.type==='DXItemCell'||control.type==='DXItemGrid'){element.dataset.sourceItem='runtime NPC-linked item/grid';element.dataset.sourceItemInvented='false'}
    if(control.type==='DXLabel'&&runtimeLabel(control)){element.textContent='';element.dataset.sourceNpcRuntimeText='true';element.dataset.sourceRuntimeTextInvented='false'}
    if(control.type==='DXButton'&&!/CloseButton$|CancelButton$/.test(String(control.name||''))){element.dataset.sourceNpcAction='source handler may require NPC/item/server state';element.dataset.sourceNpcActionExecuted='false'}
  }
  // Main NPC custom frame is deterministic and must not be replaced by a generic frame.
  if(item.id==='npc')root.dataset.sourceNpcFrame='GameInter#380/#381/#382 + source scrollbar #385/#387';
}
function scan(node){if(!(node instanceof Element))return;if(node.id?.startsWith('w-'))queueMicrotask(()=>install(node));node.querySelectorAll?.('[id^="w-"]').forEach(root=>queueMicrotask(()=>install(root)))}
new MutationObserver(records=>records.forEach(record=>record.addedNodes.forEach(scan))).observe(stage,{childList:true,subtree:true});
fetch('ui-source-spec.json',{cache:'no-store'}).then(r=>{if(!r.ok)throw new Error(`ui-source-spec.json ${r.status}`);return r.json()}).then(value=>{spec=value;stage.querySelectorAll('[id^="w-"]').forEach(install);console.info(`ORIGINS NPC runtime boundary active for ${(spec.windows||[]).filter(item=>item.category==='npc').length} source windows`) }).catch(error=>console.error('Unable to load NPC source manifest',error));
