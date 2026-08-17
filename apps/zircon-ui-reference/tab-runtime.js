import { gameSceneWindows } from './game-scene-windows.js';

const stage = document.querySelector('#stage');
const guildStateSelect = document.querySelector('#guild-reference-state');
const guildStateControl = guildStateSelect?.closest('.reference-state-control');
const byId = new Map(gameSceneWindows.map(item => [item.id, item]));
const selectedByWindow = new WeakMap();
let sourceSpec = null;
let guildReferenceState = guildStateSelect?.value || 'noGuild';

const pad = value => String(value).padStart(5, '0');
const asset = (library, index) => `assets/${library}/${pad(index)}.png`;

const GUILD_STATE_TABS = {
  noGuild: new Set(['CreateTab']),
  hasGuild: new Set(['HomeTab', 'MemberTab', 'StorageTab', 'WarTab', 'StyleTab']),
  ownsCastle: new Set(['HomeTab', 'MemberTab', 'StorageTab', 'WarTab', 'StyleTab', 'CastleTab']),
};

function sourceWindowForRoot(root) {
  if (!sourceSpec || !(root instanceof Element) || !root.id?.startsWith('w-')) return null;
  const id = root.id.slice(2);
  const field = byId.get(id)?.field;
  return sourceSpec.windows?.find(window => window.field === field) || null;
}

function comboSourceWindowForRoot(root) {
  if (!sourceSpec || !(root instanceof Element)) return null;
  const field = root.dataset.sourceField;
  if (!field) return null;
  return [...(sourceSpec.windows || []), ...(sourceSpec.nestedWindows || [])]
    .find(window => window.field === field) || null;
}

function simpleParent(expression) {
  const value = String(expression ?? '').trim();
  return /^[A-Za-z_][A-Za-z0-9_]*$/.test(value) ? value : null;
}

function isGuildTopLevelTab(control, window) {
  return window?.field === 'GuildBox' &&
    (control?.type === 'DXTab' || control?.type === 'DXConfigTab') &&
    simpleParent(control?.properties?.Parent) === 'GuildTabs';
}

