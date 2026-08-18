// Source-faithful DungeonFinderDialog runtime boundary. Filter controls retain
// their generic source behavior, while dungeon rows, selected dungeon/group and
// packet-driven actions remain neutral until real runtime data exists.
const stage=document.querySelector('#stage');
function install(root){
  if(!root||root.id!=='w-dungeon-finder'||root.dataset.sourceDungeonFinderRuntime==='true')return;
  root.dataset.sourceDungeonFinderRuntime='true';root.dataset.sourceDungeonData='runtime/server';root.dataset.sourceDungeonDataInvented='false';root.dataset.sourceDungeonSelection='null';root.dataset.sourceDungeonGroup='runtime';root.dataset.sourceDungeonRequirements='runtime';
  root.querySelectorAll('[data-control-type="DXItemCell"],[data-control-type="DXItemGrid"]').forEach(el=>{el.dataset.sourceItem='runtime dungeon/reward/group data';el.dataset.sourceItemInvented='false'});
  root.querySelectorAll('[data-control-type="DXComboBox"],[data-control-type="DXCheckBox"],[data-control-type="DXTextBox"]').forEach(el=>{el.dataset.sourceDungeonFilter='local source control; results require runtime dungeon data'});
  for(const button of root.querySelectorAll('[data-control-type="DXButton"]')){
    const name=String(button.dataset.controlName||'');if(/CloseButton$|CancelButton$/.test(name))continue;
    if(button.dataset.sourceDungeonActionBound==='true')continue;button.dataset.sourceDungeonActionBound='true';
    button.addEventListener('click',()=>queueMicrotask(()=>{root.dataset.sourceLastDungeonAction=name;root.dataset.sourceDungeonAction='source handler requires live DungeonInfo/group/server state';root.dataset.sourceDungeonActionExecuted='false'}));
  }
}
function scan(node){if(!(node instanceof Element))return;if(node.id==='w-dungeon-finder')queueMicrotask(()=>install(node));node.querySelectorAll?.('#w-dungeon-finder').forEach(root=>queueMicrotask(()=>install(root)))}
new MutationObserver(records=>records.forEach(record=>record.addedNodes.forEach(scan))).observe(stage,{childList:true,subtree:true});
install(document.querySelector('#w-dungeon-finder'));
console.info('ORIGINS DungeonFinder source runtime active: filters local; dungeon/group/server data neutral');
