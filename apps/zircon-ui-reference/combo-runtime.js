const stage = document.querySelector('#stage');
let sourceSpec = null;

const sourceInt = (expression, fallback) => {
  const value = String(expression ?? '').trim();
  return /^-?\d+$/.test(value) ? Number(value) : fallback;
};

const sourceBool = (expression, fallback = false) => {
  const value = String(expression ?? '').trim().toLowerCase();
  if (value === 'true') return true;
  if (value === 'false') return false;
  return fallback;
};

function sourceWindowForRoot(root) {
  if (!sourceSpec || !(root instanceof Element)) return null;
  const field = root.dataset.sourceField;
  if (!field) return null;
  return [...(sourceSpec.windows || []), ...(sourceSpec.nestedWindows || [])]
    .find(window => window.field === field) || null;
}

function restoreCombo(root, control) {
  if (!(root instanceof Element) || root.dataset.originsComboInitialized === '1') return;
  const properties = control?.properties || {};
  const normalHeight = Math.max(1, sourceInt(properties.NormalHeight, 16));
  const dropDownHeight = Math.max(normalHeight, sourceInt(properties.DropDownHeight, 123));
  const arrow = root.querySelector(':scope > img.ui-button');
  const selectedLabel = root.querySelector(':scope > span');

  root.dataset.originsComboInitialized = '1';
  root.dataset.sourceNormalHeight = String(normalHeight);
  root.dataset.sourceDropDownHeight = String(dropDownHeight);
  root.dataset.runtimeOptions = 'DXListBoxItem controls supplied by game/runtime';
  root.dataset.sourceListParent = 'ActiveScene';
  root.dataset.sourceSort = String(sourceBool(properties.Sort, true));
  root.style.background = 'transparent';
  root.style.border = '1px solid #c6a663';
  root.style.overflow = 'visible';

  if (selectedLabel) {
    selectedLabel.style.position = 'absolute';
    selectedLabel.style.left = '0';
    selectedLabel.style.top = '-1px';
    selectedLabel.style.height = `${normalHeight}px`;
    selectedLabel.style.lineHeight = `${normalHeight}px`;
    selectedLabel.style.color = '#fff';
    selectedLabel.style.whiteSpace = 'nowrap';
    selectedLabel.style.overflow = 'hidden';
    selectedLabel.style.textOverflow = 'ellipsis';
    selectedLabel.style.padding = '0 2px';
  }

  const arrowWidth = Math.max(1, arrow?.naturalWidth || arrow?.width || 16);
  const arrowHeight = Math.max(1, arrow?.naturalHeight || arrow?.height || 16);
  if (selectedLabel) selectedLabel.style.width = `${Math.max(0, root.clientWidth - 3 - arrowHeight)}px`;
  if (arrow) {
    arrow.style.left = `${Math.max(0, root.clientWidth - arrowWidth)}px`;
    arrow.style.top = `${Math.max(0, Math.trunc((normalHeight - arrowHeight) / 2))}px`;
    arrow.dataset.sourceLibrary = 'GameInter';
    arrow.dataset.sourceIndex = '795';
  }

  let showing = sourceBool(properties.Showing, false);
  const applyShowing = () => {
    // DXComboBox.OnShowingChanged uses:
    // min(ListBox.ScrollBar.MaxValue + NormalHeight + 2, DropDownHeight).
    // The neutral reference deliberately has no fabricated runtime rows, so
    // MaxValue is zero and an opened empty combo grows by exactly two pixels.
    const height = showing ? Math.min(normalHeight + 2, dropDownHeight) : normalHeight;
    root.style.height = `${height}px`;
    root.dataset.sourceShowing = String(showing);
    root.dataset.sourceNeutralListHeight = String(Math.max(0, height - normalHeight - 2));
    root.classList.toggle('showing', showing);
  };

  applyShowing();

  if (arrow) {
    arrow.addEventListener('click', event => {
      showing = !showing;
      applyShowing();
      event.preventDefault();
      event.stopPropagation();
    });
  }
}

function initializeWindow(root) {
  if (!(root instanceof Element)) return;
  const window = sourceWindowForRoot(root);
  if (!window) return;
  const controls = window.controls || [];
  for (const element of root.querySelectorAll('[data-control-type="DXComboBox"][data-control-index]')) {
    const index = Number.parseInt(element.dataset.controlIndex || '', 10);
    if (!Number.isInteger(index)) continue;
    const control = controls[index];
    if (control?.type !== 'DXComboBox') continue;
    restoreCombo(element, control);
  }
}

function scan(node) {
  if (!(node instanceof Element)) return;
  if (node.matches('.window,.generic-window')) queueMicrotask(() => initializeWindow(node));
  node.querySelectorAll?.('.window,.generic-window').forEach(root => queueMicrotask(() => initializeWindow(root)));
}

new MutationObserver(records => {
  for (const record of records) record.addedNodes.forEach(scan);
}).observe(stage, { childList: true, subtree: true });

fetch('ui-source-spec.json', { cache: 'no-store' })
  .then(response => {
    if (!response.ok) throw new Error(`ui-source-spec.json ${response.status}`);
    return response.json();
  })
  .then(spec => {
    sourceSpec = spec;
    stage.querySelectorAll('.window,.generic-window').forEach(initializeWindow);
    const combos = [...(spec.windows || []), ...(spec.nestedWindows || [])]
      .flatMap(window => window.controls || [])
      .filter(control => control.type === 'DXComboBox').length;
    console.info(`ORIGINS Zircon DXComboBox runtime active: ${combos} source combo boxes; runtime options remain neutral until supplied by game data`);
  })
  .catch(error => console.error('Unable to load Zircon combo manifest', error));
