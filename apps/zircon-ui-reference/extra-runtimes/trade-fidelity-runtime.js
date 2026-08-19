// Source-faithful TradeDialog behavior that can be reproduced without a live server.
// We never fabricate inventory, gold, partner confirmation or network success.
const stage=document.querySelector('#stage');

function control(root,name){return root?.querySelector?.(`[data-control-name="${CSS.escape(name)}"]`)||null}
function disableSourceButton(button){
  if(!button)return;
  button.dataset.sourceDynamicEnabled='false';
  button.setAttribute('aria-disabled','true');
  button.style.pointerEvents='none';
}
function install(root){
  if(!root||root.id!=='w-trade'||root.dataset.sourceTradeRuntime==='true')return;
  root.dataset.sourceTradeRuntime='true';
  root.dataset.sourceTradeState='constructor-neutral';
  root.dataset.sourceTradeIsTrading='false';
  root.dataset.sourceTradePlayerItems='runtime-only';
  root.dataset.sourceTradeUserGold='runtime-user-gold';
  root.dataset.sourceTradePlayerGold='runtime-partner-gold';

  const confirm=control(root,'ConfirmButton');
  if(confirm){
    confirm.addEventListener('click',event=>{
      if(confirm.dataset.sourceDynamicEnabled==='false'){
        event.preventDefault();event.stopImmediatePropagation();return;
      }
      // Zircon disables immediately, then enqueues C.TradeConfirm. There is no
      // truthful server response in the reference viewer, so stop at pending.
      event.preventDefault();event.stopImmediatePropagation();
      disableSourceButton(confirm);
      root.dataset.sourceTradeState='confirm-pending';
      root.dataset.sourceNetworkAction='C.TradeConfirm';
      root.dataset.sourceNetworkActionExecuted='false';
    },true);
  }

  const userGold=control(root,'UserGoldLabel');
  if(userGold){
    userGold.dataset.sourceRuntimeValue='GameScene.Game.User.Gold.Amount';
    userGold.addEventListener('click',event=>{
      // Source opens DXItemAmountWindow("Trade Gold", current user gold).
      // Without a real user-gold payload MaxValue/Change would be fabricated.
      event.preventDefault();event.stopImmediatePropagation();
      root.dataset.sourceTradeGoldAmountWindow='requires-runtime-user-gold';
    },true);
  }

  const close=control(root,'CloseButton');
  if(close){
    close.addEventListener('click',()=>{
      root.dataset.sourceTradeCloseContract='if IsTrading && !Observer => C.TradeClose';
      root.dataset.sourceTradeCloseNetworkExecuted='false';
    },true);
  }
}
function scan(node){
  if(!(node instanceof Element))return;
  if(node.id==='w-trade')queueMicrotask(()=>install(node));
  node.querySelectorAll?.('#w-trade').forEach(root=>queueMicrotask(()=>install(root)));
}
new MutationObserver(records=>records.forEach(record=>record.addedNodes.forEach(scan))).observe(stage,{childList:true,subtree:true});
install(document.querySelector('#w-trade'));
console.info('ORIGINS TradeDialog fidelity runtime active: confirm pending/network-neutral + runtime-gold guard');
