// Exact direct MainPanel navigation from Zircon MainPanel.cs.  Capture phase is
// intentional: it replaces the older generic interaction listener for these
// controls so block-lambda actions (Character/Mail/CashShop) cannot double-toggle.
const stage=document.querySelector('#stage');
const catalog=document.querySelector('#window-list');

const ACTIONS={
  CharacterButton:[['close','inspect'],['toggle','character']],
  InventoryButton:[['toggle','inventory']],
  SpellButton:[['toggle','magic']],
  QuestButton:[['toggle','quest']],
  MailButton:[['toggle','communication']],
  BeltButton:[['toggle','belt']],
  GroupButton:[['toggle','group']],
  MenuButton:[['toggle','menu']],
  CashShopButton:[['toggle','game-store']],
};

function root(id){return stage.querySelector(`#w-${CSS.escape(id)}`)}
function open(id){
  const existing=root(id);if(existing)return existing;
  catalog?.querySelector(`[data-window-id="${CSS.escape(id)}"]`)?.click();
  return root(id);
}
function close(id){root(id)?.remove()}
function toggle(id){const existing=root(id);if(existing)existing.remove();else open(id)}
function apply(action,id){if(action==='open')open(id);else if(action==='close')close(id);else toggle(id)}

stage.addEventListener('click',event=>{
  if(!(event.target instanceof Element))return;
  const source=event.target.closest('#w-main-panel');if(!source)return;
  const control=event.target.closest('[data-control-name]');if(!control||!source.contains(control))return;
  const actions=ACTIONS[control.dataset.controlName];if(!actions)return;

  // Source MainPanel handlers are left-click UI actions. Prevent the older
  // generic interaction runtime from observing this exact click a second time.
  event.preventDefault();event.stopImmediatePropagation();
  for(const [action,target] of actions)apply(action,target);
  source.dataset.lastSourceNavigation=`${control.dataset.controlName}:${actions.map(([a,t])=>`${a}:${t}`).join(',')}`;
},true);

const expected=new Set(Object.keys(ACTIONS));
new MutationObserver(()=>{
  const main=root('main-panel');if(!main)return;
  const present=new Set([...main.querySelectorAll('[data-control-name]')].map(el=>el.dataset.controlName));
  main.dataset.sourceNavigationCoverage=String([...expected].filter(name=>present.has(name)).length);
}).observe(stage,{childList:true,subtree:true});
console.info('ORIGINS MainPanel source navigation active: 9 controls / 10 window actions');