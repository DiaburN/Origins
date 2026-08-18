// Source-faithful InventoryDialog neutral/local behavior. Inventory items, user
// currencies and bag weight are runtime data and are never fabricated.
const stage=document.querySelector('#stage');
function control(root,name){return root?.querySelector?.(`[data-control-name="${CSS.escape(name)}"]`)||null}
function setVisible(element,visible){if(!element)return;element.hidden=!visible;element.dataset.sourceDynamicVisible=String(visible)}
function openOrToggle(id){const existing=document.querySelector(`#w-${CSS.escape(id)}`);if(existing){existing.remove();return null}document.querySelector(`[data-window-id="${CSS.escape(id)}"]`)?.click();return document.querySelector(`#w-${CSS.escape(id)}`)}
function install(root){
  if(!root||root.id!=='w-inventory'||root.dataset.sourceInventoryRuntime==='true')return;
  root.dataset.sourceInventoryRuntime='true';root.dataset.sourceInventoryMode='Normal';root.dataset.sourceInventoryItems='runtime GameScene.Game.Inventory';root.dataset.sourceCurrencyValues='runtime user currency';root.dataset.sourceBagWeight='runtime MapObject.User';root.dataset.sourceSelectedItems='runtime-only';
  setVisible(control(root,'TrashButton'),true);setVisible(control(root,'SellButton'),false);

  const sort=control(root,'SortButton');
  sort?.addEventListener('click',event=>{event.preventDefault();event.stopImmediatePropagation();root.dataset.sourceNetworkAction='C.ItemSort { Grid = GridType.Inventory }';root.dataset.sourceNetworkActionExecuted='false'},true);

  const trash=control(root,'TrashButton');
  trash?.addEventListener('click',event=>{
    event.preventDefault();event.stopImmediatePropagation();
    root.dataset.sourceTrashContract='requires DXItemCell.SelectedCell, item != null, !Locked, !Marriage, GridType.Inventory';
    root.dataset.sourceTrashAction='C.ItemDelete { Grid, Slot }';root.dataset.sourceTrashActionExecuted='false';
  },true);

  const sell=control(root,'SellButton');
  sell?.addEventListener('click',event=>{event.preventDefault();event.stopImmediatePropagation();root.dataset.sourceSellContract='only runtime InventoryMode.Sell with real selected/sellable items';root.dataset.sourceSellAction='C.NPCSell';root.dataset.sourceSellActionExecuted='false'},true);

  const wallet=control(root,'WalletLabel');
  wallet?.addEventListener('click',event=>{event.preventDefault();event.stopImmediatePropagation();openOrToggle('currency')},true);

  for(const name of ['PrimaryCurrencyLabel','SecondaryCurrencyLabel']){
    control(root,name)?.addEventListener('click',event=>{event.preventDefault();event.stopImmediatePropagation();root.dataset.sourceCurrencyPickupContract='requires real GameScene.Game.User.GetCurrency + CanPickup + Amount';root.dataset.sourceCurrencyPickupExecuted='false'},true);
  }
}
function scan(node){if(!(node instanceof Element))return;if(node.id==='w-inventory')queueMicrotask(()=>install(node));node.querySelectorAll?.('#w-inventory').forEach(root=>queueMicrotask(()=>install(root)))}
new MutationObserver(records=>records.forEach(record=>record.addedNodes.forEach(scan))).observe(stage,{childList:true,subtree:true});
install(document.querySelector('#w-inventory'));
console.info('ORIGINS Inventory source runtime active: Normal mode + Wallet toggle; item/currency/server actions neutral');
