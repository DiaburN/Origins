// Reference-only runtime for Zircon nested/modal branches that depend on
// constructor arguments or live item/user data. Controls added here live OUTSIDE
// the 1024x768 game desktop and therefore never masquerade as Zircon artwork.

const stage = document.querySelector('#stage');
const topActions = document.querySelector('.top-actions');

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
  // message/caption are constructor parameters, not static source text.
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
    if (field) field.textContent = '1'; // explicit source assignment: AmountBox.Value = 1.
    // Do not make up a count: leave increment/decrement inert in this neutral review.
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
      for (const root of roots) {
        applyMessageVariant(root);
        annotateInput(root);
        annotateItemAmount(root);
      }
    }
  }
  refreshReferenceControls();
});
if (stage) observer.observe(stage,{childList:true,subtree:true});
refreshReferenceControls();
