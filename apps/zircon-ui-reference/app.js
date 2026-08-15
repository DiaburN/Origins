import { gameSceneWindows, uiCategories } from './game-scene-windows.js';

const stage = document.querySelector('#stage');
const list = document.querySelector('#window-list');
const filters = document.querySelector('#category-filters');
const search = document.querySelector('#window-search');
const sourceStatus = document.querySelector('#source-status');
const selectionInfo = document.querySelector('#selection-info');

const pad = i => String(i).padStart(5, '0');
const asset = (lib, i) => `assets/${lib}/${pad(i)}.png`;
const windows = new Map();
let sourceSpec = null;
let activeCategory = 'all';
let activeId = null;

function img(src, x, y, cls='ui-img', parent=stage) {
  const e = document.createElement('img');
  e.src = src;
  e.className = cls;
  e.style.left = `${x}px`;
  e.style.top = `${y}px`;
  e.draggable = false;
  parent.append(e);
  return e;
}
function label(text, x, y, w=0, parent=stage) {
  const e = document.createElement('div');
  e.className = 'runtime-label';
  e.textContent = text;
  e.style.left = `${x}px`;
  e.style.top = `${y}px`;
  if (w) { e.style.width = `${w}px`; e.style.textAlign = 'center'; }
  parent.append(e);
  return e;
}
function numberFrom(expr) {
  const m = String(expr ?? '').match(/\b(\d+)\b/);
  return m ? Number(m[1]) : null;
}
function libraryFrom(expr) {
  const m = String(expr ?? '').match(/LibraryFile\.([A-Za-z0-9_]+)/);
  return m ? m[1] : null;
}
function pairFrom(expr, type='Point') {
  const re = new RegExp(`new\\s+${type}\\s*\\(\\s*(-?\\d+)\\s*,\\s*(-?\\d+)\\s*\\)`);
  const m = String(expr ?? '').match(re);
  return m ? [Number(m[1]), Number(m[2])] : null;
}
function sourceText(expr, fallback='') {
  if (!expr) return fallback;
  const quoted = String(expr).match(/"([^"]+)"/);
  if (quoted) return quoted[1];
  const lang = String(expr).match(/CEnvir\.Language\.([A-Za-z0-9_]+)/);
  return lang ? lang[1].replace(/([a-z])([A-Z])/g, '$1 $2') : fallback;
}
function removeTransientWindows() {
  stage.querySelectorAll('.window,.generic-window').forEach(e => e.remove());
  windows.clear();
  activeId = null;
  document.querySelectorAll('.catalog-item.active').forEach(e => e.classList.remove('active'));
}

// ---------------------------------------------------------------------------
// Permanent Zircon desktop HUD
// ---------------------------------------------------------------------------
function buildDesktop() {
  stage.innerHTML = '';
  const mainY = 700;
  img(asset('GameInter', 50), 0, mainY);
  img(asset('GameInter', 51), 17, mainY + 3);
  for (const [i,x,y] of [[52,35,22],[54,35,36],[58,35,50],[70,277,25],[71,277,45],[72,362,25],[73,362,45],[66,445,25],[65,445,45],[63,531,25],[62,541,45]])
    img(asset('GameInter', i), x, mainY + y);

  const buttons = [
    [82,650,'character'],[87,689,'inventory'],[92,728,'magic'],[112,767,'quest'],
    [97,806,'communication'],[107,845,'belt'],[102,884,'group'],[117,923,'menu'],[122,972,'game-store']
  ];
  for (const [i,x,target] of buttons) {
    const b = img(asset('GameInter', i), x, mainY + (i === 122 ? 16 : 23), 'ui-button');
    b.addEventListener('click', () => openWindow(target));
  }
  label('Wizard',300,mainY+20,60); label('50',300,mainY+40,60);
  label('55/100',385,mainY+20,60); label('1250',385,mainY+40,60);
  label('8-12',470,mainY+20,60); label('14-22',470,mainY+40,60);
  label('10-14',567,mainY+20,60); label('28-45',567,mainY+40,60);
  label('830 / 1000',82,mainY+18,125); label('710 / 1000',82,mainY+32,125); label('55 / 100',82,mainY+46,125);

  const chat = document.createElement('div');
  chat.className = 'chat'; chat.style.left='0'; chat.style.top='432px'; chat.style.width='493px'; chat.style.height='150px';
  chat.innerHTML = 'Welcome to ORIGINS.<br><span style="color:#7fff7f">Zuma Temple</span><br>Zircon GameInter desktop reference';
  stage.append(chat);
  const system = document.createElement('div');
  system.className='chat'; system.style.right='0'; system.style.top='596px'; system.style.width='350px'; system.style.height='104px';
  system.innerHTML='System<br>GameScene UI reference'; stage.append(system);

  const mm=document.createElement('div'); mm.className='minimap';
  mm.innerHTML='<div class="minimap-title">Zuma Temple</div><div class="minimap-body">MiniMap runtime content</div>';
  stage.append(mm); mm.addEventListener('click',()=>openWindow('big-map'));

  const belt=document.createElement('div'); belt.className='belt'; belt.dataset.persist='true';
  for(let i=0;i<10;i++){ const s=document.createElement('div'); s.className='belt-slot'; s.textContent=(i+1)%10; belt.append(s); }
  stage.append(belt);
}

