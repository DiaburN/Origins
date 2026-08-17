import { gameSceneWindows } from '../game-scene-windows.js';

// Replace the old handcrafted desktop placeholders with the actual source-
// reconstructed GameScene controls that are visible immediately after GameScene
// construction. No player/map/chat/item values are invented here.
const stage=document.querySelector('#stage');
const list=document.querySelector('#window-list');
const info=document.querySelector('#selection-info');
const DEFAULT_VISIBLE=gameSceneWindows.filter(item=>item.defaultVisible).map(item=>item.id);
let initialized=false;

function removeHandcraftedDesktop(){
  // buildDesktop() predates the source renderer. Its direct stage children are
  // samples only; real source windows are always wrapped in .window/.generic-window.
  stage.querySelectorAll(':scope > img,:scope > .runtime-label,:scope > .chat,:scope > .minimap,:scope > .belt').forEach(element=>element.remove());
  stage.dataset.desktopComposition='GameScene source windows only';
}
function root(id){return stage.querySelector(`#w-${CSS.escape(id)}`)}
function clickSourceWindow(id){
  if(root(id))return true;
  const button=list?.querySelector(`[data-window-id="${CSS.escape(id)}"]`);
  if(!button)return false;
  button.click();return Boolean(root(id));
}
function px(element,name){return Number.parseFloat(element?.style?.[name]||'0')||0}
function placeDefaults(){
  const main=root('main-panel');
  if(main){main.style.left=`${Math.round((1024-main.offsetWidth)/2)}px`;main.style.top=`${Math.round(768-main.offsetHeight)}px`;main.dataset.sourceDefaultLocation='((Game.Width-Main.Width)/2, Game.Height-Main.Height)'}
  const belt=root('belt');
  if(main&&belt){belt.style.left=`${Math.round(px(main,'left')+main.offsetWidth-belt.offsetWidth)}px`;belt.style.top=`${Math.round(px(main,'top')-belt.offsetHeight)}px`;belt.dataset.sourceDefaultLocation='MainPanel.Right-Belt.Width, MainPanel.Top-Belt.Height'}
  const mini=root('minimap');
  if(mini){mini.style.left=`${Math.round(1024-mini.offsetWidth)}px`;mini.style.top='0px';mini.dataset.sourceDefaultLocation='Game.Width-MiniMap.Width,0'}
  const buffs=root('buffs');
  if(mini&&buffs){buffs.style.left=`${Math.round(1024-mini.offsetWidth-buffs.offsetWidth-5)}px`;buffs.style.top='0px';buffs.dataset.sourceDefaultLocation='Game.Width-MiniMap.Width-Buff.Width-5,0'}
}
function initialize(){
  if(initialized)return;
  removeHandcraftedDesktop();
  if(!DEFAULT_VISIBLE.every(id=>list?.querySelector(`[data-window-id="${CSS.escape(id)}"]`)))return;
  initialized=true;
  for(const id of DEFAULT_VISIBLE)clickSourceWindow(id);
  requestAnimationFrame(()=>{placeDefaults();info.textContent='Zircon GameScene source-default HUD loaded; runtime player/map/item data remains neutral.'});
  stage.dataset.sourceDefaultHud=DEFAULT_VISIBLE.join(',');
  console.info('ORIGINS source-default HUD:',DEFAULT_VISIBLE.join(', '));
}

const observer=new MutationObserver(()=>initialize());
observer.observe(document.body,{childList:true,subtree:true});
initialize();
document.querySelector('#reset-layout')?.addEventListener('click',()=>{initialized=false;queueMicrotask(initialize)});