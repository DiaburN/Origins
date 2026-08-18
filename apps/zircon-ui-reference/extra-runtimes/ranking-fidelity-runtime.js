// Source-faithful RankingDialog neutral state for the compact GameScene variant.
// Ranking rows, online/observable flags, selected-rank inspect equipment and
// search results are runtime/server data and are never fabricated.
const stage=document.querySelector('#stage');
function control(root,name){return root?.querySelector?.(`[data-control-name="${CSS.escape(name)}"]`)||null}
function setEnabled(element,value){if(!element)return;element.dataset.sourceDynamicEnabled=String(Boolean(value));element.dispatchEvent(new CustomEvent('origins:source-enabled-changed',{bubbles:true}))}
function blank(element,reason){if(!element)return;element.textContent='';element.dataset.sourceRuntimeText=reason}
function install(root){
  if(!root||root.id!=='w-ranking'||root.dataset.sourceRankingRuntime==='true')return;
  root.dataset.sourceRankingRuntime='true';root.dataset.sourceRankingVariant='compact fullRanking=false';root.dataset.sourceRankingIndex='Interface#210';root.dataset.sourceRankingSize='330x456';
  root.dataset.sourceSelectedRank='null';root.dataset.sourceSelectedStartIndex='-1';root.dataset.sourceStartIndex='0';root.dataset.sourceOnlineOnly='false';root.dataset.sourceRanksInvented='false';root.dataset.sourceRankingInspectInvented='false';
  setEnabled(control(root,'ObserveButton'),false);
  blank(control(root,'LastUpdate'),'runtime ranking refresh time');
  const search=control(root,'SearchText');if(search){search.contentEditable='true';search.spellcheck=false;search.dataset.sourceSearchResults='runtime RankSearch response';search.dataset.sourceSearchResultsInvented='false'}
  const searchButton=control(root,'SearchButton');searchButton?.addEventListener('click',event=>{event.preventDefault();event.stopImmediatePropagation();root.dataset.sourceRankSearchAction='runtime ranking search request';root.dataset.sourceRankSearchActionExecuted='false'},true);
  const scroll=control(root,'ScrollBar');if(scroll){scroll.dataset.sourceRankingMax='runtime ranking count';scroll.dataset.sourceRankingValue='0'}
  for(const cell of root.querySelectorAll('[data-control-type="DXItemCell"]')){cell.dataset.sourceItem='runtime selected ranking inspect equipment';cell.dataset.sourceItemInvented='false'}
  for(const element of root.querySelectorAll('[data-control-name]')){
    const name=String(element.dataset.controlName||'');
    if(/CharacterNameLabel$|GuildNameLabel$|GuildRankLabel$/.test(name))blank(element,'runtime SelectedRank/inspect payload');
  }
}
function scan(node){if(!(node instanceof Element))return;if(node.id==='w-ranking')queueMicrotask(()=>install(node));node.querySelectorAll?.('#w-ranking').forEach(root=>queueMicrotask(()=>install(root)))}
new MutationObserver(records=>records.forEach(record=>record.addedNodes.forEach(scan))).observe(stage,{childList:true,subtree:true});
install(document.querySelector('#w-ranking'));
console.info('ORIGINS Ranking source runtime active: compact #210/330x456; rank/search/inspect data neutral');
