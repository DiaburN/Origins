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
  const set=i=>{ if(i==null) return; el.src=src(lib,i);el.dataset.index=i };
  if(hover!=null) el.addEventListener('mouseenter',()=>set(hover));
  el.addEventListener('mouseleave',()=>set(normal));
  if(pressed!=null){el.addEventListener('mousedown',()=>set(pressed));window.addEventListener('mouseup',()=>{if(el.matches(':hover')&&hover!=null)set(hover);else set(normal)})}
  if(onClick) el.addEventListener('click',onClick);
  return el;
}
function layer(id){ const el=document.createElement('div');el.id=id;el.className='window-layer hidden';root.append(el);return el; }
function hideAllPrimary(){ ['inventory-window','character-window','option-window','menu-window','quest-window'].forEach(hideWindow); }
function togglePrimary(id){ const target=document.getElementById(id);const wasHidden=target.classList.contains('hidden');hideAllPrimary();if(wasHidden)target.classList.remove('hidden'); }
function hideWindow(id){ const el=document.getElementById(id);if(el)el.classList.add('hidden'); }

// ---- MainDialog: exact 1024-resolution Crystal source layout ----
const main = meta('Prguse.Lib',1);
const mainX = Math.round((1024-main.size[0])/2);
const mainY = 768-main.size[1];
image('Prguse.Lib',1,mainX,mainY);
image('Prguse.Lib',4,mainX,mainY+30);          // HealthOrb full HP/MP source artwork
image('Prguse.Lib',8,mainX+9,mainY+143);       // ExperienceBar source artwork
image('Prguse.Lib',76,mainX+main.size[0]-105,mainY+103); // WeightBar source artwork

label('HP 44/44',mainX+28,mainY+57,null,'ui-label small');
label('MP 28/28',mainX+28,mainY+72,null,'ui-label small');
label('1',mainX+5,mainY+108);
label('ORIGINS',mainX+6,mainY+120,90,'ui-label small');
label('0.00%',mainX+Math.round(main.size[0]/2)-22,mainY+133,null,'ui-label small');
label('0',mainX+main.size[0]-102,mainY+101,null,'ui-label small');
label('40',mainX+main.size[0]-28,mainY+101,null,'ui-label small');
label('0',mainX+main.size[0]-100,mainY+119,null,'ui-label small');

// Main HUD buttons, exact indices and source positions.
button('Prguse.Lib',1900,1901,1902,mainX+main.size[0]-119,mainY+76,()=>showCharacter('character'));
button('Prguse.Lib',1903,1904,1905,mainX+main.size[0]-96, mainY+76,()=>togglePrimary('inventory-window'));
button('Prguse.Lib',1906,1907,1908,mainX+main.size[0]-73, mainY+76,()=>showCharacter('skills'));
button('Prguse.Lib',1909,1910,1911,mainX+main.size[0]-50, mainY+76,()=>togglePrimary('quest-window'));
button('Prguse.Lib',1912,1913,1914,mainX+main.size[0]-27, mainY+76,()=>togglePrimary('option-window'));
button('Prguse.Lib',1960,1961,1962,mainX+main.size[0]-55, mainY+35,()=>togglePrimary('menu-window'));
button('Prguse.Lib',826,827,828,mainX+main.size[0]-105, mainY+35,()=>sourceNotice('GameShopDialog'));

// ---- BeltDialog, visible by default in GameScene ----
const beltX=mainX+230, beltY=768-150;
image('Prguse.Lib',1932,beltX,beltY);
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
const chatLines=[['Welcome to ORIGINS.', 'system'],['Zuma Temple', 'guild'],['Crystal desktop UI reconstruction', ''],['UI artwork and placement from Crystal source', '']];
chatLines.forEach(([t,c],i)=>label(t,chatX+1,chatY+1+i*13,null,`chat-line ${c}`));

// ---- MiniMapDialog ----
const miniX=1024-126, miniY=0;
const miniContent=document.createElement('div'); miniContent.className='minimap-content';
miniContent.style.left=`${miniX+3}px`;miniContent.style.top=`${miniY+22}px`;miniContent.style.width='120px';miniContent.style.height='108px';
miniContent.innerHTML='<img src="./reference/d515-full.png" alt="Zuma minimap reference">'; root.append(miniContent);
image('Prguse.Lib',2090,miniX,miniY);
label('Zuma Temple',miniX+2,miniY+4,120,'ui-label small');
label('20, 32',miniX+46,miniY+133,56,'ui-label small');
button('Prguse.Lib',2099,2100,2101,miniX+4,miniY+131,()=>sourceNotice('MailListDialog'));
button('Prguse.Lib',2096,2097,2098,miniX+25,miniY+131,()=>sourceNotice('BigMapDialog'));
button('Prguse.Lib',2102,2103,2104,miniX+109,miniY+3,null);
image('Prguse.Lib',2093,miniX+102,miniY+131);
// DuraStatusDialog is visible by default. Its Character button is offset +20,0.
button('Prguse.Lib',2113,2111,2112,miniX+86+20,meta('Prguse.Lib',2090).size[1],()=>sourceNotice('CharacterDuraPanel'));