function sourceVisible(control, window) {
  if (!control) return false;

  // This selector is a reference-only projection of states already encoded in
  // GuildDialog.ClearGuild()/GuildInfoChanged. It never invents player data.
  if (isGuildTopLevelTab(control, window)) {
    return Boolean(GUILD_STATE_TABS[guildReferenceState]?.has(control.name));
  }

  if (control.tabButtonVisible === false) return false;
  return String(control.properties?.Visible ?? 'true').trim().toLowerCase() !== 'false';
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

function controlVisibleThroughTabs(control, model, selected, window) {
  let current = control;
  const visited = new Set();
  while (current) {
    const parentName = simpleParent(current.properties?.Parent);
    if (!parentName || parentName === 'this' || visited.has(parentName)) return true;
    visited.add(parentName);
    const parent = model.namedContainers.get(parentName);
    if (!parent) return true;
    if (parent.type === 'DXTab' || parent.type === 'DXConfigTab') {
      if (!sourceVisible(parent, window)) return false;
      const tabControlName = simpleParent(parent.properties?.Parent);
      if (tabControlName && selected.get(tabControlName) !== parent.name) return false;
    }
    current = parent;
  }
  return true;
}

function ensureVisibleSelections(state) {
  for (const [tabControlName, tabs] of state.model.tabGroups) {
    const current = state.selected.get(tabControlName);
    const currentControl = state.model.namedContainers.get(current);
    if (currentControl && sourceVisible(currentControl, state.window)) continue;
    const firstVisible = tabs.find(name => sourceVisible(state.model.namedContainers.get(name), state.window));
    if (firstVisible) state.selected.set(tabControlName, firstVisible);
    else state.selected.delete(tabControlName);
  }
}

function applyWindowTabs(root, state) {
  ensureVisibleSelections(state);
  const {window, model, selected} = state;
  for (const element of root.querySelectorAll('[data-control-index]')) {
    const index = Number.parseInt(element.dataset.controlIndex || '', 10);
    if (!Number.isInteger(index)) continue;
    const control = model.controls[index];
    if (!control) continue;

    const isTab = control.type === 'DXTab' || control.type === 'DXConfigTab';
    if (isTab) {
      const tabControlName = simpleParent(control.properties?.Parent);
      setTabSkin(element, sourceVisible(control, window) && selected.get(tabControlName) === control.name);
    }

    element.hidden = !sourceVisible(control, window) || !controlVisibleThroughTabs(control, model, selected, window);
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
  const state = {window, model, selected};
  selectedByWindow.set(root, state);
  root.dataset.originsTabsInitialized = '1';
  applyWindowTabs(root, state);
}

function comboInt(expression, fallback) {
  const value = String(expression ?? '').trim();
  return /^-?\d+$/.test(value) ? Number(value) : fallback;
}

function comboBool(expression, fallback=false) {
  const value = String(expression ?? '').trim().toLowerCase();
  if (value === 'true') return true;
  if (value === 'false') return false;
  return fallback;
}

function restoreCombo(element, control) {
  if (!(element instanceof Element) || element.dataset.originsComboInitialized === '1') return;
  const properties = control?.properties || {};
  const normalHeight = Math.max(1, comboInt(properties.NormalHeight, 16));
  const dropDownHeight = Math.max(normalHeight, comboInt(properties.DropDownHeight, 123));
  const arrow = element.querySelector(':scope > img.ui-button');
  const selectedLabel = element.querySelector(':scope > span');

  element.dataset.originsComboInitialized = '1';
  element.dataset.sourceNormalHeight = String(normalHeight);
  element.dataset.sourceDropDownHeight = String(dropDownHeight);
  element.dataset.runtimeOptions = 'DXListBoxItem controls supplied by game/runtime';
  element.dataset.sourceListParent = 'ActiveScene';
  element.dataset.sourceSort = String(comboBool(properties.Sort, true));
  element.style.background = 'transparent';
  element.style.border = '1px solid #c6a663';
  element.style.overflow = 'visible';

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
  if (selectedLabel) selectedLabel.style.width = `${Math.max(0, element.clientWidth - 3 - arrowHeight)}px`;
  if (arrow) {
    arrow.style.left = `${Math.max(0, element.clientWidth - arrowWidth)}px`;
    arrow.style.top = `${Math.max(0, Math.trunc((normalHeight - arrowHeight) / 2))}px`;
    arrow.dataset.sourceLibrary = 'GameInter';
    arrow.dataset.sourceIndex = '795';
  }

  let showing = comboBool(properties.Showing, false);
  const applyShowing = () => {
    // Zircon: min(ListBox.ScrollBar.MaxValue + NormalHeight + 2, DropDownHeight).
    // Runtime rows are intentionally absent in this reference, so MaxValue=0.
    const height = showing ? Math.min(normalHeight + 2, dropDownHeight) : normalHeight;
    element.style.height = `${height}px`;
    element.dataset.sourceShowing = String(showing);
    element.dataset.sourceNeutralListHeight = String(Math.max(0, height - normalHeight - 2));
    element.classList.toggle('showing', showing);
  };

  applyShowing();
  arrow?.addEventListener('click', event => {
    showing = !showing;
    applyShowing();
    event.preventDefault();
    event.stopPropagation();
  });
}

function initializeComboWindow(root) {
  if (!(root instanceof Element)) return;
  const window = comboSourceWindowForRoot(root);
  if (!window) return;
  const controls = window.controls || [];
  for (const element of root.querySelectorAll('[data-control-type="DXComboBox"][data-control-index]')) {
    const index = Number.parseInt(element.dataset.controlIndex || '', 10);
    if (!Number.isInteger(index)) continue;
    const control = controls[index];
    if (control?.type === 'DXComboBox') restoreCombo(element, control);
  }
}

function scan(node) {
  if (!(node instanceof Element)) return;
  if (node.matches('.window,.generic-window')) {
    initializeWindow(node);
    initializeComboWindow(node);
  }
  node.querySelectorAll?.('.window,.generic-window').forEach(root => {
    initializeWindow(root);
    initializeComboWindow(root);
  });
}

function refreshGuildReferenceState() {
  guildReferenceState = guildStateSelect?.value || 'noGuild';
  guildStateControl?.classList.toggle('reference-active', guildReferenceState !== 'noGuild');
  const guildItem = gameSceneWindows.find(item => item.field === 'GuildBox');
  if (!guildItem) return;
  const root = document.querySelector(`#w-${CSS.escape(guildItem.id)}`);
  if (!root) return;
  initializeWindow(root);
  const state = selectedByWindow.get(root);
  if (state) applyWindowTabs(root, state);
}

guildStateSelect?.addEventListener('change', refreshGuildReferenceState);
refreshGuildReferenceState();

stage.addEventListener('click', event => {
  if (!(event.target instanceof Element)) return;
  const tabElement = event.target.closest('[data-control-type="DXTab"],[data-control-type="DXConfigTab"]');
  if (!tabElement || tabElement.hidden) return;
  const root = tabElement.closest('.window,.generic-window');
  if (!root) return;
  initializeWindow(root);
  const state = selectedByWindow.get(root);
  if (!state) return;

  const index = Number.parseInt(tabElement.dataset.controlIndex || '', 10);
  const tab = Number.isInteger(index) ? state.model.controls[index] : null;
  if (!tab || !sourceVisible(tab, state.window) || (tab.type !== 'DXTab' && tab.type !== 'DXConfigTab')) return;
  const tabControlName = simpleParent(tab.properties?.Parent);
  if (!tabControlName || !state.model.tabGroups.get(tabControlName)?.includes(tab.name)) return;

  state.selected.set(tabControlName, tab.name);
  applyWindowTabs(root, state);
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
    stage.querySelectorAll('.window,.generic-window').forEach(root => {
      initializeWindow(root);
      initializeComboWindow(root);
    });
    const controls = spec.windows.flatMap(window => window.controls || []);
    const tabControls = controls.filter(control => control.type === 'DXTabControl').length;
    const tabs = controls.filter(control => control.type === 'DXTab' || control.type === 'DXConfigTab').length;
    const combos = [...(spec.windows || []), ...(spec.nestedWindows || [])]
      .flatMap(window => window.controls || [])
      .filter(control => control.type === 'DXComboBox').length;
    console.info(`ORIGINS Zircon tab runtime: ${tabControls} tab controls / ${tabs} tabs / Guild state ${guildReferenceState}`);
    console.info(`ORIGINS Zircon DXComboBox runtime: ${combos} source combo boxes / neutral runtime options`);
  })
  .catch(error => console.error('Unable to load Zircon tab/combo manifest', error));
