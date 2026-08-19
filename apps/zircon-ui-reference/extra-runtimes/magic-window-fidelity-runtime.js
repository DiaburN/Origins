// Source-faithful MagicDialog runtime boundary. Zircon defines dynamic school/tab
// templates, but actual visible schools, learned MagicInfo rows, levels/cooldowns
// and spell assignment are player-runtime data. The reference never fabricates a
// spell list or assumes a school is visible.
const stage=document.querySelector('#stage');
function install(root){
  if(!root||root.id!=='w-magic'||root.dataset.sourceMagicRuntime==='true')return;
  root.dataset.sourceMagicRuntime='true';root.dataset.sourceMagicSchools='16 source templates; visible schools runtime-only';root.dataset.sourceVisibleMagicSchools='0 neutral';root.dataset.sourcePlayerMagic='runtime GameScene/User magic collection';root.dataset.sourcePlayerMagicInvented='false';root.dataset.sourceMagicLevelsInvented='false';root.dataset.sourceMagicCooldownsInvented='false';
  root.querySelectorAll('[data-control-type="DXItemCell"],[data-control-type="DXItemGrid"]').forEach(element=>{element.dataset.sourceMagicItem='runtime MagicInfo/learned spell';element.dataset.sourceMagicItemInvented='false'});
  for(const element of root.querySelectorAll('[data-control-type="DXTab"],[data-control-type="DXConfigTab"]')){
    if(element.dataset.sourceRuntimeMagicTemplate==='true'||/MagicSchool|School/i.test(String(element.dataset.controlName||''))){element.hidden=true;element.dataset.sourceMagicTemplateVisible='false until real player magic data'}
  }
}
function installBar(root){if(!root||root.id!=='w-magic-bar'||root.dataset.sourceMagicBarNeutralRuntime==='true')return;root.dataset.sourceMagicBarNeutralRuntime='true';root.dataset.sourceMagicBarSlots='24 deterministic source slots';root.dataset.sourceMagicBarAssignedSpells='0 neutral';root.dataset.sourceMagicBarSpellDataInvented='false';root.querySelectorAll('[data-control-type="DXItemCell"]').forEach(cell=>{cell.dataset.sourceSpell='runtime spell assignment';cell.dataset.sourceSpellInvented='false'})}
function scan(node){if(!(node instanceof Element))return;if(node.id==='w-magic')queueMicrotask(()=>install(node));if(node.id==='w-magic-bar')queueMicrotask(()=>installBar(node));node.querySelectorAll?.('#w-magic').forEach(root=>queueMicrotask(()=>install(root)));node.querySelectorAll?.('#w-magic-bar').forEach(root=>queueMicrotask(()=>installBar(root)))}
new MutationObserver(records=>records.forEach(record=>record.addedNodes.forEach(scan))).observe(stage,{childList:true,subtree:true});
install(document.querySelector('#w-magic'));installBar(document.querySelector('#w-magic-bar'));
console.info('ORIGINS Magic source runtime active: 16 school templates/24 bar slots, no fabricated player spells');