// ---------------------------------------------------------------------------
// Exact image-backed windows already validated against Zircon source
// ---------------------------------------------------------------------------
function addImageWindow(name, lib, index, x, y, title) {
  const root=document.createElement('div'); root.className='window'; root.id=`w-${name}`;
  root.style.left=`${x}px`; root.style.top=`${y}px`;
  const bg=img(asset(lib,index),0,0,'window-img',root);
  bg.addEventListener('load',()=>{ root.style.width=`${bg.naturalWidth}px`; root.style.height=`${bg.naturalHeight}px`; placeIfOffscreen(root); });
  const close=img(asset('Interface',15),0,0,'close',root); close.style.left='auto'; close.addEventListener('click',()=>root.remove());
  const t=document.createElement('div'); t.className='window-title'; t.textContent=title; root.append(t);
  stage.append(root); windows.set(name,root); return root;
}
function exactCharacter(item) {
  const root=addImageWindow(item.id,'Interface',item.id==='inspect'?115:110,0,0,item.id==='inspect'?'Inspect Character':'Character');
  label('ORIGINS',97,52,137,root); label('Wizard',97,70,137,root); return root;
}
function exactInventory(item) {
  const root=addImageWindow(item.id,'Interface',130,760,200,'Inventory');
  img(asset('GameInter',360),53,355,'ui-img',root); img(asset('GameInter',364),180,384,'ui-button',root); img(asset('GameInter',358),218,384,'ui-button',root);
  label('Gold',55,382,60,root); label('12,500',112,382,65,root); return root;
}
function exactMagic(item) {
  const root=addImageWindow(item.id,'Interface',161,605,110,'Magic'); img(asset('Interface',164),0,66,'ui-img',root);
  const icons=document.createElement('div'); icons.className='magic-icons';
  for(const i of [0,8,10,14,18,20,30,38,40,44,52,64]){const e=document.createElement('img');e.src=asset('MagicIcon',i);icons.append(e)}
  root.append(icons); return root;
}
function exactQuest(item) {
  const root=addImageWindow(item.id,'Interface',291,146,80,'Quests'); label('Current',24,55,80,root); label('Zuma Temple',25,85,150,root); label('Reach the King Room',25,103,180,root); return root;
}
function exactMenu(item) {
  const root=addImageWindow(item.id,'Interface',279,872,440,'Menu'); const mb=document.createElement('div'); mb.className='menu-buttons';
  for(const [text,target] of [['Settings','config'],['Help','help'],['Guild','guild'],['Storage','storage'],['Ranking','ranking'],['Companion','companion'],['Leave','exit']]){
    const e=document.createElement('div'); e.textContent=text; e.addEventListener('click',()=>openWindow(target)); mb.append(e);
  }
  root.append(mb); return root;
}

