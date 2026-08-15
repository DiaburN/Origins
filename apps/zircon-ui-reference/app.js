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
function boolFrom(expr, fallback=false) {
  const value = String(expr ?? '').trim().toLowerCase();
  if (value === 'true') return true;
  if (value === 'false') return false;
  return fallback;
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
function buttonTypeFrom(expr, fallback='Default') {
  const m = String(expr ?? '').match(/ButtonType\.([A-Za-z0-9_]+)/);
  return m ? m[1] : fallback;
}
function cssColour(expr, fallback='#000') {
  const s=String(expr??'');
  if (/Color\.Black\b/.test(s)) return '#000';
  if (/Color\.White\b/.test(s)) return '#fff';
  const m=s.match(/Color\.FromArgb\(\s*(?:\d+\s*,\s*)?(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)/);
  return m?`rgb(${m[1]},${m[2]},${m[3]})`:fallback;
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
// Zircon reusable-control renderer
// ---------------------------------------------------------------------------
const buttonParts = {
  Default:[16,18,17], SelectedTab:[56,58,57], DeselectedTab:[53,55,54], SmallButton:[41,43,42],
};
const singleButtonPart = {AddButton:241,RemoveButton:242,LFGButton:243,OptionsButton:245};

function renderGeneratedButton(text,x,y,w,h,type,parent) {
  const root=document.createElement('div'); root.className=`dx-generated-button dx-button-${type}`;
  root.style.left=`${x}px`;root.style.top=`${y}px`;root.style.width=`${w}px`;root.style.height=`${h}px`;parent.append(root);
  if(singleButtonPart[type]!==undefined){
    const e=img(asset('Interface',singleButtonPart[type]),0,0,'ui-img',root);
    e.addEventListener('load',()=>{root.style.width=`${e.naturalWidth}px`;root.style.height=`${e.naturalHeight}px`});
  } else {
    const [li,mi,ri]=buttonParts[type]||buttonParts.Default;
    const left=img(asset('Interface',li),0,0,'ui-img',root);
    const middle=img(asset('Interface',mi),0,0,'ui-img dx-button-middle',root);
    const right=img(asset('Interface',ri),0,0,'ui-img',root);
    const layout=()=>{
      const lw=left.naturalWidth||6,rw=right.naturalWidth||6;
      right.style.left=`${Math.max(0,w-rw)}px`;
      middle.style.left=`${lw}px`;middle.style.width=`${Math.max(0,w-lw-rw)}px`;
      middle.style.height=`${Math.max(left.naturalHeight||h,right.naturalHeight||h)}px`;
    };
    left.addEventListener('load',layout);middle.addEventListener('load',layout);right.addEventListener('load',layout);layout();
  }
  if(text){const t=document.createElement('div');t.className='dx-button-label';t.textContent=text;root.append(t)}
  return root;
}
function renderCheckBox(control,x,y,parent){
  const p=control.properties||{},text=sourceText(p.Label||p.Text,control.name),checked=boolFrom(p.Checked,false);
  const root=document.createElement('div');root.className='dx-checkbox';root.style.left=`${x}px`;root.style.top=`${y}px`;parent.append(root);
  const t=document.createElement('span');t.textContent=text;root.append(t);
  const box=document.createElement('img');box.src=asset('GameInter',checked?162:161);box.draggable=false;root.append(box);
  root.addEventListener('click',()=>{const on=box.src.endsWith('/00162.png');box.src=asset('GameInter',on?161:162)});return root;
}
function renderScrollBar(control,x,y,w,h,parent,skin={}){
  const vertical=skin.vertical??(control.type==='DXVScrollBar');
  const up=skin.up??44,down=skin.down??46,thumb=skin.thumb??45,bg=skin.background??null;
  const root=document.createElement('div');root.className=`dx-scrollbar ${vertical?'vertical':'horizontal'}`;
  root.style.left=`${x}px`;root.style.top=`${y}px`;root.style.width=`${w}px`;root.style.height=`${h}px`;parent.append(root);
  if(bg!==null){const b=img(asset('Interface',bg),1,0,'ui-img dx-scroll-bg',root);if(vertical)b.style.height='100%';else b.style.width='100%'}
  if(vertical){img(asset('Interface',up),1,1,'ui-img',root);img(asset('Interface',down),1,Math.max(1,h-13),'ui-img',root);img(asset('Interface',thumb),1,16,'ui-img dx-scroll-thumb',root)}
  else{img(asset('Interface',up),1,1,'ui-img',root);img(asset('Interface',down),Math.max(1,w-13),1,'ui-img',root);img(asset('Interface',thumb),16,1,'ui-img dx-scroll-thumb',root)}
  return root;
}
function renderTextBox(control,x,y,w,h,parent){
  const p=control.properties||{},e=document.createElement('div');e.className='dx-textbox';e.style.left=`${x}px`;e.style.top=`${y}px`;e.style.width=`${w}px`;e.style.height=`${h}px`;
  e.textContent=sourceText(p.Text,'');parent.append(e);return e;
}
function renderNumberBox(control,x,y,parent){
  const root=document.createElement('div');root.className='dx-numberbox';root.style.left=`${x}px`;root.style.top=`${y}px`;root.style.width='90px';root.style.height='20px';parent.append(root);
  img(asset('GameInter',1011),0,1,'ui-button',root);
  const field=document.createElement('div');field.className='dx-textbox';field.style.left='19px';field.style.top='1px';field.style.width='50px';field.style.height='20px';field.textContent='0';root.append(field);
  img(asset('GameInter',1010),73,1,'ui-button',root);return root;
}
function renderTab(control,ctx,parent){
  const p=control.properties||{},text=sourceText(p.TabButton||p.Label||p.Text,control.name.replace(/Tab$/,''));
  const width=Math.max(60,numberFrom(p.MinimumTabWidth)||60),x=ctx.tabX,type=ctx.tabCount===0?'SelectedTab':'DeselectedTab';
  const button=renderGeneratedButton(text,x,0,width,22,type,parent);button.classList.add('dx-tab-button');ctx.tabX+=width+1;ctx.tabCount+=1;return button;
}
function renderItemCell(control,x,y,parent){
  const e=document.createElement('div');e.className='dx-item-cell';e.style.left=`${x}px`;e.style.top=`${y}px`;e.title=control.name;parent.append(e);return e;
}
function renderStructuralControl(control,x,y,w,h,parent){
  const p=control.properties||{};
  const shouldDraw=boolFrom(p.DrawTexture,false)||boolFrom(p.Border,false)||p.BackColour!==undefined;
  if(!shouldDraw)return null;
  const e=document.createElement('div');e.className='dx-structural-control';e.style.left=`${x}px`;e.style.top=`${y}px`;e.style.width=`${w}px`;e.style.height=`${h}px`;e.style.background=cssColour(p.BackColour,'transparent');
  if(boolFrom(p.Border,false))e.classList.add('with-border');parent.append(e);return e;
}
function renderComboBox(control,x,y,w,parent){
  const p=control.properties||{},root=document.createElement('div');root.className='dx-combobox';root.style.left=`${x}px`;root.style.top=`${y}px`;root.style.width=`${Math.max(w,70)}px`;root.style.height='16px';parent.append(root);
  const text=document.createElement('span');text.textContent=sourceText(p.SelectedLabel||p.Text,'');root.append(text);
  const arrow=img(asset('GameInter',795),0,0,'ui-button',root);arrow.style.right='0';arrow.style.left='auto';return root;
}
function renderColourControl(control,x,y,w,h,parent){
  const p=control.properties||{},e=document.createElement('div');e.className='dx-colour-control';e.style.left=`${x}px`;e.style.top=`${y}px`;e.style.width=`${w||40}px`;e.style.height=`${h||15}px`;e.style.background=cssColour(p.BackColour,'#000');parent.append(e);return e;
}
function renderListBox(control,x,y,w,h,parent){
  const root=document.createElement('div');root.className='dx-listbox';root.style.left=`${x}px`;root.style.top=`${y}px`;root.style.width=`${w}px`;root.style.height=`${h}px`;parent.append(root);
  renderScrollBar({type:'DXVScrollBar'},Math.max(0,w-14),0,14,h,root);return root;
}
function renderSoundBar(control,x,y,parent){
  const root=document.createElement('div');root.className='dx-soundbar';root.style.left=`${x}px`;root.style.top=`${y}px`;root.style.width='180px';root.style.height='18px';parent.append(root);
  img(asset('GameInter',4741),0,1,'ui-button',root);
  img(asset('GameInter',4743),20,3,'ui-img',root);
  const inner=img(asset('GameInter',4742),22,5,'ui-img dx-sound-inner',root);inner.style.clipPath='inset(0 35% 0 0)';
  img(asset('GameInter',4746),100,1,'ui-button',root);return root;
}
function renderTreeControl(control,x,y,w,h,parent){
  const root=document.createElement('div');root.className='dx-tree-control';root.style.left=`${x}px`;root.style.top=`${y}px`;root.style.width=`${w}px`;root.style.height=`${h}px`;parent.append(root);
  const rows=document.createElement('div');rows.className='dx-tree-runtime';rows.textContent='Tree rows: runtime data';root.append(rows);
  renderScrollBar({type:'DXVScrollBar'},Math.max(0,w-18),0,18,h,root,{up:61,down:62,thumb:60,background:59});return root;
}

// ---------------------------------------------------------------------------
// Source-driven renderer for all remaining GameScene windows
// ---------------------------------------------------------------------------
function buildDxFrame(width,height,title,props={}) {
  const root=document.createElement('div'); root.className='generic-window'; root.style.width=`${width}px`; root.style.height=`${height}px`;
  const hasTop=props.HasTopBorder===undefined?true:boolFrom(props.HasTopBorder,true),hasTitle=props.HasTitle===undefined?true:boolFrom(props.HasTitle,true),hasFooter=boolFrom(props.HasFooter,false),slimFooter=boolFrom(props.SlimFooter,false);
  const topIndex=hasTop?0:2,cornerLeft=hasTop?11:25,cornerRight=hasTop?12:26;
  const top=img(asset('Interface',topIndex),0,0,'ui-img dx-window-stretch-x',root);top.style.width='100%';
  const left=img(asset('Interface',1),0,20,'ui-img dx-window-side',root);left.style.height='calc(100% - 20px)';
  const right=img(asset('Interface',1),Math.max(0,width-8),20,'ui-img dx-window-side',root);right.style.height='calc(100% - 20px)';
  if(hasTitle){const mid=img(asset('Interface',3),8,20,'ui-img dx-window-stretch-x',root);mid.style.width=`${Math.max(0,width-16)}px`;img(asset('Interface',4),0,34,'ui-img',root);const rc=img(asset('Interface',5),0,34,'ui-img',root);rc.style.right='0';rc.style.left='auto'}
  img(asset('Interface',cornerLeft),0,0,'ui-img',root);const tr=img(asset('Interface',cornerRight),0,0,'ui-img',root);tr.style.right='0';tr.style.left='auto';
  if(hasFooter||slimFooter){const footer=img(asset('Interface',126),0,0,'ui-img dx-window-stretch-x',root);footer.style.bottom='0';footer.style.top='auto';footer.style.width='100%'}
  const bottomY=Math.max(0,height-(hasFooter||slimFooter?24:8));const bottom=img(asset('Interface',2),0,bottomY,'ui-img dx-window-stretch-x',root);bottom.style.width='100%';
  img(asset('Interface',8),0,Math.max(0,bottomY-8),'ui-img',root);const br=img(asset('Interface',9),0,Math.max(0,bottomY-8),'ui-img',root);br.style.right='0';br.style.left='auto';
  const header=document.createElement('div');header.className='generic-window-header';header.textContent=title;root.append(header);
  const close=img(asset('Interface',15),width-24,3,'close',root);close.addEventListener('click',()=>root.remove());
  const body=document.createElement('div');body.className='generic-window-body';root.append(body);return{root,body};
}
function fallbackSize(item) {
  const root=item.root||{};return pairFrom(root.Size,'Size')||pairFrom(root.ClientSize,'Size')||[Math.min(520,item.category==='npc'?420:380),item.category==='hud'?180:300];
}
function preferredLocation(item,w,h){return pairFrom(item.defaultLocationExpression,'Point')||pairFrom(item.root?.Location,'Point')||[Math.max(0,(1024-w)/2),Math.max(0,(700-h)/2)]}
function controlPosition(p,index) { return pairFrom(p.Location,'Point') || [10 + (index%3)*95, 34 + Math.floor(index/3)*42]; }
function controlSize(p,type) {
  const exact=pairFrom(p.Size,'Size');if(exact)return exact;
  const gs=pairFrom(p.GridSize,'Size');if(gs)return[gs[0]*35+1,gs[1]*35+1];
  if(type==='DXButton')return[90,24];if(type==='DXLabel')return[120,18];if(type==='DXItemCell')return[36,36];if(type==='DXVScrollBar')return[16,120];if(type==='DXHScrollBar')return[120,16];if(type==='DXComboBox')return[120,16];if(type==='DXListBox')return[160,120];if(type==='DXTreeControl')return[220,210];if(type==='DXColourControl')return[40,15];if(type==='DXNumberBox')return[90,20];if(type==='DXTextBox'||type==='DXNumberTextBox')return[120,20];return[80,28];
}
function renderControl(control,index,parent,ctx) {
  const p=control.properties||{},[x,y]=controlPosition(p,index),[w,h]=controlSize(p,control.type),lib=libraryFrom(p.LibraryFile),idx=numberFrom(p.Index);
  if((control.type==='DXImageControl'||control.type==='DXAnimatedControl')&&lib&&idx!==null){const e=img(asset(lib,idx),x,y,'ui-img',parent);e.title=`${control.name}: ${control.type}`;return e}
  switch(control.type){
    case 'DXButton':
      if(lib&&idx!==null){const e=img(asset(lib,idx),x,y,'ui-button',parent);e.title=`${control.name}: DXButton`;return e}
      return renderGeneratedButton(sourceText(p.Label||p.Text,control.name),x,y,w,h,buttonTypeFrom(p.ButtonType),parent);
    case 'DXLabel': {const e=label(sourceText(p.Text,control.name),x,y,w,parent);e.classList.add('dx-label');return e}
    case 'DXCheckBox': return renderCheckBox(control,x,y,parent);
    case 'DXItemCell': return renderItemCell(control,x,y,parent);
    case 'DXItemGrid': {
      const gs=pairFrom(p.GridSize,'Size')||[4,4],grid=document.createElement('div');grid.className='generic-control generic-grid';grid.style.left=`${x}px`;grid.style.top=`${y}px`;grid.style.width=`${gs[0]*35+1}px`;grid.style.height=`${gs[1]*35+1}px`;grid.style.gridTemplateColumns=`repeat(${gs[0]},35px)`;
      for(let n=0;n<gs[0]*gs[1];n++){const c=document.createElement('div');c.className='generic-cell';grid.append(c)}parent.append(grid);return grid;
    }
    case 'DXControl': return renderStructuralControl(control,x,y,w,h,parent);
    case 'DXTab': case 'DXConfigTab': return renderTab(control,ctx,parent);
    case 'DXTabControl': return null;
    case 'DXVScrollBar': case 'DXHScrollBar': return renderScrollBar(control,x,y,w,h,parent);
    case 'DXTextBox': case 'DXNumberTextBox': return renderTextBox(control,x,y,w,h,parent);
    case 'DXNumberBox': return renderNumberBox(control,x,y,parent);
    case 'DXComboBox': return renderComboBox(control,x,y,w,parent);
    case 'DXColourControl': return renderColourControl(control,x,y,w,h,parent);
    case 'DXListBox': return renderListBox(control,x,y,w,h,parent);
    case 'DXSoundBar': return renderSoundBar(control,x,y,parent);
    case 'DXTreeControl': return renderTreeControl(control,x,y,w,h,parent);
    case 'DXKeyBindWindow': return null;
    default: {
      const e=document.createElement('div');e.className='generic-control unknown-control';e.style.left=`${x}px`;e.style.top=`${y}px`;e.style.width=`${w}px`;e.style.height=`${h}px`;e.textContent=`UNMAPPED ${control.type}`;e.title=JSON.stringify(p);parent.append(e);return e;
    }
  }
}
function genericWindow(item) {
  const rootLib=libraryFrom(item.root?.LibraryFile),rootIndex=numberFrom(item.root?.Index),ctx={tabX:0,tabCount:0};
  if(rootLib&&rootIndex!==null){
    const [x,y]=preferredLocation(item,380,300),root=addImageWindow(item.id,rootLib,rootIndex,x,y,item.sourceClass);(item.controls||[]).forEach((c,i)=>renderControl(c,i,root,ctx));return root;
  }
  const [w,h]=fallbackSize(item),{root,body}=buildDxFrame(w,h,item.sourceClass,item.root||{});root.id=`w-${item.id}`;const[x,y]=preferredLocation(item,w,h);root.style.left=`${x}px`;root.style.top=`${y}px`;
  (item.controls||[]).forEach((c,i)=>renderControl(c,i,body,ctx));const badge=document.createElement('div');badge.className='generic-source-badge';badge.textContent=item.sourcePath||'source class unresolved';root.append(badge);stage.append(root);windows.set(item.id,root);placeIfOffscreen(root);return root;
}
function placeIfOffscreen(root){requestAnimationFrame(()=>{const w=root.offsetWidth||350,h=root.offsetHeight||300;let x=parseInt(root.style.left)||0,y=parseInt(root.style.top)||0;if(x+w>1024)x=Math.max(0,1024-w);if(y+h>700)y=Math.max(0,700-h);root.style.left=`${x}px`;root.style.top=`${y}px`})}

const exactRenderers={character:exactCharacter,inspect:exactCharacter,inventory:exactInventory,magic:exactMagic,quest:exactQuest,menu:exactMenu};
function itemById(id){return sourceSpec?.windows?.find(x=>x.id===id||x.field===gameSceneWindows.find(g=>g.id===id)?.field)||gameSceneWindows.find(x=>x.id===id)}
function openWindow(id){
  if(id==='main-panel'||id==='belt'||id==='minimap'||id==='buffs'||id==='group-health'||id==='timer'){selectionInfo.textContent=`${id}: persistent/default GameScene HUD component.`;return}
  removeTransientWindows();const item=itemById(id);if(!item)return;const enriched={...gameSceneWindows.find(x=>x.field===item.field),...item,id};const renderer=exactRenderers[id]||genericWindow;renderer(enriched);activeId=id;
  document.querySelector(`[data-window-id="${id}"]`)?.classList.add('active');const source=enriched.sourcePath?` — ${enriched.sourcePath}`:'';selectionInfo.textContent=`${enriched.field} / ${enriched.sourceClass||enriched.class}${source}`;
}
function mergeSpec(raw){const byField=new Map((raw.windows||[]).map(w=>[w.field,w]));return gameSceneWindows.map(base=>({...base,...(byField.get(base.field)||{}),id:base.id,sourceClass:(byField.get(base.field)||{}).class||base.sourceClass}))}
async function loadSpec(){
  try{const r=await fetch('ui-source-spec.json',{cache:'no-store'});if(!r.ok)throw new Error(r.statusText);const raw=await r.json();sourceSpec={...raw,windows:mergeSpec(raw)};sourceStatus.textContent=`${raw.windowCount||sourceSpec.windows.length} GameScene entries · all discovered DX control types have explicit render policy`}
  catch(err){sourceSpec={windows:gameSceneWindows};sourceStatus.textContent=`static GameScene registry (${gameSceneWindows.length} entries); generated source spec not present in this checkout`}
  renderCatalog();
}
function renderCatalog(){
  list.innerHTML='';const q=search.value.trim().toLowerCase(),items=(sourceSpec?.windows||gameSceneWindows).filter(x=>(activeCategory==='all'||x.category===activeCategory)&&(!q||`${x.id} ${x.field} ${x.sourceClass||x.class}`.toLowerCase().includes(q)));
  for(const category of uiCategories){const groupItems=items.filter(x=>x.category===category);if(!groupItems.length)continue;const group=document.createElement('div');group.className='catalog-group';const head=document.createElement('div');head.className='catalog-group-title';head.textContent=`${category} (${groupItems.length})`;group.append(head);for(const item of groupItems){const b=document.createElement('button');b.className='catalog-item';b.dataset.windowId=item.id;b.innerHTML=`${item.id}<small>${item.field} · ${item.sourceClass||item.class}</small>`;b.addEventListener('click',()=>openWindow(item.id));group.append(b)}list.append(group)}
}
function buildFilters(){for(const c of ['all',...uiCategories]){const b=document.createElement('button');b.textContent=c;b.dataset.category=c;if(c==='all')b.classList.add('active');b.addEventListener('click',()=>{activeCategory=c;filters.querySelectorAll('button').forEach(x=>x.classList.toggle('active',x===b));renderCatalog()});filters.append(b)}}

document.querySelector('[data-close-all]').addEventListener('click',()=>{removeTransientWindows();selectionInfo.textContent='All transient Zircon windows closed.'});
document.querySelector('#reset-layout').addEventListener('click',()=>{buildDesktop();selectionInfo.textContent='Zircon desktop reset.'});
search.addEventListener('input',renderCatalog);

buildFilters();buildDesktop();loadSpec();
