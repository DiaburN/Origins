// Source-faithful GameStoreDialog local state. Store rows, top items and currency
// amounts depend on runtime globals/player data and are deliberately not fabricated.
const stage=document.querySelector('#stage');
let spec=null;
function control(root,name){return root?.querySelector?.(`[data-control-name="${CSS.escape(name)}"]`)||null}
function language(key,fallback=''){return spec?.language?.English?.[key]??fallback}
function setButtonText(button,text){
  if(!button)return;
  const label=button.querySelector('.dx-button-label,.source-button-label');
  if(label)label.textContent=text;
  button.dataset.sourceDynamicLabel=text;
}
function refreshCurrencyState(root){
  const hunt=root.dataset.sourceUseHuntGold==='true';
  const toggle=control(root,'CurrencyToggleButton');
  setButtonText(toggle,language(hunt?'GameStoreDialogUseGameGoldLabel':'GameStoreDialogUseHuntGoldLabel',hunt?'Use Game Gold':'Use Hunt Gold'));
  const amount=control(root,'GameGoldLabel');
  if(amount){
    amount.textContent='';
    amount.dataset.sourceRuntimeAmount=hunt?'GameScene.Game.User.HuntGold.Amount':'GameScene.Game.User.GameGold.Amount';
    amount.dataset.sourceCurrencyLanguageKey=hunt?'GameStoreDialogHuntGoldLabel':'GameStoreDialogGameGoldLabel';
  }
  root.dataset.sourceGameStoreCurrency=hunt?'HuntGold':'GameGold';
  root.dataset.sourceStoreTreeRebuild='BuildFolderTree() requires Globals.StoreInfoList';
  root.dataset.sourceStoreRefresh='RefreshItems() requires runtime store rows';
}
function install(root){
  if(!root||root.id!=='w-game-store'||root.dataset.sourceGameStoreRuntime==='true')return;
  root.dataset.sourceGameStoreRuntime='true';
  root.dataset.sourceUseHuntGold='false';
  root.dataset.sourceInitialSort='MarketPlaceStoreSort.Alphabetical';
  root.dataset.sourceStoreRows='runtime Globals.StoreInfoList';
  root.dataset.sourceTopFive='runtime GameStoreTopItemsControl';
  refreshCurrencyState(root);

  const toggle=control(root,'CurrencyToggleButton');
  toggle?.addEventListener('click',event=>{
    event.preventDefault();event.stopImmediatePropagation();
    root.dataset.sourceUseHuntGold=String(root.dataset.sourceUseHuntGold!=='true');
    refreshCurrencyState(root);
  },true);

  const search=control(root,'SearchButton');
  search?.addEventListener('click',()=>{
    root.dataset.sourceSearchRequested='true';
    root.dataset.sourceSearchExpression='ItemList.Search(SearchBox.TextBox.Text, selected sort)';
    root.dataset.sourceSearchResultsInvented='false';
  },true);

  const recharge=control(root,'BuyGameGoldButton');
  recharge?.addEventListener('click',event=>{
    event.preventDefault();event.stopImmediatePropagation();
    root.dataset.sourceRechargeContract='if !Observer && !TestServer => DXMessageBox YesNo; Yes opens BuyAddress+User.Name';
    root.dataset.sourceRechargeExecuted='false';
  },true);
}
function scan(node){if(!(node instanceof Element))return;if(node.id==='w-game-store')queueMicrotask(()=>install(node));node.querySelectorAll?.('#w-game-store').forEach(root=>queueMicrotask(()=>install(root)))}
new MutationObserver(records=>records.forEach(record=>record.addedNodes.forEach(scan))).observe(stage,{childList:true,subtree:true});
fetch('ui-source-spec.json',{cache:'no-store'}).then(r=>{if(!r.ok)throw new Error(`ui-source-spec.json ${r.status}`);return r.json()}).then(value=>{spec=value;install(document.querySelector('#w-game-store'));console.info('ORIGINS GameStore fidelity runtime active: currency toggle source-backed; store/player data neutral')}).catch(error=>console.error('Unable to load GameStore source manifest',error));
