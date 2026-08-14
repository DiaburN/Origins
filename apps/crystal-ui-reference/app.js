const root = document.querySelector('#ui-root');
const manifest = await fetch('./ui-assets.json').then(r => r.json());

const libFolder = {
  'Prguse.Lib': 'Prguse',
  'Prguse2.Lib': 'Prguse2',
  'Title.Lib': 'Title',
  'UI_32bit.Lib': 'UI_32bit',
};

function meta(lib, id) {
  const result = manifest.libraries?.[lib]?.[String(id)];
  if (!result) throw new Error(`Missing Crystal UI asset ${lib} #${id}`);
  return result;
}
function src(lib, id) { return `./assets/${libFolder[lib]}/${String(id).padStart(5,'0')}.png`; }
function image(lib, id, x, y, cls='ui-img', parent=root) {
  const el = document.createElement('img');
  el.src = src(lib,id); el.dataset.lib=lib; el.dataset.index=id;
  el.className=cls; el.style.left=`${x}px`; el.style.top=`${y}px`;
  parent.append(el); return el;
}
function label(text,x,y,w=null,cls='ui-label',parent=root){
  const el=document.createElement('div'); el.className=cls; el.textContent=text;
  el.style.left=`${x}px`; el.style.top=`${y}px`; if(w){el.style.width=`${w}px`;el.style.textAlign='center'}
  parent.append(el); return el;
}
function button(lib, normal, hover, pressed, x, y, onClick, parent=root){
  const el=image(lib,normal,x,y,'ui-button',parent);
  const set=i=>{el.src=src(lib,i);el.dataset.index=i};
  if(hover!=null) el.addEventListener('mouseenter',()=>set(hover));
  el.addEventListener('mouseleave',()=>set(normal));
  if(pressed!=null){el.addEventListener('mousedown',()=>set(pressed));window.addEventListener('mouseup',()=>{if(el.matches(':hover')&&hover!=null)set(hover);else set(normal)})}
  if(onClick) el.addEventListener('click',onClick);
  return el;
}

// ---- MainDialog: exact 1024-resolution Crystal source layout ----
const main = meta('Prguse.Lib',1);
const mainX = Math.round((1024-main.size[0])/2);
const mainY = 768-main.size[1];
image('Prguse.Lib',1,mainX,mainY);
image('Prguse.Lib',4,mainX,mainY+30);          // full HP/MP orb at 100%
image('Prguse.Lib',8,mainX+9,mainY+143);       // EXP fill source image
image('Prguse.Lib',76,mainX+main.size[0]-105,mainY+103); // weight fill source image

label('HP 44/44',mainX+28,mainY+57,null,'ui-label small');
label('MP 28/28',mainX+28,mainY+72,null,'ui-label small');
label('1',mainX+5,mainY+108);
label('ORIGINS',mainX+6,mainY+120,90,'ui-label small');
label('0.00%',mainX+Math.round(main.size[0]/2)-22,mainY+133,null,'ui-label small');
label('0',mainX+main.size[0]-102,mainY+101,null,'ui-label small');
label('40',mainX+main.size[0]-28,mainY+101,null,'ui-label small');
label('0',mainX+main.size[0]-100,mainY+119,null,'ui-label small');

// Main HUD buttons, indices and positions copied from MainDialogs.cs.
button('Prguse.Lib',1900,1901,1902,mainX+main.size[0]-119,mainY+76,()=>showCharacter('character'));
button('Prguse.Lib',1903,1904,1905,mainX+main.size[0]-96, mainY+76,()=>toggleWindow('inventory-window'));
button('Prguse.Lib',1906,1907,1908,mainX+main.size[0]-73, mainY+76,()=>showCharacter('skills'));
button('Prguse.Lib',1909,1910,1911,mainX+main.size[0]-50, mainY+76,()=>flashUnavailable('QuestDiaryDialog'));
button('Prguse.Lib',1912,1913,1914,mainX+main.size[0]-27, mainY+76,()=>flashUnavailable('OptionDialog'));
button('Prguse.Lib',1960,1961,1962,mainX+main.size[0]-55, mainY+35,()=>flashUnavailable('MenuDialog'));
button('Prguse.Lib',826,827,828,mainX+main.size[0]-105, mainY+35,()=>flashUnavailable('GameShopDialog'));

// ---- BeltDialog, visible by default in GameScene ----
const beltX=mainX+230, beltY=768-150;
image('Prguse.Lib',1932,beltX,beltY);
// Crystal draws Index+1 at 50% opacity on top; keep the actual second source piece visible.
const beltOverlay=image('Prguse.Lib',1933,beltX,beltY); beltOverlay.style.opacity='.5';
button('Prguse.Lib',1926,1927,1928,beltX+222,beltY+3,null);
button('Prguse.Lib',1923,1924,1925,beltX+222,beltY+19,null);
for(let i=0;i<6;i++) label(String(i+1),beltX+8+i*35,beltY+2,null,'ui-label small');

// ---- ChatControlBar ----
const chatX=mainX+230, controlY=768-112, chatY=768-97;
image('Prguse.Lib',2034,chatX,controlY);
const chatButtons=[
  [2036,2037,2038,12],[2039,2040,2041,34],[2042,2043,2044,56],
  [2045,2046,2047,78],[2048,2049,2050,100],[2051,2052,2053,122],
  [2054,2055,2056,144],[2004,2005,2006,166]
];
chatButtons.forEach(([a,b,c,x])=>button('Prguse.Lib',a,b,c,chatX+x,controlY+1,null));
button('Prguse.Lib',2057,2058,2059,chatX+574,controlY+1,null);
button('Prguse.Lib',2060,2061,2062,chatX+596,controlY+1,null);

