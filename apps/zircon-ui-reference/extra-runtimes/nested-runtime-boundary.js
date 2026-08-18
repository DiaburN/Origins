// Final nested/transient runtime-data boundary. Source constructor literals and
// already-implemented Message/Input/Amount/Colour/LFG behavior are preserved;
// account/character/market/item payloads stay neutral until real constructor or
// live data exists.
const stage=document.querySelector('#stage');
let spec=null;
function itemFor(root){if(!spec||!root?.dataset?.nestedSourceClass)return null;return (spec.nestedWindows||[]).find(item=>item.sourceClass===root.dataset.nestedSourceClass)||null}
function exactLiteral(raw){const text=String(raw??'').trim();if(text==='string.Empty')return '';if(/^"(?:\\.|[^"\\])*"$/.test(text)){try{return JSON.parse(text)}catch{return text.slice(1,-1)}}return null}
function unresolvedRuntimeText(control){if(control?.resolvedText!==undefined&&control?.resolvedText!==null)return false;const p=control?.properties||{},raw=p.Text??p.Label??p.Title;if(raw===undefined)return true;if(exactLiteral(raw)!==null)return false;if(/^CEnvir\.Language\./.test(String(raw).trim()))return false;return true}
function install(root){
  const item=itemFor(root);if(!item||root.dataset.sourceNestedBoundary==='true')return;root.dataset.sourceNestedBoundary='true';root.dataset.sourceNestedCategory=item.category||'';root.dataset.sourceConstructorRuntimeDataInvented='false';
  for(const element of root.querySelectorAll('[data-control-index]')){
    const index=Number.parseInt(element.dataset.controlIndex||'',10);if(!Number.isInteger(index))continue;const control=item.controls?.[index];if(!control)continue;
    if(control.type==='DXItemCell'||control.type==='DXItemGrid'){element.dataset.sourceItem='constructor/runtime item only';element.dataset.sourceItemInvented='false'}
    if(control.type==='DXLabel'&&unresolvedRuntimeText(control)){element.textContent='';element.dataset.sourceNestedRuntimeText='true';element.dataset.sourceRuntimeTextInvented='false'}
  }
  if(['login','character-select','market'].includes(item.category))root.dataset.sourceLivePayload=`${item.category} runtime/account/server data`;
  if(item.sourceClass==='DXKeyBindWindow')root.dataset.sourceKeyBindings='runtime user key-bind data; source tree/chrome only';
  if(item.sourceClass==='DXMessageBox'){root.dataset.sourceMessage='constructor string';root.dataset.sourceCaption='constructor string'}
  if(item.sourceClass==='DXInputWindow'){root.dataset.sourceMessage='constructor string';root.dataset.sourceCaption='constructor string';root.dataset.sourceInput='user input'}
  if(item.sourceClass==='DXItemAmountWindow'){root.dataset.sourceItem='constructor ClientUserItem';root.dataset.sourceAmountMax='item.Count runtime constructor value'}
}
function scan(node){if(!(node instanceof Element))return;if(node.matches?.('.nested-source-window'))queueMicrotask(()=>install(node));node.querySelectorAll?.('.nested-source-window').forEach(root=>queueMicrotask(()=>install(root)))}
new MutationObserver(records=>records.forEach(record=>record.addedNodes.forEach(scan))).observe(stage,{childList:true,subtree:true});
fetch('ui-source-spec.json',{cache:'no-store'}).then(r=>{if(!r.ok)throw new Error(`ui-source-spec.json ${r.status}`);return r.json()}).then(value=>{spec=value;stage.querySelectorAll('.nested-source-window').forEach(install);console.info(`ORIGINS nested runtime boundary active: ${(spec.nestedWindows||[]).length} source windows`) }).catch(error=>console.error('Unable to load nested runtime-boundary manifest',error));
