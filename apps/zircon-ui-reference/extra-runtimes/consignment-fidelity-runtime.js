// Source-faithful ConsignmentDialog tab state. Marketplace rows/results remain
// runtime/server data and are never fabricated in the reference viewer.
const stage=document.querySelector('#stage');
const pad=value=>String(value).padStart(5,'0');
const asset=(library,index)=>`assets/${library}/${pad(index)}.png`;
function control(root,name){return root?.querySelector?.(`[data-control-name="${CSS.escape(name)}"]`)||null}
function setVisible(element,visible){if(!element)return;element.hidden=!visible;element.dataset.sourceDynamicVisible=String(visible)}
function setTabImage(root,index){
  const element=control(root,'TabImage');if(!element)return;
  const image=element instanceof HTMLImageElement?element:element.querySelector('img');
  if(image)image.src=asset('Interface',index);
  element.dataset.sourceDynamicIndex=String(index);
}
function setActiveTab(root,search){
  setTabImage(root,search?301:302);
  setVisible(control(root,'BuyButton'),search);
  setVisible(control(root,'ConsignButton'),!search);
  setVisible(control(root,'RemoveListingButton'),!search);
  setVisible(control(root,'BuyGuildBox'),search);
  setVisible(control(root,'ConsignGuildBox'),!search);
  setVisible(control(root,'ResultCountLabel'),search);
  setVisible(control(root,'ConsignResultCountLabel'),!search);
  root.dataset.sourceConsignmentTab=search?'SearchTab':'ConsignTab';
  root.dataset.sourceSelectionReset=search?'SelectedConsignRow=null':'SelectedRow=null; RefreshConsignList()';
}
function install(root){
  if(!root||root.id!=='w-consignment'||root.dataset.sourceConsignmentRuntime==='true')return;
  root.dataset.sourceConsignmentRuntime='true';
  root.dataset.sourceMarketplaceRows='runtime-only';
  root.dataset.sourceSearchResults='runtime-only';
  // Constructor ends with SearchTab.TabButton.InvokeMouseClick().
  setActiveTab(root,true);
  const searchTab=control(root,'SearchTab');
  const consignTab=control(root,'ConsignTab');
  searchTab?.addEventListener('click',()=>setActiveTab(root,true),true);
  consignTab?.addEventListener('click',()=>setActiveTab(root,false),true);
  const searchButton=control(root,'SearchButton');
  searchButton?.addEventListener('click',()=>{
    root.dataset.sourceMarketplaceSearch='requested';
    root.dataset.sourceMarketplaceSearchExecuted='false';
  },true);
}
function scan(node){if(!(node instanceof Element))return;if(node.id==='w-consignment')queueMicrotask(()=>install(node));node.querySelectorAll?.('#w-consignment').forEach(root=>queueMicrotask(()=>install(root)))}
new MutationObserver(records=>records.forEach(record=>record.addedNodes.forEach(scan))).observe(stage,{childList:true,subtree:true});
install(document.querySelector('#w-consignment'));
console.info('ORIGINS ConsignmentDialog fidelity runtime active: Search/Consign source tab state, marketplace data neutral');
