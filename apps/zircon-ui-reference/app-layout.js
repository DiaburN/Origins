import { gameSceneWindows, uiCategories } from './game-scene-windows.js';
import { buildWindowLayout, getAssetSize } from './layout-resolver.js';

const stage = document.querySelector('#stage');
const list = document.querySelector('#window-list');
const filters = document.querySelector('#category-filters');
const search = document.querySelector('#window-search');
const sourceStatus = document.querySelector('#source-status');
const selectionInfo = document.querySelector('#selection-info');

const pad = value => String(value).padStart(5, '0');
const asset = (library, index) => `assets/${library}/${pad(index)}.png`;
const windows = new Map();
let sourceSpec = null;
let activeCategory = 'all';

function image(src, x, y, className='ui-img', parent=stage) {
  const element = document.createElement('img');
  element.src = src;
  element.className = className;
  element.style.left = `${Math.round(x)}px`;
  element.style.top = `${Math.round(y)}px`;
  element.draggable = false;
  parent.append(element);
  return element;
}

function runtimeLabel(text, x, y, width=0, parent=stage) {
  const element = document.createElement('div');
  element.className = 'runtime-label';
  element.textContent = text;
  element.style.left = `${Math.round(x)}px`;
  element.style.top = `${Math.round(y)}px`;
  if (width) {
    element.style.width = `${Math.round(width)}px`;
    element.style.textAlign = 'center';
  }
  parent.append(element);
  return element;
}

function boolFrom(expression, fallback=false) {
  const value = String(expression ?? '').trim().toLowerCase();
  if (value === 'true') return true;
  if (value === 'false') return false;
  return fallback;
}

function libraryFrom(expression) {
  const match = String(expression ?? '').match(/LibraryFile\.([A-Za-z0-9_]+)/);
  return match ? match[1] : null;
}

function indexFrom(expression) {
  const match = String(expression ?? '').match(/\b(\d+)\b/);
  return match ? Number(match[1]) : null;
}

function sourceText(expression, fallback='') {
  if (!expression) return fallback;
  const quoted = String(expression).match(/"([^"]+)"/);
  if (quoted) return quoted[1];
  const language = String(expression).match(/CEnvir\.Language\.([A-Za-z0-9_]+)/);
  if (language) return language[1].replace(/([a-z])([A-Z])/g, '$1 $2');
  const label = String(expression).match(/Label\s*=\s*\{\s*Text\s*=\s*"([^"]+)"/);
  return label ? label[1] : fallback;
}

function buttonTypeFrom(expression, fallback='Default') {
  const match = String(expression ?? '').match(/ButtonType\.([A-Za-z0-9_]+)/);
  return match ? match[1] : fallback;
}

