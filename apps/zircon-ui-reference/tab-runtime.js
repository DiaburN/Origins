import { gameSceneWindows } from './game-scene-windows.js';

const stage = document.querySelector('#stage');
const byId = new Map(gameSceneWindows.map(item => [item.id, item]));
const selectedByWindow = new WeakMap();
let sourceSpec = null;

const pad = value => String(value).padStart(5, '0');
const asset = (library, index) => `assets/${library}/${pad(index)}.png`;

function sourceWindowForRoot(root) {
  if (!sourceSpec || !(root instanceof Element) || !root.id?.startsWith('w-')) return null;
  const id = root.id.slice(2);
  const field = byId.get(id)?.field;
  return sourceSpec.windows?.find(window => window.field === field) || null;
}

function simpleParent(expression) {
  const value = String(expression ?? '').trim();
  return /^[A-Za-z_][A-Za-z0-9_]*$/.test(value) ? value : null;
}

function buildModel(window) {
  const controls = window.controls || [];
  const namedContainers = new Map();
  for (const control of controls) {
    if (!['DXTabControl','DXTab','DXConfigTab'].includes(control.type)) continue;
    if (!namedContainers.has(control.name)) namedContainers.set(control.name, control);
  }

  const tabGroups = new Map();
  for (const control of controls) {
    if (control.type !== 'DXTab' && control.type !== 'DXConfigTab') continue;
    const parent = simpleParent(control.properties?.Parent);
    if (!parent) continue;
    const tabControl = namedContainers.get(parent);
    if (!tabControl || tabControl.type !== 'DXTabControl') continue;
    if (!tabGroups.has(parent)) tabGroups.set(parent, []);
    tabGroups.get(parent).push(control.name);
  }

  return {controls, namedContainers, tabGroups};
}

function setTabSkin(element, selected) {
  if (!(element instanceof Element)) return;
  element.classList.toggle('selected', selected);
  element.classList.toggle('dx-button-SelectedTab', selected);
  element.classList.toggle('dx-button-DeselectedTab', !selected);
  const images = [...element.querySelectorAll(':scope > img')];
  if (images.length < 3) return;
  const indices = selected ? [56, 58, 57] : [53, 55, 54];
  for (let i = 0; i < 3; i++) images[i].src = asset('Interface', indices[i]);
}

function controlVisibleThroughTabs(control, model, selected) {
  let current = control;
  const visited = new Set();
  while (current) {
    const parentName = simpleParent(current.properties?.Parent);
    if (!parentName || parentName === 'this' || visited.has(parentName)) return true;
    visited.add(parentName);
    const parent = model.namedContainers.get(parentName);
    if (!parent) return true;
    if (parent.type === 'DXTab' || parent.type === 'DXConfigTab') {
      const tabControlName = simpleParent(parent.properties?.Parent);
      if (tabControlName && selected.get(tabControlName) !== parent.name) return false;
    }
    current = parent;
  }
  return true;
}

function applyWindowTabs(root, model, selected) {
  for (const element of root.querySelectorAll('[data-control-index]')) {
    const index = Number.parseInt(element.dataset.controlIndex || '', 10);
    if (!Number.isInteger(index)) continue;
    const control = model.controls[index];
    if (!control) continue;

    const isTab = control.type === 'DXTab' || control.type === 'DXConfigTab';
    if (isTab) {
      const tabControlName = simpleParent(control.properties?.Parent);
      setTabSkin(element, selected.get(tabControlName) === control.name);
    }

    element.hidden = !controlVisibleThroughTabs(control, model, selected);
  }
}

function initializeWindow(root) {
  if (!(root instanceof Element) || root.dataset.originsTabsInitialized === '1') return;
  const window = sourceWindowForRoot(root);
  if (!window) return;
  const model = buildModel(window);
  if (!model.tabGroups.size) {
    root.dataset.originsTabsInitialized = '1';
    return;
  }

  const selected = new Map();
  for (const [tabControlName, tabs] of model.tabGroups) {
    if (tabs.length) selected.set(tabControlName, tabs[0]);
  }
  selectedByWindow.set(root, {window, model, selected});
  root.dataset.originsTabsInitialized = '1';
  applyWindowTabs(root, model, selected);
}

function scan(node) {
  if (!(node instanceof Element)) return;
  if (node.matches('.window,.generic-window')) initializeWindow(node);
  node.querySelectorAll?.('.window,.generic-window').forEach(initializeWindow);
}

stage.addEventListener('click', event => {
  if (!(event.target instanceof Element)) return;
  const tabElement = event.target.closest('[data-control-type="DXTab"],[data-control-type="DXConfigTab"]');
  if (!tabElement) return;
  const root = tabElement.closest('.window,.generic-window');
  if (!root) return;
  initializeWindow(root);
  const state = selectedByWindow.get(root);
  if (!state) return;

  const index = Number.parseInt(tabElement.dataset.controlIndex || '', 10);
  const tab = Number.isInteger(index) ? state.model.controls[index] : null;
  if (!tab || (tab.type !== 'DXTab' && tab.type !== 'DXConfigTab')) return;
  const tabControlName = simpleParent(tab.properties?.Parent);
  if (!tabControlName || !state.model.tabGroups.get(tabControlName)?.includes(tab.name)) return;

  state.selected.set(tabControlName, tab.name);
  applyWindowTabs(root, state.model, state.selected);
  event.preventDefault();
  event.stopPropagation();
});

new MutationObserver(records => {
  for (const record of records) record.addedNodes.forEach(scan);
}).observe(stage, {childList: true, subtree: true});

fetch('ui-source-spec.json')
  .then(response => {
    if (!response.ok) throw new Error(`ui-source-spec.json ${response.status}`);
    return response.json();
  })
  .then(spec => {
    sourceSpec = spec;
    stage.querySelectorAll('.window,.generic-window').forEach(initializeWindow);
    const controls = spec.windows.flatMap(window => window.controls || []);
    const tabControls = controls.filter(control => control.type === 'DXTabControl').length;
    const tabs = controls.filter(control => control.type === 'DXTab' || control.type === 'DXConfigTab').length;
    console.info(`ORIGINS Zircon tab runtime: ${tabControls} tab controls / ${tabs} tabs`);
  })
  .catch(error => console.error('Unable to load Zircon tab manifest', error));
