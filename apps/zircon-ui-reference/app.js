const stage=document.querySelector('#stage');
const A={gi:i=>`assets/GameInter/${String(i).padStart(5,'0')}.png`,ui:i=>`assets/Interface/${String(i).padStart(5,'0')}.png`,mi:i=>`assets/MIcon/${String(i).padStart(5,'0')}.png`};
function img(src,x,y,cls='ui-img',parent=stage){const e=document.createElement('img');e.src=src;e.className=cls;e.style.left=`${x}px`;e.style.top=`${y}px`;parent.append(e);return e}
function label(text,x,y,w=0,parent=stage){const e=document.createElement('div');e.className='runtime-label';e.textContent=text;e.style.left=`${x}px`;e.style.top=`${y}px`;if(w){e.style.width=`${w}px`;e.style.textAlign='center'}parent.append(e);return e}

// MainPanel — source positions from Client/Scenes/Views/MainPanel.cs.
const mainY=700;img(A.gi(50),0,mainY);img(A.gi(51),17,mainY+3);
for(const [i,x,y] of [[52,35,22],[54,35,36],[58,35,50],[70,277,25],[71,277,45],[72,362,25],[73,362,45],[66,445,25],[65,445,45],[63,531,25],[62,541,45]])img(A.gi(i),x,mainY+y);
const buttons=[[82,650,'character'],[87,689,'inventory'],[92,728,'magic'],[112,767,'quest'],[97,806,null],[107,845,null],[102,884,null],[117,923,'menu'],[122,972,null]];
for(const [i,x,target] of buttons){const b=img(A.gi(i),x,mainY+(i===122?16:23),'ui-button');if(target)b.addEventListener('click',()=>openWindow(target))}
label('Wizard',300,mainY+20,60);label('50',300,mainY+40,60);label('55/100',385,mainY+20,60);label('1250',385,mainY+40,60);label('8-12',470,mainY+20,60);label('14-22',470,mainY+40,60);label('10-14',567,mainY+20,60);label('28-45',567,mainY+40,60);label('830 / 1000',82,mainY+18,125);label('710 / 1000',82,mainY+32,125);label('55 / 100',82,mainY+46,125);

// Default transparent chat windows configured by ChatOptionsDialog.CreateDefaultWindows().
const chat=document.createElement('div');chat.className='chat';chat.style.left='0';chat.style.top='432px';chat.style.width='493px';chat.style.height='150px';chat.innerHTML='Welcome to ORIGINS.<br><span style="color:#7fff7f">Zuma Temple</span><br>Crystal content + Zircon GameInter';stage.append(chat);
const system=document.createElement('div');system.className='chat';system.style.right='0';system.style.top='596px';system.style.width='350px';system.style.height='104px';system.innerHTML='System<br>Connection stable';stage.append(system);

// MiniMap is a reusable Zircon DXWindow. This reference keeps its exact default 200x200 footprint.
const mm=document.createElement('div');mm.className='minimap';mm.innerHTML='<div class="minimap-title">Zuma Temple</div><div class="minimap-body">MiniMap runtime image</div>';stage.append(mm);

// BeltDialog is resizable up to 10 cells; show the valid horizontal ten-cell configuration.
const belt=document.createElement('div');belt.className='belt';for(let i=0;i<10;i++){const s=document.createElement('div');s.className='belt-slot';s.textContent=(i+1)%10;belt.append(s)}stage.append(belt);

const windows={};
function addImageWindow(name,index,x,y,title){const root=document.createElement('div');root.className='window hidden';root.id=`w-${name}`;root.style.left=`${x}px`;root.style.top=`${y}px`;const bg=img(A.ui(index),0,0,'window-img',root);bg.addEventListener('load',()=>{root.style.width=`${bg.naturalWidth}px`;root.style.height=`${bg.naturalHeight}px`});const close=img(A.ui(15),0,0,'close',root);close.style.left='auto';close.addEventListener('click',()=>root.classList.add('hidden'));const t=document.createElement('div');t.className='window-title';t.textContent=title;root.append(t);stage.append(root);windows[name]=root;return root}

const character=addImageWindow('character',110,0,0,'Character');label('ORIGINS',97,52,137,character);label('Wizard',97,70,137,character);
const inventory=addImageWindow('inventory',130,760,200,'Inventory');img(A.gi(360),53,355,'ui-img',inventory);img(A.gi(364),180,384,'ui-button',inventory);img(A.gi(358),218,384,'ui-button',inventory);label('Gold',55,382,60,inventory);label('12,500',112,382,65,inventory);

const magic=addImageWindow('magic',161,605,110,'Magic');img(A.ui(164),0,66,'ui-img',magic);const icons=document.createElement('div');icons.className='magic-icons';for(const i of [0,8,10,14,18,20,30,38,40,44,52,64]){const e=document.createElement('img');e.src=A.mi(i);icons.append(e)}magic.append(icons);
const quest=addImageWindow('quest',291,146,80,'Quests');label('Current',24,55,80,quest);label('Zuma Temple',25,85,150,quest);label('Reach the King Room',25,103,180,quest);
const menu=addImageWindow('menu',279,872,440,'Menu');const mb=document.createElement('div');mb.className='menu-buttons';for(const text of ['Settings','Help','Guild','Storage','Ranking','Companion','Leave']){const e=document.createElement('div');e.textContent=text;mb.append(e)}menu.append(mb);

function openWindow(name){for(const [key,w] of Object.entries(windows))if(key!==name)w.classList.add('hidden');windows[name]?.classList.remove('hidden')}
document.querySelectorAll('[data-open]').forEach(b=>b.addEventListener('click',()=>openWindow(b.dataset.open)));
document.querySelector('[data-close-all]').addEventListener('click',()=>Object.values(windows).forEach(w=>w.classList.add('hidden')));
