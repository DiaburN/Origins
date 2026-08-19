// Source-faithful Quest/QuestTracker neutral state. Quest lists, rewards, tasks,
// NPC destinations and tracker lines are runtime data and are never fabricated.
const stage=document.querySelector('#stage');
function bySuffix(root,suffix){return [...(root?.querySelectorAll?.('[data-control-name]')||[])].find(el=>String(el.dataset.controlName||'').endsWith(suffix))||null}
function allSuffix(root,suffix){return [...(root?.querySelectorAll?.('[data-control-name]')||[])].filter(el=>String(el.dataset.controlName||'').endsWith(suffix))}
function checked(box){const image=box?.querySelector?.(':scope > img');return Boolean(image&&/GameInter\/00162\.png$/.test(image.src))}
function installQuest(root){
  if(!root||root.id!=='w-quest'||root.dataset.sourceQuestRuntime==='true')return;root.dataset.sourceQuestRuntime='true';root.dataset.sourceQuestData='runtime Globals.QuestInfoList + GameScene.Game.QuestLog';root.dataset.sourceQuestDataInvented='false';root.dataset.configQuestTrackerVisible='true';
  const current=bySuffix(root,'CurrentTab__ShowTrackerBox')||allSuffix(root,'ShowTrackerBox').find(el=>!el.hidden);
  if(current){current.dataset.sourceQuestTrackerControl='CurrentTab.ShowTrackerBox';current.dataset.sourceChecked='true';current.addEventListener('click',()=>queueMicrotask(()=>{
    const value=checked(current);root.dataset.configQuestTrackerVisible=String(value);root.dataset.sourceQuestTrackerPopulate='GameScene.Game.QuestTrackerBox.PopulateQuests()';root.dataset.sourceQuestTrackerLines='0 in neutral reference';
    // With no real tracked CurrentTab quests, PopulateQuests always leaves tracker hidden.
    document.querySelector('#w-quest-tracker')?.remove();
  }))}
  for(const box of allSuffix(root,'ShowTrackerBox')){
    if(box===current)continue;box.dataset.sourceQuestTrackerControl='source-hidden on Available/Completed';
  }
  const abandon=bySuffix(root,'AbandonButton');if(abandon){abandon.dataset.sourceDynamicEnabled='false';abandon.setAttribute('aria-disabled','true');abandon.dataset.sourceQuestRequirement='SelectedQuest runtime';abandon.dispatchEvent(new CustomEvent('origins:source-enabled-changed',{bubbles:true}))}
  for(const name of ['StartLabel','EndLabel']){
    const element=bySuffix(root,name);element?.addEventListener('click',event=>{event.preventDefault();event.stopImmediatePropagation();root.dataset.sourceQuestMapLocator=`${name} requires SelectedQuest QuestInfo/NPC runtime`;root.dataset.sourceQuestMapLocatorExecuted='false'},true);
  }
}
function installTracker(root){
  if(!root||root.id!=='w-quest-tracker'||root.dataset.sourceQuestTrackerRuntime==='true')return;root.dataset.sourceQuestTrackerRuntime='true';root.dataset.sourceQuestTrackerLines='runtime tracked CurrentTab quests';root.dataset.sourceQuestTrackerLinesInvented='false';root.dataset.sourceQuestTrackerNeutralVisible='false';root.dataset.sourceQuestIconContract='QuestIcon animated frames depend on runtime QuestType/completion';
}
function scan(node){if(!(node instanceof Element))return;if(node.id==='w-quest')queueMicrotask(()=>installQuest(node));if(node.id==='w-quest-tracker')queueMicrotask(()=>installTracker(node));node.querySelectorAll?.('#w-quest').forEach(root=>queueMicrotask(()=>installQuest(root)));node.querySelectorAll?.('#w-quest-tracker').forEach(root=>queueMicrotask(()=>installTracker(root)))}
new MutationObserver(records=>records.forEach(record=>record.addedNodes.forEach(scan))).observe(stage,{childList:true,subtree:true});
installQuest(document.querySelector('#w-quest'));installTracker(document.querySelector('#w-quest-tracker'));
console.info('ORIGINS Quest source runtime active: tracker config local, quest/task/NPC data neutral');
