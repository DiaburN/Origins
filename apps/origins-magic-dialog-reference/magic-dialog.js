const pad = value => String(value).padStart(5, '0');
const ui = index => `assets/Interface/${pad(index)}.png`;
const crystalIcon = index => `assets/CrystalMagIcon2/${pad(index)}.png`;
const dialog = document.querySelector('#magic-dialog');
const status = document.querySelector('#qa-status');
const CLASS_ORDER = ['Warrior','Wizard','Taoist','Assassin','Archer','Monk'];
const HEADER = {Warrior:160,Wizard:161,Taoist:162,Assassin:163,Archer:null,Monk:null};
const TAB = {selected:[56,58,57],deselected:[53,55,54]};
let catalog;
let selectedClass = 'Warrior';
let offset = 0;

function img(src, className, parent=dialog) {
  const el = document.createElement('img');
  el.src = src;
  el.className = `ui-img ${className}`;
  el.draggable = false;
  parent.append(el);
  return el;
}

function buildShell() {
  img(ui(0),'shell-top dx-stretch-x');
  img(ui(1),'shell-left');
  img(ui(1),'shell-right');
  img(ui(3),'shell-title-fill');
  img(ui(4),'shell-title-left');
  img(ui(5),'shell-title-right');
  img(ui(11),'shell-bottom-left');
  img(ui(12),'shell-bottom-right');
  img(ui(2),'shell-bottom dx-stretch-x');

  const title = document.createElement('div');
  title.className = 'window-title';
  title.textContent = 'Magic';
  dialog.append(title);

  const close = img(ui(15),'close-button');
  close.style.pointerEvents = 'auto';
  close.addEventListener('click',()=>{ dialog.style.visibility='hidden'; });

  const body = img(ui(164),'body-art');
  body.alt = '';

  const className = document.createElement('div');
  className.className = 'class-name';
  className.id = 'active-class-name';
  dialog.append(className);

  const tabs = document.createElement('div');
  tabs.className = 'class-tabs';
  tabs.id = 'class-tabs';
  dialog.append(tabs);

  const viewport = document.createElement('div');
  viewport.className = 'list-viewport';
  viewport.id = 'list-viewport';
  const inner = document.createElement('div');
  inner.className = 'list-inner';
  inner.id = 'list-inner';
  viewport.append(inner);
  dialog.append(viewport);
  viewport.addEventListener('wheel', event => {
    event.preventDefault();
    move(event.deltaY > 0 ? 59 : -59);
  }, {passive:false});

  const scrollbar = document.createElement('div');
  scrollbar.className = 'scrollbar';
  scrollbar.innerHTML = '<div class="scroll-track"></div>';
  const up = document.createElement('button');
  up.className = 'scroll-button scroll-up';
  const upImg = document.createElement('img'); upImg.src=ui(61); up.append(upImg);
  const down = document.createElement('button');
  down.className = 'scroll-button scroll-down';
  const downImg = document.createElement('img'); downImg.src=ui(62); down.append(downImg);
  const thumb = document.createElement('button');
  thumb.className = 'scroll-thumb'; thumb.id='scroll-thumb';
  const thumbImg = document.createElement('img'); thumbImg.src=ui(60); thumb.append(thumbImg);
  up.addEventListener('click',()=>move(-59)); down.addEventListener('click',()=>move(59));
  scrollbar.append(up,down,thumb);
  dialog.append(scrollbar);
}

function buildTabs() {
  const root = document.querySelector('#class-tabs');
  root.replaceChildren();
  for (const className of CLASS_ORDER) {
    const selected = className === selectedClass;
    const button = document.createElement('button');
    button.className = 'class-tab';
    button.dataset.class = className;
    button.setAttribute('aria-selected', String(selected));
    const indices = selected ? TAB.selected : TAB.deselected;
    for (const [part,index] of [['left',indices[0]],['middle',indices[1]],['right',indices[2]]]) {
      const partImg = document.createElement('img');
      partImg.src=ui(index); partImg.className=`tab-part ${part}`; partImg.draggable=false;
      button.append(partImg);
    }
    const label = document.createElement('span');
    label.className='tab-label'; label.textContent=className;
    button.append(label);
    button.addEventListener('click',()=>selectClass(className));
    root.append(button);
  }
}

function headerFor(className) {
  document.querySelector('.header-art')?.remove();
  const index = HEADER[className];
  if (index == null) return;
  const header = img(ui(index),'header-art');
  header.alt='';
  dialog.insertBefore(header, document.querySelector('.body-art'));
}

