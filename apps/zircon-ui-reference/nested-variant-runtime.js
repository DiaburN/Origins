// Reference-only runtime for Zircon nested/modal branches that depend on
// constructor arguments or live item/user data. Reference selectors live OUTSIDE
// the 1024x768 game desktop and therefore never masquerade as Zircon artwork.
//
// This layer also enforces a visual source rule for nested windows: whenever a
// control has literal LibraryFile + non-negative Index, the exact extracted PNG
// replaces generic HTML chrome. This currently fixes the six Interface1c class /
// gender buttons used by NewCharacterDialog.

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
}

function annotateInput(root) {
  if (!root || root.dataset.nestedSourceClass !== 'DXInputWindow') return;
  root.dataset.runtimeMessage = 'constructor:string message';
  root.dataset.runtimeCaption = 'constructor:string caption';
  root.dataset.runtimeValue = 'user input';
}

function annotateItemAmount(root) {
  if (!root || root.dataset.nestedSourceClass !== 'DXItemAmountWindow') return;
  root.dataset.runtimeCaption = 'constructor:string caption';
  root.dataset.runtimeItem = 'constructor:ClientUserItem item';
  root.dataset.runtimeAmountMax = 'item.Count';
  root.dataset.runtimeAmountChange = 'Math.Max(1, item.Count / 5)';
  const number = [...root.querySelectorAll('[data-control-name]')].find(el => suffix(el,'AmountBox'));
  if (number) {
    number.dataset.runtimeMaxValue = 'item.Count';
    number.dataset.runtimeChange = 'Math.Max(1,item.Count/5)';
    const field = number.querySelector('.dx-number-value');
    if (field) field.textContent = '1';
    number.querySelectorAll('.dx-number-up,.dx-number-down').forEach(button => {
      button.style.opacity = '.55';
      button.title = 'Requires runtime item.Count';
      button.style.pointerEvents = 'none';
    });
  }
  const itemCell = [...root.querySelectorAll('[data-control-name]')].find(el => suffix(el,'ItemCell'));
  if (itemCell) {
    itemCell.dataset.runtimeItemGrid = 'new[] { item }';
    itemCell.title = 'Runtime ClientUserItem from constructor';
  }
}

function initialiseNestedRoot(root) {
  applyIndexedSourceArtwork(root);
  applyMessageVariant(root);
  annotateInput(root);
  annotateItemAmount(root);
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