// ---- ChatDialog default four-line 1024 version ----
image('Prguse.Lib',2221,chatX,chatY);
button('Prguse.Lib',2018,2019,2020,chatX+618,chatY+1,null);
button('Prguse.Lib',2021,2022,2023,chatX+618,chatY+9,null);
image('Prguse.Lib',2012,chatX+622,chatY+16);
button('Prguse.Lib',2015,2016,2017,chatX+619,chatY+16,null);
button('Prguse.Lib',2024,2025,2026,chatX+618,chatY+39,null);
button('Prguse.Lib',2027,2028,2029,chatX+618,chatY+45,null);
const chatLines=[['Welcome to ORIGINS.', 'system'],['Zuma Temple', 'guild'],['Crystal interface reconstruction', ''],['All UI art: Crystal source libraries', '']];
chatLines.forEach(([t,c],i)=>label(t,chatX+1,chatY+1+i*13,null,`chat-line ${c}`));

// ---- MiniMapDialog ----
const miniX=1024-126, miniY=0;
const miniContent=document.createElement('div'); miniContent.className='minimap-content';
miniContent.style.left=`${miniX+3}px`;miniContent.style.top=`${miniY+22}px`;miniContent.style.width='120px';miniContent.style.height='108px';
miniContent.innerHTML='<img src="./reference/d515-full.png" alt="Zuma minimap reference">'; root.append(miniContent);
image('Prguse.Lib',2090,miniX,miniY);
label('Zuma Temple',miniX+2,miniY+4,120,'ui-label small');
label('20, 32',miniX+46,miniY+133,56,'ui-label small');
button('Prguse.Lib',2099,2100,2101,miniX+4,miniY+131,()=>flashUnavailable('MailListDialog'));
button('Prguse.Lib',2096,2097,2098,miniX+25,miniY+131,()=>flashUnavailable('BigMapDialog'));
button('Prguse.Lib',2102,2103,2104,miniX+109,miniY+3,null);
image('Prguse.Lib',2093,miniX+102,miniY+131);

// ---- InventoryDialog: real Crystal source base and controls ----
const inv=document.createElement('div'); inv.id='inventory-window';inv.className='window-layer hidden';root.append(inv);
image('Title.Lib',196,0,0,'ui-window',inv);
image('Prguse.Lib',24,182,217,'ui-img',inv);
button('Title.Lib',197,197,197,6,7,null,inv);
button('Title.Lib',738,738,738,76,7,null,inv);
button('Title.Lib',739,739,739,146,7,null,inv);
button('Prguse2.Lib',360,361,362,289,3,()=>hideWindow('inventory-window'),inv);
button('Prguse2.Lib',366,367,368,291,212,null,inv);
label('0',40,212,111,'ui-label small',inv);
label('40',268,212,26,'ui-label small',inv);
// Source locations for first 40 visible inventory cells.
const grid=document.createElement('div');grid.className='slot-grid';grid.style.left='9px';grid.style.top='37px';grid.style.width='291px';grid.style.height='164px';inv.append(grid);
for(let i=0;i<40;i++){const s=document.createElement('div');s.className='slot';grid.append(s)}

// ---- CharacterDialog + Character/Skill pages ----
const char=document.createElement('div'); char.id='character-window';char.className='window-layer hidden';root.append(char);
const charX=1024-264,charY=0;
image('Title.Lib',504,charX,charY,'ui-window',char);
button('Title.Lib',500,500,500,charX+8,charY+70,()=>showCharacter('character'),char);
button('Title.Lib',501,501,501,charX+70,charY+70,()=>showCharacter('status'),char);
button('Title.Lib',502,502,502,charX+132,charY+70,()=>showCharacter('state'),char);
button('Title.Lib',503,503,503,charX+194,charY+70,()=>showCharacter('skills'),char);
button('Prguse2.Lib',360,361,362,charX+241,charY+3,()=>hideWindow('character-window'),char);
label('ORIGINS',charX,charY+12,264,'ui-label',char);
label('Wizard',charX,charY+35,264,'ui-label small',char);
image('Prguse.Lib',100,charX+15,charY+33,'ui-img',char);
let charPage=image('Prguse.Lib',340,charX+8,charY+90,'ui-img',char); charPage.id='character-page-image';
const charModeLabel=label('',charX+100,charY+106,null,'skill-placeholder',char);

function showCharacter(mode){
  inv.classList.add('hidden');char.classList.remove('hidden');
  charModeLabel.textContent='';
  if(mode==='character') charPage.src=src('Prguse.Lib',340);
  if(mode==='status') charPage.src=src('Title.Lib',506);
  if(mode==='state') charPage.src=src('Title.Lib',507);
  if(mode==='skills') { charPage.src=src('Title.Lib',508); charModeLabel.textContent='Crystal SkillPage'; }
}
function toggleWindow(id){ const el=document.getElementById(id); el.classList.toggle('hidden'); if(id==='inventory-window') char.classList.add('hidden'); }
function hideWindow(id){ document.getElementById(id).classList.add('hidden'); }
function flashUnavailable(name){
  let n=document.getElementById('source-dialog-note');
  if(!n){n=label('',350,20,320,'ui-label');n.id='source-dialog-note';n.style.padding='7px 10px';n.style.background='rgba(0,0,0,.75)';n.style.textAlign='center'}
  n.textContent=`${name}: source window queued for reconstruction`;n.style.display='block';clearTimeout(window.__note);window.__note=setTimeout(()=>n.style.display='none',1600);
}
