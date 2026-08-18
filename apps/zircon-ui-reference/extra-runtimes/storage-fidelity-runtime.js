// Source-faithful StorageDialog local behavior. Inventory/storage item arrays and
// ItemSort server results remain runtime-only.
const stage=document.querySelector('#stage');
function control(root,name){return root?.querySelector?.(`[data-control-name="${CSS.escape(name)}"]`)||null}
function openWindow(id){
  const existing=document.querySelector(`#w-${CSS.escape(id)}`);if(existing)return existing;
  document.querySelector(`[data-window-id="${CSS.escape(id)}"]`)?.click();
  return document.querySelector(`#w-${CSS.escape(id)}`);
}
function resetCombo(combo){
  if(!combo)return;
  combo.dataset.sourceSelectedIndex='-1';combo.dataset.sourceSelectedValue='null';combo.dataset.sourceStorageFilter='null';
  const label=combo.querySelector(':scope > span');if(label)label.textContent='';
  combo.dispatchEvent(new CustomEvent('origins:source-combo-reset',{bubbles:true}));
}
function clearTextBox(element){
  if(!element)return;element.textContent='';element.dataset.sourceStorageFilter='';
  const input=element.querySelector('input,textarea,[contenteditable="true"]');if(input){if('value'in input)input.value='';else input.textContent=''}
}
function install(root){
  if(!root||root.id!=='w-storage'||root.dataset.sourceStorageRuntime==='true')return;
  root.dataset.sourceStorageRuntime='true';
  root.dataset.sourceStorageItems='runtime CEnvir.Storage';
  root.dataset.sourcePartsItems='runtime CEnvir.PartsStorage';
  root.dataset.sourceStorageSize='runtime GameScene.Game.StorageSize';

  // StorageDialog.OnIsVisibleChanged opens Inventory whenever Storage becomes visible.
  queueMicrotask(()=>{const inventory=openWindow('inventory');if(inventory)root.dataset.sourceInventoryForcedVisible='true'});

  const clear=control(root,'ClearButton');
  clear?.addEventListener('click',event=>{
    event.preventDefault();event.stopImmediatePropagation();
    resetCombo(control(root,'ItemTypeComboBox'));
    clearTextBox(control(root,'ItemNameTextBox'));
    root.dataset.sourceStorageFiltersCleared='true';
  },true);

  const sort=control(root,'SortButton');
  sort?.addEventListener('click',event=>{
    event.preventDefault();event.stopImmediatePropagation();
    root.dataset.sourceSortConfirmation='DXMessageBox YesNo: Are you sure you want to sort your storage?';
    root.dataset.sourceSortGrid='StorageTab visible ? GridType.Storage : GridType.PartsStorage';
    root.dataset.sourceNetworkAction='C.ItemSort';
    root.dataset.sourceNetworkActionExecuted='false';
  },true);
}
function scan(node){if(!(node instanceof Element))return;if(node.id==='w-storage')queueMicrotask(()=>install(node));node.querySelectorAll?.('#w-storage').forEach(root=>queueMicrotask(()=>install(root)))}
new MutationObserver(records=>records.forEach(record=>record.addedNodes.forEach(scan))).observe(stage,{childList:true,subtree:true});
install(document.querySelector('#w-storage'));
console.info('ORIGINS StorageDialog fidelity runtime active: Inventory co-open + clear filters; storage/server data neutral');