// ---------------------------------------------------------------------------
// Source-driven generic renderer for the remaining Zircon GameScene windows.
// It preserves unresolved C# expressions instead of guessing them.
// ---------------------------------------------------------------------------
function buildDxFrame(width,height,title) {
  const root=document.createElement('div'); root.className='generic-window'; root.style.width=`${width}px`; root.style.height=`${height}px`;
  const header=document.createElement('div'); header.className='generic-window-header'; header.textContent=title; root.append(header);
  // Zircon DXWindow draws these Interface pieces as reusable edges/corners.
  const pieces=[[0,0,0,'100%',null],[1,0,22,null,'calc(100% - 22px)'],[1,width-8,22,null,'calc(100% - 22px)'],[2,0,height-8,'100%',null],[11,0,0,null,null],[12,width-16,0,null,null],[8,0,height-16,null,null],[9,width-16,height-16,null,null]];
  for(const [idx,x,y,w,h] of pieces){const e=img(asset('Interface',idx),x,y,'ui-img',root);if(w)e.style.width=w;if(h)e.style.height=h;}
  const close=img(asset('Interface',15),width-24,3,'close',root); close.addEventListener('click',()=>root.remove());
  const body=document.createElement('div'); body.className='generic-window-body'; root.append(body); return {root,body};
}
function fallbackSize(item) {
  const root=item.root||{};
  return pairFrom(root.Size,'Size') || pairFrom(root.ClientSize,'Size') || [Math.min(520, item.category==='npc'?420:380), item.category==='hud'?180:300];
}
function controlPosition(p,index) { return pairFrom(p.Location,'Point') || [10 + (index%3)*95, 34 + Math.floor(index/3)*42]; }
function controlSize(p,type) {
  return pairFrom(p.Size,'Size') || pairFrom(p.GridSize,'Size')?.map((v,i)=>i===0?v*36:v*36) || (type==='DXButton'?[90,24]:type==='DXLabel'?[120,18]:[80,28]);
}
function renderControl(control,index,parent) {
  const p=control.properties||{}; const [x,y]=controlPosition(p,index); const [w,h]=controlSize(p,control.type);
  const lib=libraryFrom(p.LibraryFile); const idx=numberFrom(p.Index);
  if((control.type==='DXImageControl'||control.type==='DXButton'||control.type==='DXAnimatedControl') && lib && idx!==null){
    const e=img(asset(lib,idx),x,y,control.type==='DXButton'?'ui-button':'ui-img',parent);
    e.title=`${control.name}: ${control.type}`; return;
  }
  if(control.type==='DXItemGrid'){
    const gs=pairFrom(p.GridSize,'Size')||[4,4]; const grid=document.createElement('div'); grid.className='generic-control generic-grid';
    grid.style.left=`${x}px`;grid.style.top=`${y}px`;grid.style.width=`${gs[0]*36}px`;grid.style.height=`${gs[1]*36}px`;grid.style.gridTemplateColumns=`repeat(${gs[0]},35px)`;
    for(let n=0;n<gs[0]*gs[1];n++){const c=document.createElement('div');c.className='generic-cell';grid.append(c)} parent.append(grid); return;
  }
  const e=document.createElement('div'); e.className='generic-control'; e.style.left=`${x}px`;e.style.top=`${y}px`;e.style.width=`${w}px`;e.style.height=`${h}px`;
  if(control.type==='DXTab')e.classList.add('generic-tab');
  e.textContent=sourceText(p.Text,control.name||control.type); e.title=JSON.stringify(p); parent.append(e);
}
function genericWindow(item) {
  const rootLib=libraryFrom(item.root?.LibraryFile); const rootIndex=numberFrom(item.root?.Index);
  if(rootLib && rootIndex!==null){
    const root=addImageWindow(item.id,rootLib,rootIndex,250,120,item.sourceClass); const body=root;
    (item.controls||[]).forEach((c,i)=>renderControl(c,i,body)); return root;
  }
  const [w,h]=fallbackSize(item); const {root,body}=buildDxFrame(w,h,item.sourceClass); root.id=`w-${item.id}`;
  root.style.left=`${Math.max(0,(1024-w)/2)}px`; root.style.top=`${Math.max(0,(700-h)/2)}px`;
  (item.controls||[]).forEach((c,i)=>renderControl(c,i,body));
  const badge=document.createElement('div'); badge.className='generic-source-badge'; badge.textContent=item.sourcePath||'source class unresolved'; root.append(badge);
  stage.append(root); windows.set(item.id,root); return root;
}
function placeIfOffscreen(root){
  requestAnimationFrame(()=>{const w=root.offsetWidth||350,h=root.offsetHeight||300;let x=parseInt(root.style.left)||0,y=parseInt(root.style.top)||0;if(x+w>1024)x=Math.max(0,1024-w);if(y+h>700)y=Math.max(0,700-h);root.style.left=`${x}px`;root.style.top=`${y}px`;});
}

