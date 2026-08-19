// Source-faithful CharacterDialog neutral state for CharacterBox and InspectBox.
// Character identity, equipment, fame, guild, partner, discipline/hermit system
// data and player preview layers are runtime-only and are never fabricated.
const stage=document.querySelector('#stage');
function control(root,name){return root?.querySelector?.(`[data-control-name="${CSS.escape(name)}"]`)||null}
function setVisible(element,visible){if(!element)return;element.hidden=!visible;element.dataset.sourceDynamicVisible=String(visible);element.querySelectorAll?.('.dx-tab-button').forEach(button=>button.hidden=!visible)}
function blank(element,reason){if(!element)return;element.textContent='';element.dataset.sourceRuntimeText=reason}
function install(root){
  if(!root||!['w-character','w-inspect'].includes(root.id)||root.dataset.sourceCharacterRuntime==='true')return;
  const inspect=root.id==='w-inspect';root.dataset.sourceCharacterRuntime='true';root.dataset.sourceInspect=String(inspect);root.dataset.sourceRootIndex=inspect?'Interface#115':'Interface#110';
  root.dataset.sourceCharacterIdentity='runtime player/inspect packet';root.dataset.sourceEquipment='runtime equipment array';root.dataset.sourceCharacterPreview='runtime gender/class/hair/equipment/guild layers';root.dataset.sourceFame='runtime';root.dataset.sourceGuild='runtime';root.dataset.sourceMarriage='runtime';root.dataset.sourcePlayerDataInvented='false';

  for(const name of ['CharacterNameLabel','GuildNameLabel','GuildRankLabel','MarriageLabel'])blank(control(root,name),inspect?'S.Inspect payload':'MapObject.User/GameScene GuildInfo');
  setVisible(control(root,'MarriageIcon'),false);setVisible(control(root,'MarriageLabel'),false);

  // CharacterTab is selected in the constructor. Discipline needs loaded
  // Globals.DisciplineInfoList and Hermit needs GameScene.Game.HermitEnabled.
  // Inspect hides both unconditionally. Standalone reference has neither runtime
  // system-model binding nor user Hermit state, so both stay source-neutral hidden.
  setVisible(control(root,'CharacterTab'),true);setVisible(control(root,'DisciplineTab'),false);setVisible(control(root,'HermitTab'),false);
  root.dataset.sourceSelectedPrimaryTab='CharacterTab';
  root.dataset.sourceDisciplineVisibility=inspect?'false (Inspect)':'!Inspect && Globals.DisciplineInfoList.Binding.Count > 0 (runtime)';
  root.dataset.sourceHermitVisibility=inspect?'false (Inspect)':'!Inspect && GameScene.Game.HermitEnabled (runtime)';

  // Do not blank stat labels: Zircon itself initializes many of them to 0/0-0
  // before UpdateStats() replaces them with real player stats.
  root.dataset.sourceStatDisplay='constructor zeros preserved; UpdateStats runtime';

  // Equipment cells are source geometry/chrome only; item payloads are runtime.
  root.querySelectorAll('[data-control-type="DXItemCell"]').forEach(cell=>{cell.dataset.sourceItem='runtime equipment';cell.dataset.sourceItemInvented='false'});
  const fame=control(root,'FameControl');if(fame){fame.dataset.sourceMouseFame='Globals.FameInfoList lookup by runtime Fame';fame.dataset.sourceFameInvented='false'}

  if(!inspect){
    // OnIsVisibleChanged only opens FishingBox when a real equipped weapon has
    // ItemEffect.FishingRod. Neutral equipment is empty, so force it closed.
    document.querySelector('#w-fishing')?.remove();root.dataset.sourceFishingVisibility='HasFishingRod && IsVisible => false in neutral reference';
  }
  else root.dataset.sourceInspectPopulation='S.Inspect.NewInformation only; neutral reference has no inspect packet';
}
function scan(node){if(!(node instanceof Element))return;if(['w-character','w-inspect'].includes(node.id))queueMicrotask(()=>install(node));node.querySelectorAll?.('#w-character,#w-inspect').forEach(root=>queueMicrotask(()=>install(root)))}
new MutationObserver(records=>records.forEach(record=>record.addedNodes.forEach(scan))).observe(stage,{childList:true,subtree:true});
install(document.querySelector('#w-character'));install(document.querySelector('#w-inspect'));
console.info('ORIGINS Character/Inspect source runtime active: CharacterTab neutral, runtime identity/equipment/preview not fabricated');