// ---- InventoryDialog ----
const inv=layer('inventory-window');
image('Title.Lib',196,0,0,'ui-window',inv);
image('Prguse.Lib',24,182,217,'ui-img',inv);
button('Title.Lib',197,197,197,6,7,null,inv);
button('Title.Lib',738,738,738,76,7,null,inv);
button('Title.Lib',739,739,739,146,7,null,inv);
button('Prguse2.Lib',360,361,362,289,3,()=>hideWindow('inventory-window'),inv);
button('Prguse2.Lib',366,367,368,291,212,null,inv);
label('0',40,212,111,'ui-label small',inv);
label('40',268,212,26,'ui-label small',inv);
const grid=document.createElement('div');grid.className='slot-grid';grid.style.left='9px';grid.style.top='37px';grid.style.width='291px';grid.style.height='164px';inv.append(grid);
for(let i=0;i<40;i++){const s=document.createElement('div');s.className='slot';grid.append(s)}

// ---- CharacterDialog + Character/Status/State/Skill pages ----
const char=layer('character-window');
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

// ---- OptionDialog, exact source background + controls ----
const opt=layer('option-window');
const optMeta=meta('Title.Lib',411); const optX=Math.round((1024-optMeta.size[0])/2), optY=Math.round((768-optMeta.size[1])/2);
image('Title.Lib',411,optX,optY,'ui-window',opt);
button('Prguse2.Lib',360,361,362,optX+optMeta.size[0]-26,optY+5,()=>hideWindow('option-window'),opt);
const toggleDefs=[
  // default Crystal settings represented by OptionPanel_BeforeDraw
  ['Prguse2.Lib',450,451,optX+159,optY+68],['Prguse2.Lib',455,454,optX+201,optY+68],
  ['Prguse2.Lib',458,457,optX+159,optY+93],['Prguse2.Lib',459,460,optX+201,optY+93],
  ['Prguse2.Lib',458,457,optX+159,optY+118],['Prguse2.Lib',459,460,optX+201,optY+118],
  ['Prguse2.Lib',458,457,optX+159,optY+143],['Prguse2.Lib',459,460,optX+201,optY+143],
  ['Prguse2.Lib',458,457,optX+159,optY+168],['Prguse2.Lib',459,460,optX+201,optY+168],
  ['Prguse2.Lib',464,463,optX+159,optY+193],['Prguse2.Lib',465,466,optX+201,optY+193],
  ['Prguse2.Lib',456,457,optX+159,optY+271],['Prguse2.Lib',461,460,optX+201,optY+271],
  ['Title.Lib',851,853,optX+159,optY+296],['Title.Lib',850,850,optX+201,optY+296],
];
toggleDefs.forEach(([l,n,p,x,y])=>button(l,n,null,p,x,y,null,opt));
image('Prguse2.Lib',468,optX+159,optY+225,'ui-img',opt);
image('Prguse.Lib',20,optX+155,optY+218,'ui-img',opt);
image('Prguse2.Lib',468,optX+159,optY+251,'ui-img',opt);
image('Prguse.Lib',20,optX+155,optY+244,'ui-img',opt);

// ---- MenuDialog, exact source geometry ----
const menu=layer('menu-window');
const menuMeta=meta('Title.Lib',567); const menuX=1024-menuMeta.size[0], menuY=mainY-menuMeta.size[1]+15;
image('Title.Lib',567,menuX,menuY,'ui-window',menu);
const menuButtons=[
  ['Title.Lib',633,634,635,3,12,'Exit'],['Title.Lib',636,637,638,3,31,'Logout'],
  ['Prguse.Lib',1970,1971,1972,3,50,'Help'],['Prguse.Lib',1973,1974,1975,3,69,'Keyboard'],
  ['Prguse.Lib',2000,2001,2002,3,88,'Ranking'],
  ['Prguse2.Lib',431,432,433,3,126,'Creatures'],['Prguse.Lib',1976,1977,1978,3,145,'Mount'],
  ['Prguse.Lib',1979,1980,1981,3,164,'Fishing'],['Prguse.Lib',1982,1983,1984,3,183,'Friends'],
  ['Prguse.Lib',1985,1986,1987,3,202,'Mentor'],['Prguse.Lib',1988,1989,1990,3,221,'Relationship'],
  ['Prguse.Lib',1991,1992,1993,3,240,'Group'],['Prguse.Lib',1994,1995,1996,3,259,'Guild'],
];
menuButtons.forEach(([l,n,h,p,x,y,name])=>button(l,n,h,p,menuX+x,menuY+y,()=>sourceNotice(`${name} dialog`),menu));

// ---- QuestDiaryDialog, the window actually opened by MainDialog QuestButton ----
const quest=layer('quest-window');
const questX=1024/2-300-20, questY=60;
image('Prguse.Lib',961,questX,questY,'ui-window',quest);
button('Title.Lib',193,194,195,questX+200,questY+436,()=>hideWindow('quest-window'),quest);
label('Quest Diary',questX+10,questY+8,210,'ui-label',quest);
label('0 / 20',questX+210,questY+7,null,'ui-label small',quest);

function showCharacter(mode){
  hideAllPrimary(); char.classList.remove('hidden'); charModeLabel.textContent='';
  if(mode==='character') charPage.src=src('Prguse.Lib',340);
  if(mode==='status') charPage.src=src('Title.Lib',506);
  if(mode==='state') charPage.src=src('Title.Lib',507);
  if(mode==='skills') { charPage.src=src('Title.Lib',508); charModeLabel.textContent=''; }
}
function sourceNotice(name){
  let n=document.getElementById('source-dialog-note');
  if(!n){n=label('',350,20,320,'ui-label');n.id='source-dialog-note';n.style.padding='7px 10px';n.style.background='rgba(0,0,0,.8)';n.style.textAlign='center'}
  n.textContent=`${name} — next exact Crystal source window`;n.style.display='block';clearTimeout(window.__note);window.__note=setTimeout(()=>n.style.display='none',1400);
}