const exactRenderers={character:exactCharacter,inspect:exactCharacter,inventory:exactInventory,magic:exactMagic,quest:exactQuest,menu:exactMenu};

function itemById(id){return sourceSpec?.windows?.find(x=>x.id===id||x.field===gameSceneWindows.find(g=>g.id===id)?.field) || gameSceneWindows.find(x=>x.id===id);}
function openWindow(id){
  if(id==='main-panel'||id==='belt'||id==='minimap'||id==='buffs'||id==='group-health'||id==='timer'){
    selectionInfo.textContent=`${id}: persistent/default GameScene HUD component.`; return;
  }
  removeTransientWindows();
  const item=itemById(id); if(!item)return;
  const enriched={...gameSceneWindows.find(x=>x.field===item.field),...item,id};
  const renderer=exactRenderers[id]||genericWindow; renderer(enriched); activeId=id;
  document.querySelector(`[data-window-id="${id}"]`)?.classList.add('active');
  const source=enriched.sourcePath?` — ${enriched.sourcePath}`:'';
  selectionInfo.textContent=`${enriched.field} / ${enriched.sourceClass||enriched.class}${source}`;
}

function mergeSpec(raw){
  const byField=new Map((raw.windows||[]).map(w=>[w.field,w]));
  return gameSceneWindows.map(base=>({...base,...(byField.get(base.field)||{}),id:base.id,sourceClass:(byField.get(base.field)||{}).class||base.sourceClass}));
}
async function loadSpec(){
  try{
    const r=await fetch('ui-source-spec.json',{cache:'no-store'}); if(!r.ok)throw new Error(r.statusText); const raw=await r.json();
    sourceSpec={...raw,windows:mergeSpec(raw)}; sourceStatus.textContent=`${raw.windowCount||sourceSpec.windows.length} GameScene entries parsed from current Zircon source`;
  }catch(err){
    sourceSpec={windows:gameSceneWindows}; sourceStatus.textContent=`static GameScene registry (${gameSceneWindows.length} entries); generated source spec not present in this checkout`;
  }
  renderCatalog();
}
function renderCatalog(){
  list.innerHTML=''; const q=search.value.trim().toLowerCase();
  const items=(sourceSpec?.windows||gameSceneWindows).filter(x=>(activeCategory==='all'||x.category===activeCategory)&&(!q||`${x.id} ${x.field} ${x.sourceClass||x.class}`.toLowerCase().includes(q)));
  for(const category of uiCategories){
    const groupItems=items.filter(x=>x.category===category); if(!groupItems.length)continue;
    const group=document.createElement('div'); group.className='catalog-group'; const head=document.createElement('div');head.className='catalog-group-title';head.textContent=`${category} (${groupItems.length})`;group.append(head);
    for(const item of groupItems){const b=document.createElement('button');b.className='catalog-item';b.dataset.windowId=item.id;b.innerHTML=`${item.id}<small>${item.field} · ${item.sourceClass||item.class}</small>`;b.addEventListener('click',()=>openWindow(item.id));group.append(b)}
    list.append(group);
  }
}
function buildFilters(){
  for(const c of ['all',...uiCategories]){const b=document.createElement('button');b.textContent=c;b.dataset.category=c;if(c==='all')b.classList.add('active');b.addEventListener('click',()=>{activeCategory=c;filters.querySelectorAll('button').forEach(x=>x.classList.toggle('active',x===b));renderCatalog()});filters.append(b)}
}

document.querySelector('[data-close-all]').addEventListener('click',()=>{removeTransientWindows();selectionInfo.textContent='All transient Zircon windows closed.'});
document.querySelector('#reset-layout').addEventListener('click',()=>{buildDesktop();selectionInfo.textContent='Zircon desktop reset.'});
search.addEventListener('input',renderCatalog);

buildFilters(); buildDesktop(); loadSpec();
