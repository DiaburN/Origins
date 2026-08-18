// Runtime-boundary fidelity for secondary source windows whose meaningful rows
// depend on live/system-model data rather than constructor literals.
const stage=document.querySelector('#stage');
const POLICIES={
  'guild-member':{data:'runtime selected guild-member/member-rank/guild state',items:'runtime guild/member payload'},
  'help':{data:'runtime HelpInfo/system-model content',items:'runtime help tree/page payload'},
};
function install(root){
  if(!root?.id?.startsWith('w-')||root.dataset.sourceSecondaryBoundary==='true')return;const policy=POLICIES[root.id.slice(2)];if(!policy)return;root.dataset.sourceSecondaryBoundary='true';root.dataset.sourceRuntimeData=policy.data;root.dataset.sourceRuntimeDataInvented='false';
  root.querySelectorAll('[data-control-type="DXItemCell"],[data-control-type="DXItemGrid"],[data-control-type="DXTreeControl"]').forEach(el=>{el.dataset.sourceRuntimePayload=policy.items;el.dataset.sourceRuntimePayloadInvented='false'});
  for(const button of root.querySelectorAll('[data-control-type="DXButton"]')){if(/CloseButton$|CancelButton$/.test(String(button.dataset.controlName||'')))continue;button.dataset.sourceSecondaryAction='requires live/system-model data';button.dataset.sourceSecondaryActionExecuted='false'}
}
function scan(node){if(!(node instanceof Element))return;if(node.id?.startsWith('w-'))queueMicrotask(()=>install(node));node.querySelectorAll?.('[id^="w-"]').forEach(root=>queueMicrotask(()=>install(root)))}
new MutationObserver(records=>records.forEach(record=>record.addedNodes.forEach(scan))).observe(stage,{childList:true,subtree:true});
stage.querySelectorAll('[id^="w-"]').forEach(install);
console.info('ORIGINS secondary runtime boundaries active: GuildMember + Help');
