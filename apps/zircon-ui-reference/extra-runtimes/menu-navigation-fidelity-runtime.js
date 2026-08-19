// Exact direct window navigation already encoded in Zircon MenuDialog and
// MiniMapDialog. Capture-phase replacement prevents duplicate toggles from the
// older generic interaction projection.
const stage=document.querySelector('#stage');
const catalog=document.querySelector('#window-list');
const MENU={
  SettingsButton:['toggle','settings'],
  HelpButton:['toggle','help'],
  GuildButton:['toggle','guild'],
  StorageButton:['toggle','storage'],
  RankingButton:['toggle','ranking'],
  CompanionButton:['toggle','companion'],
  LeaveButton:['open','exit'],
};
function root(id){return stage.querySelector(`#w-${CSS.escape(id)}`)}
function open(id){const current=root(id);if(current)return current;catalog?.querySelector(`[data-window-id="${CSS.escape(id)}"]`)?.click();return root(id)}
function close(id){root(id)?.remove()}
function execute(action,id){if(action==='open')open(id);else{const current=root(id);if(current)current.remove();else open(id)}}
function sourceControl(event,windowId){if(!(event.target instanceof Element))return null;const window=event.target.closest(`#w-${CSS.escape(windowId)}`);if(!window)return null;const control=event.target.closest('[data-control-name]');return control&&window.contains(control)?{window,control}:null}

stage.addEventListener('click',event=>{
  const menu=sourceControl(event,'menu');
  if(menu){const contract=MENU[menu.control.dataset.controlName];if(contract){event.preventDefault();event.stopImmediatePropagation();execute(contract[0],contract[1]);menu.window.dataset.lastSourceNavigation=`${menu.control.dataset.controlName}:${contract.join(':')}`;return}}
  const mini=sourceControl(event,'minimap');
  if(mini?.control.dataset.controlName==='BigMapButton'){
    event.preventDefault();event.stopImmediatePropagation();execute('toggle','big-map');mini.window.dataset.lastSourceNavigation='BigMapButton:toggle:big-map';
  }
},true);
console.info('ORIGINS Menu 7-control + MiniMap BigMap source navigation active');