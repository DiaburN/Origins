import { gameSceneWindows } from './game-scene-windows.js';
import { buildWindowLayout, getAssetSize } from './layout-resolver-derived.js';

const stage = document.querySelector('#stage');
const byId = new Map(gameSceneWindows.map(item => [item.id, item]));
const byField = new Map(gameSceneWindows.map(item => [item.field, item]));
let interactions = [];
let sourceSpec = null;
let nestedByClass = new Map();

const pad = value => String(value).padStart(5,'0');
const asset = (library,index) => `assets/${library}/${pad(index)}.png`;

function windowRoot(id) {
  return document.querySelector(`#w-${CSS.escape(id)}`);
}
function catalogButton(id) {
  return document.querySelector(`[data-window-id="${CSS.escape(id)}"]`);
}
function openWindowById(id) {
  const existing = windowRoot(id);
  if (existing) {
    existing.dispatchEvent(new CustomEvent('origins:focus', {bubbles: true}));
    return existing;
  }
  catalogButton(id)?.click();
  return windowRoot(id);
}
function applyInteraction(interaction) {
  const target = byField.get(interaction.targetField);
  if (!target) return;
  const existing = windowRoot(target.id);
  switch (interaction.action) {
    case 'open': openWindowById(target.id); break;
    case 'close': existing?.remove(); break;
    case 'toggle': existing ? existing.remove() : openWindowById(target.id); break;
  }
}
function sourceFieldFromRoot(root) {
  if (!(root instanceof Element) || !root.id?.startsWith('w-')) return null;
  const id = root.id.slice(2);
  return byId.get(id)?.field || root.dataset.sourceField || null;
}

function img(library,index,x,y,parent,className='ui-img') {
  const el=document.createElement('img');
  el.src=asset(library,index); el.className=className; el.draggable=false;
  el.style.position='absolute'; el.style.left=`${Math.round(x)}px`; el.style.top=`${Math.round(y)}px`;
  parent.append(el); return el;
}
function boolValue(raw,fallback=false) {
  const value=String(raw??'').trim().toLowerCase();
  return value==='true'?true:value==='false'?false:fallback;
}
function controlText(control) {
  if(control.resolvedText) return control.resolvedText;
  const p=control.properties||{};
  for(const key of ['Text','Label','Title']) {
    const raw=String(p[key]??'');
    const quoted=raw.match(/"([^"]*)"/); if(quoted) return quoted[1];
  }
  return '';
}

function buildNestedFrame(item,layout) {
  const [width,height]=layout.rootSize;
  const root=document.createElement('div');
  root.className='generic-window nested-source-window';
  root.id=`w-${item.id}`;
  root.dataset.sourceField=item.field;
  root.dataset.nestedSourceClass=item.sourceClass;
  root.style.position='absolute'; root.style.width=`${width}px`; root.style.height=`${height}px`;
  // DXKeyBindWindow.OnIsVisibleChanged centres against Config.GameSize. The
  // reference desktop is the locked 1024x768 Zircon desktop viewport.
  root.style.left=`${Math.round((1024-width)/2)}px`;
  root.style.top=`${Math.round((768-height)/2)}px`;

  const p=item.root||{};
  const hasTop=p.HasTopBorder===undefined?true:boolValue(p.HasTopBorder,true);
  const hasTitle=p.HasTitle===undefined?true:boolValue(p.HasTitle,true);
  const hasFooter=boolValue(p.HasFooter,false);
  const slimFooter=boolValue(p.SlimFooter,false);
  const topIndex=hasTop?0:2, leftCorner=hasTop?11:25, rightCorner=hasTop?12:26;
  const top=img('Interface',topIndex,0,0,root); top.style.width='100%';
  const left=img('Interface',1,0,7,root); left.style.height='calc(100% - 7px)';
  const right=img('Interface',1,Math.max(0,width-8),7,root); right.style.height='calc(100% - 7px)';
  if(hasTitle){
    const fill=img('Interface',3,8,7,root); fill.style.width=`${Math.max(0,width-16)}px`;
    img('Interface',4,0,34,root);
    const tr=img('Interface',5,0,34,root); tr.style.right='0'; tr.style.left='auto';
  }
  img('Interface',leftCorner,0,0,root);
  const tc=img('Interface',rightCorner,0,0,root); tc.style.right='0'; tc.style.left='auto';
  if(hasFooter||slimFooter){const f=img('Interface',126,0,0,root);f.style.bottom='0';f.style.top='auto';f.style.width='100%'}
  const bottom=img('Interface',2,0,Math.max(0,height-8),root);bottom.style.width='100%';
  img('Interface',8,0,Math.max(0,height-16),root);
  const br=img('Interface',9,0,Math.max(0,height-16),root);br.style.right='0';br.style.left='auto';

  const heading=document.createElement('div'); heading.className='generic-window-header';
  heading.textContent=item.resolvedText || item.sourceClass; root.append(heading);
  stage.append(root);
  root.dispatchEvent(new CustomEvent('origins:focus',{bubbles:true}));
  return root;
}

