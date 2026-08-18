// Source-faithful CurrencyDialog neutral state. CurrencyTree chrome exists, but
// headers/items are built only from GameScene.Game.User.Currencies at runtime.
const stage=document.querySelector('#stage');
function control(root,name){return root?.querySelector?.(`[data-control-name="${CSS.escape(name)}"]`)||null}
function install(root){
  if(!root||root.id!=='w-currency'||root.dataset.sourceCurrencyRuntime==='true')return;
  root.dataset.sourceCurrencyRuntime='true';root.dataset.sourceCurrencyTree='empty runtime tree';root.dataset.sourceCurrencyHeaders='0';root.dataset.sourceCurrencyItems='0';root.dataset.sourceCurrenciesInvented='false';root.dataset.sourceCurrencyPopulation='OnIsVisibleChanged -> User.Currencies.OrderBy(Category), then ListChanged()';
  const tree=control(root,'BindTree');if(tree){tree.dataset.sourceType='CurrencyTree';tree.dataset.sourceBorder='Constants.PrimaryColour';tree.dataset.sourceTreeList='runtime ClientUserCurrency by category';tree.dataset.sourceSelectedEntry='null'}
  const scroll=control(root,'CurrencyBindTreeScrollBar');if(scroll){scroll.dataset.sourceMaxValue='0';scroll.dataset.sourceVisibleSize='340';scroll.dataset.sourceChange='22';scroll.dataset.sourceCurrencyScroll='CurrencyTree TotalCount=0'}
}
function scan(node){if(!(node instanceof Element))return;if(node.id==='w-currency')queueMicrotask(()=>install(node));node.querySelectorAll?.('#w-currency').forEach(root=>queueMicrotask(()=>install(root)))}
new MutationObserver(records=>records.forEach(record=>record.addedNodes.forEach(scan))).observe(stage,{childList:true,subtree:true});
install(document.querySelector('#w-currency'));
console.info('ORIGINS Currency source runtime active: empty bordered CurrencyTree + source scrollbar; user currencies neutral');
