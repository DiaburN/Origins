// Reference-only runtime for Zircon nested/modal branches that depend on
// constructor arguments or live item/user data. Reference selectors live OUTSIDE
// the 1024x768 game desktop and therefore never masquerade as Zircon artwork.
//
// This layer also enforces a visual source rule for nested windows: whenever a
// control has literal LibraryFile + non-negative Index, the exact extracted PNG
// replaces generic HTML chrome. Runtime-only textures/data remain explicitly
// unrendered rather than being fabricated.

const stage = document.querySelector('#stage');
const topActions = document.querySelector('.top-actions');
let nestedSpecByClass = new Map();

const pad = value => String(value).padStart(5,'0');
const sourceAsset = (library,index) => `assets/${library}/${pad(index)}.png`;
function sourceLibrary(raw) {
  const match=String(raw??'').match(/LibraryFile\.([A-Za-z0-9_]+)/);
  return match?match[1]:null;
}
function sourceIndex(raw) {
  const match=String(raw??'').trim().match(/^-?\d+$/);
  return match?Number(match[0]):null;
}

const messageControl = document.createElement('label');
messageControl.className = 'reference-state-control';
messageControl.hidden = true;
messageControl.title = 'Reference-only selector for DXMessageBoxButtons source branches.';
messageControl.innerHTML = `
  <span>MessageBox source variant</span>
  <select id="messagebox-reference-variant">
    <option value="OK">OK</option>
    <option value="YesNo">Yes / No</option>
    <option value="Cancel">Cancel</option>
  </select>`;
topActions?.prepend(messageControl);
const messageSelect = messageControl.querySelector('select');

function suffix(element, name) {
  return String(element?.dataset?.controlName || '').endsWith(name);
}
function controlBySuffix(root,name) {
  return [...(root?.querySelectorAll?.('[data-control-name]')||[])].find(element=>suffix(element,name))||null;
}
function closeNested(root) {
  if (!root?.isConnected) return;
  root.remove();
  refreshReferenceControls();
}
function bindOnce(element,key,event,handler,options) {
  if (!element) return;
  const marker=`originsBound${key}`;
  if (element.dataset[marker]==='true') return;
  element.dataset[marker]='true';
  element.addEventListener(event,handler,options);
}

function applyIndexedSourceArtwork(root) {
  if (!root?.dataset?.nestedSourceClass) return;
  const item=nestedSpecByClass.get(root.dataset.nestedSourceClass);
  if (!item) return;
  let applied=0;
  for(const control of item.controls||[]) {
    const p=control.properties||{};
    const library=sourceLibrary(p.LibraryFile),index=sourceIndex(p.Index);
    if(!library||index===null||index<0) continue;
    if(control.type!=='DXButton'&&control.type!=='DXImageControl'&&control.type!=='DXAnimatedControl') continue;
    const target=root.querySelector(`[data-control-name="${CSS.escape(control.name)}"]`);
    if(!target) continue;
    const image=document.createElement('img');
    image.src=sourceAsset(library,index);image.draggable=false;image.className='nested-source-indexed-art';
    image.style.position='absolute';image.style.inset='0';image.style.width='100%';image.style.height='100%';
    image.style.pointerEvents='none';
    target.replaceChildren(image);
    target.classList.add('nested-source-indexed-control');
    target.dataset.sourceLibrary=library;target.dataset.sourceIndex=String(index);
    target.title=`${control.name}: ${library} #${index}`;
    applied++;
  }
  root.dataset.indexedSourceArtworkApplied=String(applied);
}

