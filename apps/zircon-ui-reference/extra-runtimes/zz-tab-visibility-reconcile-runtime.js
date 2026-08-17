// Final visibility reconciliation after all source-control initialization modules.
// It preserves literal Visible=false and re-applies selected-tab ancestry so a
// global source-visible control can never leak out of an inactive DXTab.
const stage=document.querySelector('#stage');
let spec=null;
function boolFrom(raw,fallback=true){const v=String(raw??'').trim().toLowerCase();return v==='true'?true:v==='false'?false:fallback}
function simpleParent(raw){const value=String(raw??'').trim();return /^[A-Za-z_][A-Za-z0-9_]*$/.test(value)&&value!=='this'&&value!=='ActiveScene'?value:null}
function itemFor(root){if(!spec||!root?.id?.startsWith('w-'))return null;const id=root.id.slice(2);return [...(spec.windows||[]),...(spec.nestedWindows||[])].find(item=>item.id===id)||null}
function reconcile(root){
  const item=itemFor(root);if(!item)return;const controls=item.controls||[],byName=new Map(controls.map(c=>[c.name,c]));
  const selected=new Map();
  for(const tab of controls.filter(c=>c.type==='DXTab'||c.type==='DXConfigTab')){
    const tabControl=simpleParent(tab.properties?.Parent);if(!tabControl)continue;
    const el=root.querySelector(`[data-control-name="${CSS.escape(tab.name)}"]`);
    if(el&&(el.classList.contains('selected')||el.classList.contains('dx-button-SelectedTab')))selected.set(tabControl,tab.name);
  }
  // If the runtime has not stamped a selected class yet, follow Zircon's first
  // source-visible tab rule instead of exposing all pages.
  for(const tab of controls.filter(c=>c.type==='DXTab'||c.type==='DXConfigTab')){
    const tabControl=simpleParent(tab.properties?.Parent);if(!tabControl||selected.has(tabControl))continue;
    if(tab.tabButtonVisible===false||!boolFrom(tab.properties?.Visible,true))continue;selected.set(tabControl,tab.name);
  }
  const visibleThroughTabs=control=>{
    let current=control;const visited=new Set();
    while(current){
      const parentName=simpleParent(current.properties?.Parent);if(!parentName||visited.has(parentName))return true;visited.add(parentName);
      const parent=byName.get(parentName);if(!parent)return true;
      if(parent.type==='DXTab'||parent.type==='DXConfigTab'){
        if(parent.tabButtonVisible===false||!boolFrom(parent.properties?.Visible,true))return false;
        const group=simpleParent(parent.properties?.Parent);if(group&&selected.get(group)!==parent.name)return false;
      }
      current=parent;
    }
    return true;
  };
  for(const element of root.querySelectorAll('[data-control-index]')){
    const index=Number.parseInt(element.dataset.controlIndex||'',10);if(!Number.isInteger(index))continue;const control=controls[index];if(!control)continue;
    const literalVisible=control.sourceNeutralVisible===false?false:boolFrom(control.properties?.Visible,true);
    const tabVisible=visibleThroughTabs(control);
    if(!literalVisible||!tabVisible)element.hidden=true;
    else if(control.type==='DXTab'||control.type==='DXConfigTab'||simpleParent(control.properties?.Parent))element.hidden=false;
    element.dataset.sourceTabVisible=String(tabVisible);
  }
}
function scan(node){if(!(node instanceof Element))return;if(node.matches?.('.window,.generic-window'))queueMicrotask(()=>reconcile(node));node.querySelectorAll?.('.window,.generic-window').forEach(root=>queueMicrotask(()=>reconcile(root)))}
new MutationObserver(records=>records.forEach(record=>record.addedNodes.forEach(scan))).observe(stage,{childList:true,subtree:true});
stage.addEventListener('click',event=>{if(!(event.target instanceof Element))return;const tab=event.target.closest('[data-control-type="DXTab"],[data-control-type="DXConfigTab"]');const root=tab?.closest('.window,.generic-window');if(root)queueMicrotask(()=>reconcile(root))},false);
fetch('ui-source-spec.json',{cache:'no-store'}).then(r=>{if(!r.ok)throw new Error(`ui-source-spec.json ${r.status}`);return r.json()}).then(value=>{spec=value;stage.querySelectorAll('.window,.generic-window').forEach(reconcile);console.info('ORIGINS final source/tab visibility reconciliation active')}).catch(error=>console.error('Unable to load final tab visibility manifest',error));