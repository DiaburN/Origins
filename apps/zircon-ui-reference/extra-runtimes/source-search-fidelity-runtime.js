// Source-backed local search behavior for windows whose result catalog is
// server/system-model data. Filters and enablement work locally; no RankInfo,
// InstanceInfo or ItemInfo result is fabricated by the reference viewer.
const stage=document.querySelector('#stage');
let spec=null;
function items(){return [...(spec?.windows||[]),...(spec?.nestedWindows||[])]}
function itemFor(root){if(!root?.id?.startsWith('w-'))return null;const id=root.id.slice(2);return items().find(item=>item.id===id)||null}
function indexByName(item,name){return (item?.controls||[]).findIndex(control=>control.name===name)}
function elementByName(root,item,name){const index=indexByName(item,name);return index>=0?root.querySelector(`[data-control-index="${index}"]`):null}
function setDynamicEnabled(element,value){if(!element)return;element.dataset.sourceDynamicEnabled=String(Boolean(value));element.dispatchEvent(new CustomEvent('origins:source-enabled-changed',{bubbles:true,detail:{enabled:Boolean(value)}}))}
function markPending(root,action,detail={}){root.dataset.pendingSourceAction=action;root.dataset.pendingSourceActionDetail=JSON.stringify(detail);root.dispatchEvent(new CustomEvent('origins:source-action-pending',{bubbles:true,detail:{action,...detail}}))}
function hideGeneratedRows(root,item,prefixes){for(let i=0;i<(item?.controls||[]).length;i++){const control=item.controls[i];if(!prefixes.some(prefix=>String(control.name||'').startsWith(prefix)))continue;if(!/Source\d{2}$/.test(String(control.name||'')))continue;const element=root.querySelector(`[data-control-index="${i}"]`);if(element)element.style.display='none'}}
function installRanking(root,item){
  if(root.dataset.sourceRankingSearchRuntime==='true')return;root.dataset.sourceRankingSearchRuntime='true';
  const input=elementByName(root,item,'SearchText');const button=elementByName(root,item,'SearchButton');
  setDynamicEnabled(button,Boolean((input?.textContent||'').trim()));
  input?.addEventListener('origins:source-text-changed',event=>{const text=String(event.detail?.text??input.textContent??'');setDynamicEnabled(button,Boolean(text.trim()));root.dataset.rankingSearchText=text});
  const submit=()=>{const text=String(input?.textContent||'').trim();if(!text)return;markPending(root,'C.RankSearch',{name:text});root.dataset.rankingRuntimeResults='not-fabricated'};
  input?.addEventListener('origins:source-text-enter',submit);button?.addEventListener('click',submit);
  const classBox=elementByName(root,item,'RequiredClassBox');const online=elementByName(root,item,'OnlineOnlyBox');
  classBox?.addEventListener('origins:source-combo-selected',()=>{root.dataset.rankingFilterChanged='true';root.dataset.rankingRuntimeResults='not-fabricated';hideGeneratedRows(root,item,['RankingLineSource'])});
  online?.addEventListener('change',()=>{root.dataset.rankingFilterChanged='true';root.dataset.rankingRuntimeResults='not-fabricated';hideGeneratedRows(root,item,['RankingLineSource'])});
}
function installDungeon(root,item){
  if(root.dataset.sourceDungeonSearchRuntime==='true')return;root.dataset.sourceDungeonSearchRuntime='true';root.dataset.dungeonRuntimeCatalog='Globals.InstanceInfoList.Binding required';
  const input=elementByName(root,item,'DungeonNameBox');const button=elementByName(root,item,'SearchButton');
  const submit=()=>{hideGeneratedRows(root,item,['DungeonRowSource']);root.dataset.dungeonSearchResultCount='0';root.dataset.dungeonRuntimeResults='not-fabricated';root.dataset.dungeonSelectedRow='none'};
  input?.addEventListener('origins:source-text-enter',submit);button?.addEventListener('click',submit);submit();
  const join=elementByName(root,item,'JoinButton');if(join){join.style.display='none';join.dataset.runtimeInstanceRequired='true'}
}
function installFortune(root,item){
  if(root.dataset.sourceFortuneSearchRuntime==='true')return;root.dataset.sourceFortuneSearchRuntime='true';root.dataset.fortuneRuntimeCatalog='Globals.ItemInfoList.Binding required';
  const input=elementByName(root,item,'ItemNameBox');const button=elementByName(root,item,'SearchButton');
  const submit=()=>{hideGeneratedRows(root,item,['FortuneRowSource']);root.dataset.fortuneSearchResultCount='0';root.dataset.fortuneRuntimeResults='not-fabricated'};
  input?.addEventListener('origins:source-text-enter',submit);button?.addEventListener('click',submit);submit();
}
function install(root){if(!(root instanceof Element)||!spec)return;const item=itemFor(root);if(!item)return;switch(item.field){case 'RankingBox':installRanking(root,item);break;case 'DungeonFinderBox':installDungeon(root,item);break;case 'FortuneCheckerBox':installFortune(root,item);break}}
function scan(node){if(!(node instanceof Element))return;if(node.matches?.('.window,.generic-window'))queueMicrotask(()=>install(node));node.querySelectorAll?.('.window,.generic-window').forEach(root=>queueMicrotask(()=>install(root)))}
new MutationObserver(records=>records.forEach(record=>record.addedNodes.forEach(scan))).observe(stage,{childList:true,subtree:true});
fetch('ui-source-spec.json',{cache:'no-store'}).then(response=>{if(!response.ok)throw new Error(`ui-source-spec.json ${response.status}`);return response.json()}).then(value=>{spec=value;stage.querySelectorAll('.window,.generic-window').forEach(install);console.info('ORIGINS source-neutral Ranking/Dungeon/Fortune search flows active; runtime result catalogs never fabricated')}).catch(error=>console.error('Unable to load source search manifest',error));
