import { gameSceneWindows } from './game-scene-windows.js';

const stage = document.querySelector('#stage');
const byId = new Map(gameSceneWindows.map(item => [item.id, item]));
const byField = new Map(gameSceneWindows.map(item => [item.field, item]));
let interactions = [];

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
    case 'open':
      openWindowById(target.id);
      break;
    case 'close':
      existing?.remove();
      break;
    case 'toggle':
      if (existing) existing.remove();
      else openWindowById(target.id);
      break;
  }
}

function sourceFieldFromRoot(root) {
  if (!(root instanceof Element) || !root.id?.startsWith('w-')) return null;
  const id = root.id.slice(2);
  return byId.get(id)?.field || null;
}

stage.addEventListener('click', event => {
  if (!(event.target instanceof Element)) return;
  const controlElement = event.target.closest('[data-control-name]');
  if (!controlElement) return;
  const root = controlElement.closest('.window,.generic-window');
  const sourceField = sourceFieldFromRoot(root);
  if (!sourceField) return;

  const control = controlElement.dataset.controlName;
  const interaction = interactions.find(item =>
    item.sourceField === sourceField &&
    item.control === control &&
    item.event === 'MouseClick'
  );
  if (!interaction) return;

  event.preventDefault();
  event.stopPropagation();
  applyInteraction(interaction);
});

fetch('ui-source-spec.json')
  .then(response => {
    if (!response.ok) throw new Error(`ui-source-spec.json ${response.status}`);
    return response.json();
  })
  .then(spec => {
    interactions = Array.isArray(spec.interactions) ? spec.interactions : [];
    console.info(`ORIGINS Zircon interaction runtime: ${interactions.length} source-backed links`);
  })
  .catch(error => console.error('Unable to load Zircon interaction manifest', error));