function renderNestedButton(control,node,root) {
  const p=control.properties||{};
  const width=node.width||80,height=node.height||20;
  const button=document.createElement('div'); button.className='dx-generated-button dx-button-Default';
  button.style.position='absolute';button.style.left=`${node.x}px`;button.style.top=`${node.y}px`;button.style.width=`${width}px`;button.style.height=`${height}px`;
  const parts=[16,18,17], ls=getAssetSize(sourceSpec,'Interface',parts[0])||[6,height], rs=getAssetSize(sourceSpec,'Interface',parts[2])||[6,height];
  img('Interface',parts[0],0,0,button);
  const mid=img('Interface',parts[1],ls[0],0,button);mid.style.width=`${Math.max(0,width-ls[0]-rs[0])}px`;mid.style.height=`${height}px`;
  img('Interface',parts[2],Math.max(0,width-rs[0]),0,button);
  const label=document.createElement('div');label.className='dx-button-label';label.textContent=controlText(control);button.append(label);
  button.dataset.controlName=control.name;button.dataset.controlType=control.type;root.append(button);
  if(/CancelButton$|CloseButton$/.test(control.name)) button.addEventListener('click',()=>root.remove());
  return button;
}

function renderNestedControl(control,node,root) {
  if(!node.visible) return null;
  if(control.type==='DXButton') return renderNestedButton(control,node,root);
  if(control.type==='DXLabel') {
    const el=document.createElement('div');el.className='runtime-label';el.textContent=controlText(control);
    el.style.position='absolute';el.style.left=`${node.x}px`;el.style.top=`${node.y}px`;el.style.width=`${node.width}px`;el.style.height=`${node.height}px`;root.append(el);return el;
  }
  if(control.type==='DXTreeControl'||control.sourceType==='KeyBindTree') {
    const el=document.createElement('div');el.className='dx-tree-control';el.style.position='absolute';el.style.left=`${node.x}px`;el.style.top=`${node.y}px`;el.style.width=`${node.width}px`;el.style.height=`${node.height}px`;el.style.border='1px solid rgb(93,70,37)';el.style.background='rgba(0,0,0,.45)';root.append(el);return el;
  }
  if(control.type==='DXTextBox'||control.type==='DXNumberTextBox') {
    const el=document.createElement('div');el.className='dx-textbox';el.style.position='absolute';el.style.left=`${node.x}px`;el.style.top=`${node.y}px`;el.style.width=`${node.width}px`;el.style.height=`${node.height}px`;root.append(el);return el;
  }
  const el=document.createElement('div');el.className=`dx-nested-control ${control.type}`;el.style.position='absolute';el.style.left=`${node.x}px`;el.style.top=`${node.y}px`;el.style.width=`${node.width}px`;el.style.height=`${node.height}px`;root.append(el);return el;
}

function openNestedByClass(className) {
  const item=nestedByClass.get(className); if(!item||!sourceSpec) return null;
  const existing=windowRoot(item.id);if(existing){existing.dispatchEvent(new CustomEvent('origins:focus',{bubbles:true}));return existing}
  const layout=buildWindowLayout(sourceSpec,item);
  const root=buildNestedFrame(item,layout);
  for(let i=0;i<(item.controls||[]).length;i++){
    const control=item.controls[i],node=layout.nodes[i];if(!node)continue;
    const el=renderNestedControl(control,node,root);if(el){el.dataset.controlIndex=String(i);el.dataset.controlName=control.name;el.dataset.controlType=control.type}
  }
  return root;
}

stage.addEventListener('click', event => {
  if (!(event.target instanceof Element)) return;
  const controlElement = event.target.closest('[data-control-name]');
  if (!controlElement) return;
  const root = controlElement.closest('.window,.generic-window');
  const sourceField = sourceFieldFromRoot(root);
  if (!sourceField) return;
  const control = controlElement.dataset.controlName;

  // DXConfigWindow source: KeyBindButton.MouseClick toggles KeyBindWindow.Visible.
  if(sourceField==='ConfigBox' && control==='KeyBindButton') {
    event.preventDefault();event.stopPropagation();
    const nested=nestedByClass.get('DXKeyBindWindow');
    if(nested && windowRoot(nested.id)) windowRoot(nested.id).remove(); else openNestedByClass('DXKeyBindWindow');
    return;
  }

  const interaction = interactions.find(item => item.sourceField === sourceField && item.control === control && item.event === 'MouseClick');
  if (!interaction) return;
  event.preventDefault(); event.stopPropagation(); applyInteraction(interaction);
});

fetch('ui-source-spec.json')
  .then(response => {if (!response.ok) throw new Error(`ui-source-spec.json ${response.status}`);return response.json()})
  .then(spec => {
    sourceSpec=spec;
    interactions=Array.isArray(spec.interactions)?spec.interactions:[];
    nestedByClass=new Map((spec.nestedWindows||[]).map(item=>[item.sourceClass,item]));
    console.info(`ORIGINS Zircon interaction runtime: ${interactions.length} direct links; ${nestedByClass.size} nested DXWindows available`);
  })
  .catch(error => console.error('Unable to load Zircon interaction manifest', error));