function cssColour(expression, fallback='#000') {
  const value = String(expression ?? '');
  if (/Color\.Black\b/.test(value)) return '#000';
  if (/Color\.White\b/.test(value)) return '#fff';
  if (/Constants\.WindowBackColour/.test(value)) return 'rgb(16,8,8)';
  if (/Constants\.RowBackColour/.test(value)) return 'rgb(25,20,0)';
  const match = value.match(/Color\.FromArgb\(\s*(?:\d+\s*,\s*)?(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)/);
  return match ? `rgb(${match[1]},${match[2]},${match[3]})` : fallback;
}

function literalPair(expression, type='Size') {
  const match = String(expression ?? '').match(new RegExp(`new\\s+${type}\\s*\\(\\s*(-?\\d+)\\s*,\\s*(-?\\d+)\\s*\\)`));
  return match ? [Number(match[1]), Number(match[2])] : null;
}

function removeTransientWindows() {
  stage.querySelectorAll('.window,.generic-window').forEach(element => element.remove());
  windows.clear();
  document.querySelectorAll('.catalog-item.active').forEach(element => element.classList.remove('active'));
}

// ---------------------------------------------------------------------------
// Permanent 1024x768 desktop HUD. These positions are literal MainPanel source
// coordinates and remain useful as a stable visual anchor while every dialog
// is reconstructed from the generated source manifest.
// ---------------------------------------------------------------------------
function buildDesktop() {
  stage.innerHTML = '';
  const mainY = 700;
  image(asset('GameInter', 50), 0, mainY);
  image(asset('GameInter', 51), 17, mainY + 3);
  for (const [index,x,y] of [[52,35,22],[54,35,36],[58,35,50],[70,277,25],[71,277,45],[72,362,25],[73,362,45],[66,445,25],[65,445,45],[63,531,25],[62,541,45]])
    image(asset('GameInter', index), x, mainY + y);

  const buttons = [
    [82,650,'character'], [87,689,'inventory'], [92,728,'magic'], [112,767,'quest'],
    [97,806,'communication'], [107,845,'belt'], [102,884,'group'], [117,923,'menu'], [122,972,'game-store'],
  ];
  for (const [index,x,target] of buttons) {
    const button = image(asset('GameInter', index), x, mainY + (index === 122 ? 16 : 23), 'ui-button');
    button.addEventListener('click', () => openWindow(target));
  }

  runtimeLabel('Wizard',300,mainY+20,60); runtimeLabel('50',300,mainY+40,60);
  runtimeLabel('55/100',385,mainY+20,60); runtimeLabel('1250',385,mainY+40,60);
  runtimeLabel('8-12',470,mainY+20,60); runtimeLabel('14-22',470,mainY+40,60);
  runtimeLabel('10-14',567,mainY+20,60); runtimeLabel('28-45',567,mainY+40,60);
  runtimeLabel('830 / 1000',82,mainY+18,125); runtimeLabel('710 / 1000',82,mainY+32,125); runtimeLabel('55 / 100',82,mainY+46,125);

  const chat = document.createElement('div');
  chat.className = 'chat';
  chat.style.left = '0'; chat.style.top = '432px'; chat.style.width = '493px'; chat.style.height = '150px';
  chat.innerHTML = 'Welcome to ORIGINS.<br><span style="color:#7fff7f">Zuma Temple</span><br>Zircon GameInter desktop reference';
  stage.append(chat);

  const system = document.createElement('div');
  system.className = 'chat';
  system.style.right = '0'; system.style.top = '596px'; system.style.width = '350px'; system.style.height = '104px';
  system.innerHTML = 'System<br>GameScene UI reference';
  stage.append(system);

  const minimap = document.createElement('div');
  minimap.className = 'minimap';
  minimap.innerHTML = '<div class="minimap-title">Zuma Temple</div><div class="minimap-body">MiniMap runtime content</div>';
  minimap.addEventListener('click', () => openWindow('big-map'));
  stage.append(minimap);

  const belt = document.createElement('div');
  belt.className = 'belt';
  for (let i=0;i<10;i++) {
    const cell = document.createElement('div');
    cell.className = 'belt-slot';
    cell.textContent = (i+1)%10;
    belt.append(cell);
  }
  stage.append(belt);
}

// ---------------------------------------------------------------------------
// Source-backed window chrome
// ---------------------------------------------------------------------------
function addImageWindow(name, library, index, x, y, width, height, title) {
  const root = document.createElement('div');
  root.className = 'window';
  root.id = `w-${name}`;
  root.style.left = `${Math.round(x)}px`;
  root.style.top = `${Math.round(y)}px`;
  root.style.width = `${Math.round(width)}px`;
  root.style.height = `${Math.round(height)}px`;
  const background = image(asset(library,index), 0, 0, 'window-img', root);
  background.style.width = `${Math.round(width)}px`;
  background.style.height = `${Math.round(height)}px`;
  const close = image(asset('Interface',15), Math.max(0,width-24), 3, 'close', root);
  close.addEventListener('click', () => root.remove());
  const heading = document.createElement('div');
  heading.className = 'window-title';
  heading.textContent = title;
  root.append(heading);
  stage.append(root);
  windows.set(name,root);
  return root;
}

function buildDxFrame(width, height, title, properties={}) {
  const root = document.createElement('div');
  root.className = 'generic-window';
  root.style.width = `${width}px`;
  root.style.height = `${height}px`;

  const hasTop = properties.HasTopBorder === undefined ? true : boolFrom(properties.HasTopBorder,true);
  const hasTitle = properties.HasTitle === undefined ? true : boolFrom(properties.HasTitle,true);
  const hasFooter = boolFrom(properties.HasFooter,false);
  const slimFooter = boolFrom(properties.SlimFooter,false);
  const topIndex = hasTop ? 0 : 2;
  const cornerLeft = hasTop ? 11 : 25;
  const cornerRight = hasTop ? 12 : 26;

  const top = image(asset('Interface',topIndex),0,0,'ui-img dx-window-stretch-x',root);
  top.style.width = '100%';
  const left = image(asset('Interface',1),0,7,'ui-img dx-window-side',root);
  left.style.height = `calc(100% - 7px)`;
  const right = image(asset('Interface',1),Math.max(0,width-8),7,'ui-img dx-window-side',root);
  right.style.height = `calc(100% - 7px)`;

  if (hasTitle) {
    const titleFill = image(asset('Interface',3),8,7,'ui-img dx-window-stretch-x',root);
    titleFill.style.width = `${Math.max(0,width-16)}px`;
    image(asset('Interface',4),0,34,'ui-img',root);
    const titleRight = image(asset('Interface',5),0,34,'ui-img',root);
    titleRight.style.right = '0'; titleRight.style.left = 'auto';
  }

  image(asset('Interface',cornerLeft),0,0,'ui-img',root);
  const topRight = image(asset('Interface',cornerRight),0,0,'ui-img',root);
  topRight.style.right = '0'; topRight.style.left = 'auto';

  if (hasFooter || slimFooter) {
    const footer = image(asset('Interface',126),0,0,'ui-img dx-window-stretch-x',root);
    footer.style.bottom = '0'; footer.style.top = 'auto'; footer.style.width = '100%';
  }

  const bottom = image(asset('Interface',2),0,Math.max(0,height-8),'ui-img dx-window-stretch-x',root);
  bottom.style.width = '100%';
  image(asset('Interface',8),0,Math.max(0,height-16),'ui-img',root);
  const bottomRight = image(asset('Interface',9),0,Math.max(0,height-16),'ui-img',root);
  bottomRight.style.right = '0'; bottomRight.style.left = 'auto';

  const heading = document.createElement('div');
  heading.className = 'generic-window-header';
  heading.textContent = title;
  root.append(heading);
  const close = image(asset('Interface',15),Math.max(0,width-24),3,'close',root);
  close.addEventListener('click', () => root.remove());
  return root;
}

function rootOverride(item) {
  if (item.id === 'character') return {library:'Interface',index:110};
  if (item.id === 'inspect') return {library:'Interface',index:115};
  return null;
}

function effectiveItem(item) {
  const override = rootOverride(item);
  if (!override) return item;
  return {
    ...item,
    root: {
      ...(item.root || {}),
      LibraryFile: `LibraryFile.${override.library}`,
      Index: String(override.index),
    },
  };
}

// ---------------------------------------------------------------------------
// Reusable Zircon control chrome
// ---------------------------------------------------------------------------
const buttonParts = {
  Default:[16,18,17],
  SelectedTab:[56,58,57],
  DeselectedTab:[53,55,54],
  SmallButton:[41,43,42],
};
const singleButtonPart = {AddButton:241,RemoveButton:242,LFGButton:243,OptionsButton:245};

function renderGeneratedButton(text,x,y,width,height,type,parent) {
  const root = document.createElement('div');
  root.className = `dx-generated-button dx-button-${type}`;
  root.style.left = `${x}px`; root.style.top = `${y}px`; root.style.width = `${width}px`; root.style.height = `${height}px`;
  parent.append(root);

  if (singleButtonPart[type] !== undefined) {
    image(asset('Interface',singleButtonPart[type]),0,0,'ui-img',root);
  } else {
    const [leftIndex,middleIndex,rightIndex] = buttonParts[type] || buttonParts.Default;
    const leftSize = getAssetSize(sourceSpec,'Interface',leftIndex) || [6,height];
    const rightSize = getAssetSize(sourceSpec,'Interface',rightIndex) || [6,height];
    image(asset('Interface',leftIndex),0,0,'ui-img',root);
    const middle = image(asset('Interface',middleIndex),leftSize[0],0,'ui-img dx-button-middle',root);
    middle.style.width = `${Math.max(0,width-leftSize[0]-rightSize[0])}px`;
    middle.style.height = `${Math.max(height,leftSize[1],rightSize[1])}px`;
    image(asset('Interface',rightIndex),Math.max(0,width-rightSize[0]),0,'ui-img',root);
  }

  if (text) {
    const label = document.createElement('div');
    label.className = 'dx-button-label';
    label.textContent = text;
    root.append(label);
  }
  return root;
}

function renderCheckBox(control,node,parent) {
  const p = control.properties || {};
  const text = sourceText(p.Label || p.Text, control.name);
  const checked = boolFrom(p.Checked,false);
  const root = document.createElement('div');
  root.className = 'dx-checkbox';
  root.style.left = `${node.x}px`; root.style.top = `${node.y}px`;
  const label = document.createElement('span'); label.textContent = text; root.append(label);
  const box = document.createElement('img'); box.src = asset('GameInter',checked?162:161); box.draggable = false; root.append(box);
  root.addEventListener('click',()=>{const on=box.src.endsWith('/00162.png');box.src=asset('GameInter',on?161:162)});
  parent.append(root);
  return root;
}

function renderScrollBar(control,node,parent,skin={}) {
  const vertical = skin.vertical ?? control.type === 'DXVScrollBar';
  const up = skin.up ?? 44, down = skin.down ?? 46, thumb = skin.thumb ?? 45, background = skin.background ?? null;
  const root = document.createElement('div');
  root.className = `dx-scrollbar ${vertical?'vertical':'horizontal'}`;
  root.style.left = `${node.x}px`; root.style.top = `${node.y}px`; root.style.width = `${node.width}px`; root.style.height = `${node.height}px`;
  parent.append(root);
  if (background !== null) {
    const bg = image(asset('Interface',background),1,0,'ui-img dx-scroll-bg',root);
    if (vertical) bg.style.height = '100%'; else bg.style.width = '100%';
  }
  if (vertical) {
    image(asset('Interface',up),1,1,'ui-img',root);
    image(asset('Interface',down),1,Math.max(1,node.height-13),'ui-img',root);
    image(asset('Interface',thumb),1,16,'ui-img dx-scroll-thumb',root);
  } else {
    image(asset('Interface',up),1,1,'ui-img',root);
    image(asset('Interface',down),Math.max(1,node.width-13),1,'ui-img',root);
    image(asset('Interface',thumb),16,1,'ui-img dx-scroll-thumb',root);
  }
  return root;
}

function renderTextBox(control,node,parent) {
  const p = control.properties || {};
  const element = document.createElement('div');
  element.className = 'dx-textbox';
  element.style.left = `${node.x}px`; element.style.top = `${node.y}px`; element.style.width = `${node.width}px`; element.style.height = `${node.height}px`;
  element.textContent = sourceText(p.Text,'');
  parent.append(element);
  return element;
}

function renderNumberBox(node,parent) {
  const root = document.createElement('div');
  root.className = 'dx-numberbox';
  root.style.left = `${node.x}px`; root.style.top = `${node.y}px`; root.style.width = `${node.width}px`; root.style.height = `${node.height}px`;
  parent.append(root);
  image(asset('GameInter',1011),0,1,'ui-button',root);
  const field = document.createElement('div');
  field.className = 'dx-textbox'; field.style.left = '19px'; field.style.top = '1px'; field.style.width = '50px'; field.style.height = '20px'; field.textContent = '0';
  root.append(field);
  image(asset('GameInter',1010),Math.max(0,node.width-17),1,'ui-button',root);
  return root;
}

function renderStructuralControl(control,node,parent) {
  const p = control.properties || {};
  const shouldDraw = boolFrom(p.DrawTexture,false) || boolFrom(p.Border,false) || p.BackColour !== undefined;
  if (!shouldDraw) return null;
  const element = document.createElement('div');
  element.className = 'dx-structural-control';
  element.style.left = `${node.x}px`; element.style.top = `${node.y}px`; element.style.width = `${node.width}px`; element.style.height = `${node.height}px`;
  element.style.background = cssColour(p.BackColour,'transparent');
  if (boolFrom(p.Border,false)) element.classList.add('with-border');
  parent.append(element);
  return element;
}

function renderComboBox(control,node,parent) {
  const p = control.properties || {};
  const root = document.createElement('div');
  root.className = 'dx-combobox';
  root.style.left = `${node.x}px`; root.style.top = `${node.y}px`; root.style.width = `${node.width}px`; root.style.height = `${node.height}px`;
  const text = document.createElement('span'); text.textContent = sourceText(p.Text,''); root.append(text);
  const arrowSize = getAssetSize(sourceSpec,'GameInter',795) || [16,16];
  image(asset('GameInter',795),Math.max(0,node.width-arrowSize[0]),0,'ui-button',root);
  parent.append(root);
  return root;
}

function renderColourControl(control,node,parent) {
  const p = control.properties || {};
  const element = document.createElement('div');
  element.className = 'dx-colour-control';
  element.style.left = `${node.x}px`; element.style.top = `${node.y}px`; element.style.width = `${node.width}px`; element.style.height = `${node.height}px`;
  element.style.background = cssColour(p.BackColour,'#000');
  parent.append(element);
  return element;
}

function renderListBox(control,node,parent) {
  const root = document.createElement('div');
  root.className = 'dx-listbox';
  root.style.left = `${node.x}px`; root.style.top = `${node.y}px`; root.style.width = `${node.width}px`; root.style.height = `${node.height}px`;
  parent.append(root);
  renderScrollBar({type:'DXVScrollBar'},{x:Math.max(0,node.width-14),y:0,width:14,height:node.height},root);
  return root;
}

function renderSoundBar(node,parent) {
  const root = document.createElement('div');
  root.className = 'dx-soundbar';
  root.style.left = `${node.x}px`; root.style.top = `${node.y}px`; root.style.width = `${node.width}px`; root.style.height = `${node.height}px`;
  parent.append(root);
  image(asset('GameInter',4741),0,1,'ui-button',root);
  image(asset('GameInter',4743),20,3,'ui-img',root);
  const inner = image(asset('GameInter',4742),22,5,'ui-img dx-sound-inner',root); inner.style.clipPath = 'inset(0 35% 0 0)';
  image(asset('GameInter',4746),Math.max(100,node.width-18),1,'ui-button',root);
  return root;
}

function renderTreeControl(control,node,parent) {
  const root = document.createElement('div');
  root.className = 'dx-tree-control';
  root.style.left = `${node.x}px`; root.style.top = `${node.y}px`; root.style.width = `${node.width}px`; root.style.height = `${node.height}px`;
  const rows = document.createElement('div'); rows.className = 'dx-tree-runtime'; rows.textContent = 'Tree rows: runtime data'; root.append(rows);
  parent.append(root);
  renderScrollBar({type:'DXVScrollBar'},{x:Math.max(0,node.width-18),y:0,width:18,height:node.height},root,{up:61,down:62,thumb:60,background:59});
  return root;
}

function renderItemGrid(control,node,parent) {
  const p = control.properties || {};
  const gridSize = literalPair(p.GridSize,'Size') || [Math.max(1,Math.round(node.width/36)),Math.max(1,Math.round(node.height/36))];
  const root = document.createElement('div');
  root.className = 'generic-control generic-grid';
  root.style.left = `${node.x}px`; root.style.top = `${node.y}px`; root.style.width = `${node.width}px`; root.style.height = `${node.height}px`;
  root.style.gridTemplateColumns = `repeat(${gridSize[0]},36px)`;
  for (let i=0;i<gridSize[0]*gridSize[1];i++) {
    const cell = document.createElement('div'); cell.className = 'generic-cell'; root.append(cell);
  }
  parent.append(root);
  return root;
}

function renderTabButton(control,node,parent) {
  if (!node.tabButton) return null;
  const p = control.properties || {};
  const text = sourceText(p.TabButton || p.Label || p.Text, control.name.replace(/Tab$/,''));
  const tab = node.tabButton;
  const type = tab.selected ? 'SelectedTab' : 'DeselectedTab';
  const button = renderGeneratedButton(text,tab.x,tab.y,tab.width,tab.height,type,parent);
  button.classList.add('dx-tab-button');
  return button;
}

function renderControl(node,root) {
  if (!node.visible && node.type !== 'DXTab' && node.type !== 'DXConfigTab') return null;
  const control = node.control;
  const p = control.properties || {};
  const library = libraryFrom(p.LibraryFile);
  const index = indexFrom(p.Index);

  if ((control.type === 'DXImageControl' || control.type === 'DXAnimatedControl') && library && index !== null) {
    const element = image(asset(library,index),node.x,node.y,'ui-img',root);
    element.style.width = `${node.width}px`; element.style.height = `${node.height}px`;
    element.title = `${control.name}: ${control.type}`;
    return element;
  }

  switch (control.type) {
    case 'DXButton':
      if (library && index !== null) {
        const element = image(asset(library,index),node.x,node.y,'ui-button',root);
        element.style.width = `${node.width}px`; element.style.height = `${node.height}px`; element.title = `${control.name}: DXButton`;
        return element;
      }
      return renderGeneratedButton(sourceText(p.Label || p.Text,control.name),node.x,node.y,node.width,node.height,buttonTypeFrom(p.ButtonType),root);
    case 'DXLabel': {
      const element = runtimeLabel(sourceText(p.Text,control.name),node.x,node.y,node.width,root);
      element.classList.add('dx-label');
      return element;
    }
    case 'DXCheckBox': return renderCheckBox(control,node,root);
    case 'DXItemCell': {
      const element = document.createElement('div'); element.className = 'dx-item-cell';
      element.style.left = `${node.x}px`; element.style.top = `${node.y}px`; element.style.width = `${node.width}px`; element.style.height = `${node.height}px`; element.title = control.name;
      root.append(element); return element;
    }
    case 'DXItemGrid': return renderItemGrid(control,node,root);
    case 'DXControl': return renderStructuralControl(control,node,root);
    case 'DXTab': case 'DXConfigTab': return renderTabButton(control,node,root);
    case 'DXTabControl': return null;
    case 'DXVScrollBar': case 'DXHScrollBar': return renderScrollBar(control,node,root);
    case 'DXTextBox': case 'DXNumberTextBox': return renderTextBox(control,node,root);
    case 'DXNumberBox': return renderNumberBox(node,root);
    case 'DXComboBox': return renderComboBox(control,node,root);
    case 'DXColourControl': return renderColourControl(control,node,root);
    case 'DXListBox': return renderListBox(control,node,root);
    case 'DXSoundBar': return renderSoundBar(node,root);
    case 'DXTreeControl': return renderTreeControl(control,node,root);
    case 'DXKeyBindWindow': return null;
    default: {
      const element = document.createElement('div'); element.className = 'generic-control unknown-control';
      element.style.left = `${node.x}px`; element.style.top = `${node.y}px`; element.style.width = `${node.width}px`; element.style.height = `${node.height}px`;
      element.textContent = `UNMAPPED ${control.type}`; root.append(element); return element;
    }
  }
}

// ---------------------------------------------------------------------------
// Complete source-driven dialog renderer
// ---------------------------------------------------------------------------
function renderSourceWindow(rawItem) {
  const item = effectiveItem(rawItem);
  const layout = buildWindowLayout(sourceSpec,item);
  const [width,height] = layout.rootSize;
  const preferred = literalPair(item.defaultLocationExpression,'Point') || literalPair(item.root?.Location,'Point') || [Math.max(0,(1024-width)/2),Math.max(0,(700-height)/2)];
  const rootLibrary = libraryFrom(item.root?.LibraryFile);
  const rootIndex = indexFrom(item.root?.Index);
  const rootAssetSize = getAssetSize(sourceSpec,rootLibrary,rootIndex);
  let root;

  if (rootLibrary && rootIndex !== null && rootAssetSize) {
    root = addImageWindow(item.id,rootLibrary,rootIndex,preferred[0],preferred[1],width,height,item.sourceClass || item.class || item.id);
  } else {
    root = buildDxFrame(width,height,item.sourceClass || item.class || item.id,item.root || {});
    root.id = `w-${item.id}`;
    root.style.left = `${preferred[0]}px`; root.style.top = `${preferred[1]}px`;
    stage.append(root); windows.set(item.id,root);
  }

  for (const node of layout.nodes) renderControl(node,root);

  const badge = document.createElement('div');
  badge.className = 'generic-source-badge';
  badge.textContent = `${item.sourcePath || 'source unresolved'} · ${layout.nodes.length} controls`;
  root.append(badge);

  // Runtime values are deliberately overlays; these never alter source PNGs.
  if (item.id === 'character' || item.id === 'inspect') {
    runtimeLabel('ORIGINS',97,52,137,root); runtimeLabel('Wizard',97,70,137,root);
  }
  if (item.id === 'inventory') {
    runtimeLabel('12,500',112,382,65,root);
  }
  if (item.id === 'quest') {
    runtimeLabel('Zuma Temple',25,85,150,root); runtimeLabel('Reach the King Room',25,103,180,root);
  }
  if (item.id === 'magic') {
    const icons = document.createElement('div'); icons.className = 'magic-icons';
    for (const icon of [0,8,10,14,18,20,30,38,40,44,52,64]) { const element=document.createElement('img'); element.src=asset('MagicIcon',icon); icons.append(element); }
    root.append(icons);
  }

  placeIfOffscreen(root);
  return root;
}

function placeIfOffscreen(root) {
  requestAnimationFrame(() => {
    const width = root.offsetWidth || 350, height = root.offsetHeight || 300;
    let x = Number.parseInt(root.style.left,10) || 0, y = Number.parseInt(root.style.top,10) || 0;
    if (x + width > 1024) x = Math.max(0,1024-width);
    if (y + height > 700) y = Math.max(0,700-height);
    root.style.left = `${x}px`; root.style.top = `${y}px`;
  });
}

function itemById(id) {
  return sourceSpec?.windows?.find(item => item.id === id || item.field === gameSceneWindows.find(base => base.id === id)?.field) || gameSceneWindows.find(item => item.id === id);
}

function openWindow(id) {
  if (['main-panel','belt','minimap','buffs','group-health','timer'].includes(id)) {
    selectionInfo.textContent = `${id}: persistent/default GameScene HUD component.`;
    return;
  }
  removeTransientWindows();
  const item = itemById(id);
  if (!item) return;
  const base = gameSceneWindows.find(entry => entry.field === item.field) || {};
  const enriched = {...base,...item,id,sourceClass:item.class || base.sourceClass};
  renderSourceWindow(enriched);
  document.querySelector(`[data-window-id="${id}"]`)?.classList.add('active');
  selectionInfo.textContent = `${enriched.field} / ${enriched.sourceClass || enriched.class} — ${enriched.sourcePath || 'registry only'}`;
}

function mergeSpec(raw) {
  const byField = new Map((raw.windows || []).map(window => [window.field,window]));
  return gameSceneWindows.map(base => ({...base,...(byField.get(base.field) || {}),id:base.id,sourceClass:(byField.get(base.field) || {}).class || base.sourceClass}));
}

async function loadSpec() {
  try {
    const response = await fetch('ui-source-spec.json',{cache:'no-store'});
    if (!response.ok) throw new Error(response.statusText);
    const raw = await response.json();
    sourceSpec = {...raw,windows:mergeSpec(raw)};
    const sizeLibraries = Object.keys(raw.assetSizes || {}).length;
    sourceStatus.textContent = `${raw.windowCount || sourceSpec.windows.length} GameScene entries · source geometry resolver active · ${sizeLibraries} asset-size libraries`;
  } catch (error) {
    sourceSpec = {windows:gameSceneWindows,assetSizes:{}};
    sourceStatus.textContent = `static registry only (${gameSceneWindows.length}); generated source spec unavailable`;
  }
  renderCatalog();
}

function renderCatalog() {
  list.innerHTML = '';
  const query = search.value.trim().toLowerCase();
  const items = (sourceSpec?.windows || gameSceneWindows).filter(item =>
    (activeCategory === 'all' || item.category === activeCategory) &&
    (!query || `${item.id} ${item.field} ${item.sourceClass || item.class}`.toLowerCase().includes(query))
  );
  for (const category of uiCategories) {
    const categoryItems = items.filter(item => item.category === category);
    if (!categoryItems.length) continue;
    const group = document.createElement('div'); group.className = 'catalog-group';
    const heading = document.createElement('div'); heading.className = 'catalog-group-title'; heading.textContent = `${category} (${categoryItems.length})`; group.append(heading);
    for (const item of categoryItems) {
      const button = document.createElement('button');
      button.className = 'catalog-item'; button.dataset.windowId = item.id;
      button.innerHTML = `${item.id}<small>${item.field} · ${item.sourceClass || item.class}</small>`;
      button.addEventListener('click',()=>openWindow(item.id));
      group.append(button);
    }
    list.append(group);
  }
}

function buildFilters() {
  for (const category of ['all',...uiCategories]) {
    const button = document.createElement('button');
    button.textContent = category; button.dataset.category = category;
    if (category === 'all') button.classList.add('active');
    button.addEventListener('click',()=>{
      activeCategory = category;
      filters.querySelectorAll('button').forEach(element => element.classList.toggle('active',element === button));
      renderCatalog();
    });
    filters.append(button);
  }
}

document.querySelector('[data-close-all]').addEventListener('click',()=>{removeTransientWindows();selectionInfo.textContent='All transient Zircon windows closed.'});
document.querySelector('#reset-layout').addEventListener('click',()=>{buildDesktop();selectionInfo.textContent='Zircon desktop reset.'});
search.addEventListener('input',renderCatalog);

buildFilters();
buildDesktop();
loadSpec();