function applyMessageVariant(root, variant = messageSelect?.value || 'OK') {
  if (!root || root.dataset.nestedSourceClass !== 'DXMessageBox') return;
  root.dataset.sourceVariant = variant;
  const controls = [...root.querySelectorAll('[data-control-name]')];
  for (const element of controls) {
    let visible = true;
    if (suffix(element,'OKButton')) visible = variant === 'OK';
    if (suffix(element,'YesButton') || suffix(element,'NoButton')) visible = variant === 'YesNo';
    if (suffix(element,'CancelButton')) visible = variant === 'Cancel';
    element.style.display = visible ? '' : 'none';
  }
  root.dataset.runtimeMessage = 'constructor:string message';
  root.dataset.runtimeCaption = 'constructor:string caption';

  for(const name of ['OKButton','YesButton','NoButton','CancelButton']) {
    const button=controlBySuffix(root,name);
    bindOnce(button,`Message${name}`,'click',event=>{
      event.preventDefault();event.stopPropagation();closeNested(root);
    });
  }
  root.tabIndex=0;
  bindOnce(root,'MessageKeyboard','keydown',event=>{
    const current=root.dataset.sourceVariant||'OK';
    if(event.key==='Escape') {
      if(current==='OK'||current==='YesNo') { event.preventDefault();closeNested(root); }
    } else if(event.key==='Enter') {
      if(current==='OK'||current==='YesNo') { event.preventDefault();closeNested(root); }
    }
  });
}

function annotateInput(root) {
  if (!root || root.dataset.nestedSourceClass !== 'DXInputWindow') return;
  root.dataset.runtimeMessage = 'constructor:string message';
  root.dataset.runtimeCaption = 'constructor:string caption';
  root.dataset.runtimeValue = 'user input';

  const field=controlBySuffix(root,'ValueTextBox');
  if(field) {
    field.contentEditable='true';
    field.spellcheck=false;
    field.setAttribute('role','textbox');
    field.dataset.runtimeEditable='true';
    bindOnce(field,'InputValue','input',()=>{root.dataset.referenceInputValue=field.textContent||''});
    bindOnce(field,'InputKeyboard','keydown',event=>{
      if(event.key==='Enter') {event.preventDefault();closeNested(root)}
      else if(event.key==='Escape') {event.preventDefault();closeNested(root)}
    });
  }
  for(const name of ['ConfirmButton','CancelButton']) {
    const button=controlBySuffix(root,name);
    bindOnce(button,`Input${name}`,'click',event=>{event.preventDefault();event.stopPropagation();closeNested(root)});
  }
}

function annotateItemAmount(root) {
  if (!root || root.dataset.nestedSourceClass !== 'DXItemAmountWindow') return;
  root.dataset.runtimeCaption = 'constructor:string caption';
  root.dataset.runtimeItem = 'constructor:ClientUserItem item';
  root.dataset.runtimeAmountMax = 'item.Count';
  root.dataset.runtimeAmountChange = 'Math.Max(1, item.Count / 5)';
  const number = controlBySuffix(root,'AmountBox');
  if (number) {
    number.dataset.runtimeMaxValue = 'item.Count';
    number.dataset.runtimeChange = 'Math.Max(1,item.Count/5)';
    number.dataset.value='1';
    const field = number.querySelector('.dx-number-value');
    if (field) field.textContent = '1';
    // Without the constructor ClientUserItem there is no truthful MaxValue or
    // Change. Keep the source controls visible but deliberately non-interactive.
    number.querySelectorAll('.dx-number-up,.dx-number-down').forEach(button => {
      button.style.opacity = '.55';
      button.title = 'Requires runtime item.Count';
      button.style.pointerEvents = 'none';
    });
  }
  const itemCell = controlBySuffix(root,'ItemCell');
  if (itemCell) {
    itemCell.dataset.runtimeItemGrid = 'new[] { item }';
    itemCell.title = 'Runtime ClientUserItem from constructor';
  }
  const confirm=controlBySuffix(root,'ConfirmButton');
  bindOnce(confirm,'AmountConfirm','click',event=>{event.preventDefault();event.stopPropagation();closeNested(root)});
}