function spellTooltip(spell) {
  const levels = spell.requiredLevels?.filter(Number.isInteger).join(' / ') || 'not implemented in source';
  const needs = spell.experienceNeeds?.filter(Number.isInteger).join(' / ');
  const pieces = [spell.spell, `Spell ID ${spell.spellId}`, `Required levels ${levels}`];
  if (needs) pieces.push(`Experience needs ${needs}`);
  if (Number.isFinite(spell.baseCost)) pieces.push(`Base cost ${spell.baseCost}`);
  if (Number.isFinite(spell.levelCost)) pieces.push(`Level cost ${spell.levelCost}`);
  if (Number.isFinite(spell.range)) pieces.push(`Range ${spell.range}`);
  pieces.push(`${spell.source.repo} / ${spell.source.path}`);
  if (spell.sourceIssue) pieces.push(spell.sourceIssue);
  return pieces.join('\n');
}

function buildCell(spell) {
  const cell = document.createElement('div');
  cell.className = `magic-cell${spell.sourceImplemented ? '' : ' source-unimplemented'}`;
  cell.title = spellTooltip(spell);
  const bg = document.createElement('img');
  bg.src=ui(165); bg.className='magic-cell-bg'; bg.draggable=false; cell.append(bg);

  if (spell.iconFrameNormal != null) {
    const icon = document.createElement('img');
    icon.className='magic-icon'; icon.src=crystalIcon(spell.iconFrameNormal); icon.draggable=false;
    icon.dataset.normal=crystalIcon(spell.iconFrameNormal);
    icon.dataset.pressed=crystalIcon(spell.iconFramePressed);
    icon.addEventListener('pointerdown',()=>{icon.src=icon.dataset.pressed});
    const restore=()=>{icon.src=icon.dataset.normal};
    icon.addEventListener('pointerup',restore); icon.addEventListener('pointercancel',restore); icon.addEventListener('pointerleave',restore);
    cell.append(icon);
  } else {
    const empty = document.createElement('div');
    empty.className='magic-icon-empty'; empty.textContent='SOURCE\nN/A'; cell.append(empty);
  }

  const name=document.createElement('div'); name.className='magic-name'; name.textContent=spell.spell; cell.append(name);
  const required=document.createElement('div'); required.className='magic-required';
  required.textContent=spell.sourceImplemented ? `Required Lv ${spell.requiredLevels[0]}` : 'Source MagicInfo not implemented'; cell.append(required);
  const more=document.createElement('div'); more.className='magic-more';
  more.textContent=spell.sourceImplemented ? `Magic Lv2 ${spell.requiredLevels[1]} · Lv3 ${spell.requiredLevels[2]}` : `Spell ID ${spell.spellId}`; cell.append(more);
  if (!spell.sourceImplemented) {
    const issue=document.createElement('div'); issue.className='magic-source-issue'; issue.textContent='No official icon/levels found — intentionally not fabricated'; cell.append(issue);
  } else {
    const reserved=document.createElement('div'); reserved.className='runtime-reserved'; reserved.title='Reserved for real runtime EXP/keybind data'; cell.append(reserved);
  }
  return cell;
}

function currentSpells() {
  const spells = [...catalog.classes[selectedClass].spells];
  spells.sort((a,b)=>{
    const al=Number.isInteger(a.requiredLevels?.[0])?a.requiredLevels[0]:Number.MAX_SAFE_INTEGER;
    const bl=Number.isInteger(b.requiredLevels?.[0])?b.requiredLevels[0]:Number.MAX_SAFE_INTEGER;
    return al-bl || a.spellId-b.spellId;
  });
  return spells;
}

function renderList() {
  const inner=document.querySelector('#list-inner');
  inner.replaceChildren(...currentSpells().map(buildCell));
  offset=0;
  updateScroll();
}

function maxOffset() {
  const count=currentSpells().length;
  return Math.max(0, count*59 - 5 - 392);
}

function move(delta) {
  offset=Math.max(0,Math.min(maxOffset(),offset+delta));
  updateScroll();
}

function updateScroll() {
  document.querySelector('#list-inner').style.transform=`translateY(${-offset}px)`;
  const thumb=document.querySelector('#scroll-thumb');
  const max=maxOffset();
  const travel=348;
  thumb.style.top=`${17 + (max ? Math.round((offset/max)*travel) : 0)}px`;
  thumb.style.visibility=max ? 'visible':'hidden';
}

function selectClass(className) {
  selectedClass=className;
  document.querySelector('#active-class-name').textContent=className;
  headerFor(className);
  buildTabs();
  renderList();
}

async function start() {
  const response=await fetch('data/magic/magic-catalog.json',{cache:'no-store'});
  if(!response.ok) throw new Error(`magic-catalog.json ${response.status}`);
  catalog=await response.json();
  const count=Object.values(catalog.classes).reduce((sum,c)=>sum+c.spells.length,0);
  if(count!==114) throw new Error(`expected 114 spells, got ${count}`);
  buildShell();
  selectClass('Warrior');
  status.textContent='6 classes · 114 spells · real Crystal MagIcon2 mapping';
}

start().catch(error=>{console.error(error);status.textContent=`ERROR: ${error.message}`;status.style.color='#d77';});