function numberValue(element) {
  const value=Number(element?.dataset?.value ?? 0);
  return Number.isFinite(value)?Math.max(0,Math.min(255,Math.round(value))):0;
}
function annotateColourPicker(root) {
  if (!root || root.dataset.nestedSourceClass !== 'DXColourPicker') return;
  root.dataset.runtimePaletteTexture='RenderingPipelineManager.GetColourPaletteTexture()';
  root.dataset.runtimeTarget='DXColourControl Target';
  root.dataset.runtimePaletteInvented='false';

  const red=controlBySuffix(root,'RedBox');
  const green=controlBySuffix(root,'GreenBox');
  const blue=controlBySuffix(root,'BlueBox');
  const colour=controlBySuffix(root,'ColourBox');
  const none=controlBySuffix(root,'NoColourLabel');
  const palette=controlBySuffix(root,'ColourScaleBox');
  const empty=controlBySuffix(root,'EmptyButton');

  for(const box of [red,green,blue].filter(Boolean)) {
    box.dataset.maxValue='255';
    box.dataset.change='5';
  }
  if(palette) {
    palette.dataset.runtimeTexture='RenderingPipelineManager.GetColourPaletteTexture()';
    palette.title='Runtime Zircon colour palette texture; no substitute artwork fabricated.';
  }
  // AllowNoColour belongs to the calling DXColourControl. New picker default is
  // false until Target/AllowNoColour is assigned, so the neutral reference hides it.
  if(empty) {
    empty.style.display='none';
    empty.dataset.runtimeVisibility='AllowNoColour';
  }

  const update=()=>{
    const r=numberValue(red),g=numberValue(green),b=numberValue(blue);
    root.dataset.selectedColour=`${r},${g},${b}`;
    if(colour) {
      colour.style.backgroundColor=`rgb(${r}, ${g}, ${b})`;
      colour.style.display='';
      colour.dataset.selectedColour=root.dataset.selectedColour;
    }
    if(none) none.style.display='none';
  };
  update();

  root._originsColourObserver?.disconnect?.();
  const rgb=[red,green,blue].filter(Boolean);
  const colourObserver=new MutationObserver(records=>{
    if(records.some(record=>record.type==='attributes'&&record.attributeName==='data-value')) update();
  });
  for(const box of rgb) colourObserver.observe(box,{attributes:true,attributeFilter:['data-value']});
  root._originsColourObserver=colourObserver;

  const select=controlBySuffix(root,'SelectButton');
  const cancel=controlBySuffix(root,'CancelButton');
  bindOnce(select,'ColourSelect','click',event=>{event.preventDefault();event.stopPropagation();closeNested(root)});
  bindOnce(cancel,'ColourCancel','click',event=>{event.preventDefault();event.stopPropagation();closeNested(root)});
  bindOnce(empty,'ColourEmpty','click',event=>{
    event.preventDefault();event.stopPropagation();
    root.dataset.selectedColour='transparent';
    if(colour) colour.style.display='none';
    if(none) none.style.display='';
  });
}

function initialiseNestedRoot(root) {
  applyIndexedSourceArtwork(root);
  applyMessageVariant(root);
  annotateInput(root);
  annotateItemAmount(root);
  annotateColourPicker(root);
}

function refreshReferenceControls() {
  const message = stage?.querySelector('[data-nested-source-class="DXMessageBox"]');
  messageControl.hidden = !message;
  if (message) applyMessageVariant(message);
}

messageSelect?.addEventListener('change', () => {
  const root = stage?.querySelector('[data-nested-source-class="DXMessageBox"]');
  if (root) applyMessageVariant(root, messageSelect.value);
});

const observer = new MutationObserver(records => {
  for (const record of records) {
    for (const node of record.addedNodes) {
      if (!(node instanceof Element)) continue;
      const roots = node.matches?.('.nested-source-window') ? [node] : [...node.querySelectorAll?.('.nested-source-window') || []];
      for (const root of roots) initialiseNestedRoot(root);
    }
  }
  refreshReferenceControls();
});
if (stage) observer.observe(stage,{childList:true,subtree:true});

fetch('ui-source-spec.json',{cache:'no-store'})
  .then(response=>{if(!response.ok)throw new Error(`ui-source-spec.json ${response.status}`);return response.json()})
  .then(spec=>{
    nestedSpecByClass=new Map((spec.nestedWindows||[]).map(item=>[item.sourceClass,item]));
    stage?.querySelectorAll('[data-nested-source-class]').forEach(initialiseNestedRoot);
    console.info(`ORIGINS nested source-art runtime: ${nestedSpecByClass.size} nested windows loaded`);
  })
  .catch(error=>console.error('Unable to load nested Zircon source-art manifest',error));

refreshReferenceControls();
