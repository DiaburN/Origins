const CLASS = Object.freeze({ Warrior: 0, Wizard: 1, Taoist: 2, Assassin: 3 });
const CLASS_BY_ID = Object.freeze(['Warrior', 'Wizard', 'Taoist', 'Assassin']);
const HEADER_INDEX = Object.freeze({ 0: 160, 1: 161, 2: 162, 3: 163 });
const SCHOOL = Object.freeze({
  1: { name: 'Passive', tab: 168 },
  2: { name: 'Active', tab: 166 },
  3: { name: 'Toggle', tab: 170 },
  4: { name: 'Fire', tab: 174 },
  5: { name: 'Ice', tab: 176 },
  6: { name: 'Lightning', tab: 178 },
  7: { name: 'Wind', tab: 180 },
  8: { name: 'Holy', tab: 184 },
  9: { name: 'Dark', tab: 186 },
  10: { name: 'Phantom', tab: 182 },
  11: { name: 'Physical', tab: 188 },
  12: { name: 'Atrocity', tab: 190 },
  13: { name: 'Kill', tab: 192 },
  14: { name: 'Assassination', tab: 194 },
  15: { name: 'Horse', tab: 172 },
});
const LEVEL_BORDER = Object.freeze({
  1: 860, 2: 861, 3: 862,
  4: 870, 5: 871, 6: 872, 7: 873, 10: 874,
  8: 880, 9: 881, 11: 883,
  12: 890, 13: 891, 14: 892,
});
const MAGIC_INFO_URL = new URL('../../database/generated/zircon-system/LibraryCore__Library_SystemModels_MagicInfo.json', import.meta.url);
const pad = value => String(value).padStart(5, '0');
const asset = (library, index) => `assets/${library}/${pad(index)}.png`;

let magicInfo = null;
let selectedSchool = null;
let state = {
  class: classFromQuery(),
  level: 50,
  spellSet: 1,
  magics: [],
};

function classFromQuery() {
  const value = new URLSearchParams(location.search).get('class');
  if (!value) return CLASS.Wizard;
  const normalized = value.trim().toLowerCase();
  const entry = Object.entries(CLASS).find(([name]) => name.toLowerCase() === normalized);
  if (entry) return entry[1];
  const numeric = Number(value);
  return Number.isInteger(numeric) && numeric >= 0 && numeric <= 3 ? numeric : CLASS.Wizard;
}

function normalizeClass(value) {
  if (typeof value === 'string') {
    const entry = Object.entries(CLASS).find(([name]) => name.toLowerCase() === value.trim().toLowerCase());
    if (entry) return entry[1];
  }
  const numeric = Number(value);
  return Number.isInteger(numeric) && numeric >= 0 && numeric <= 3 ? numeric : state.class;
}

function userMagicMap() {
  const map = new Map();
  for (const item of Array.isArray(state.magics) ? state.magics : []) {
    const key = Number(item?.Magic ?? item?.magic ?? item?.Info?.Magic ?? item?.info?.Magic);
    if (Number.isFinite(key)) map.set(key, item);
  }
  return map;
}

async function loadMagicInfo() {
  if (magicInfo) return magicInfo;
  if (Array.isArray(window.ORIGINS_ZIRCON_MAGIC_INFO)) {
    magicInfo = window.ORIGINS_ZIRCON_MAGIC_INFO;
    return magicInfo;
  }
  const response = await fetch(MAGIC_INFO_URL, { cache: 'no-store' });
  if (!response.ok) throw new Error(`MagicInfo load failed: ${response.status} ${response.statusText}`);
  const rows = await response.json();
  if (!Array.isArray(rows)) throw new Error('MagicInfo source is not an array.');
  magicInfo = rows;
  return magicInfo;
}

function playerRows(rows) {
  const learned = userMagicMap();
  return rows
    .filter(info => {
      const user = learned.get(Number(info.Magic));
      if (!user && (Number(info.Class) !== state.class || Number(info.School) === 0 || Number(info.School) === 20)) return false;
      if (Number(info.School) === 20) return false;
      if (user && Boolean(user.ItemRequired ?? user.itemRequired) && (user.RequiredItemEquipped ?? user.requiredItemEquipped) === false) return false;
      return SCHOOL[Number(info.School)] !== undefined;
    })
    .sort((a, b) => Number(a.NeedLevel1) - Number(b.NeedLevel1) || Number(a.Index) - Number(b.Index));
}

function injectStyles() {
  if (document.querySelector('#origins-zircon-magic-runtime-style')) return;
  const style = document.createElement('style');
  style.id = 'origins-zircon-magic-runtime-style';
  style.textContent = `
    #w-magic .zrm-header{position:absolute;left:0;top:0;pointer-events:none;z-index:0}
    #w-magic .zrm-runtime{position:absolute;left:0;top:0;width:419px;height:511px;z-index:3;pointer-events:none}
    #w-magic .zrm-tabs{position:absolute;left:56px;top:40px;height:28px;display:flex;gap:1px;pointer-events:auto}
    #w-magic .zrm-tab{position:relative;border:0;padding:0;margin:0;background:transparent;cursor:pointer;image-rendering:pixelated}
    #w-magic .zrm-tab img{display:block;position:static;image-rendering:pixelated}
    #w-magic .zrm-viewport{position:absolute;left:15px;top:77px;width:369px;height:402px;overflow-y:auto;overflow-x:hidden;scrollbar-width:none;pointer-events:auto}
    #w-magic .zrm-viewport::-webkit-scrollbar{display:none}
    #w-magic .zrm-list{position:relative;width:369px;min-height:100%}
    #w-magic .zrm-cell{position:relative;width:369px;height:54px;margin-bottom:5px;color:#fff;font:12px Arial,sans-serif;image-rendering:pixelated}
    #w-magic .zrm-cell>img{position:absolute;image-rendering:pixelated;pointer-events:none}
    #w-magic .zrm-cell-bg{left:0;top:0}
    #w-magic .zrm-level-border{left:4px;top:4px}
    #w-magic .zrm-icon{left:9px;top:9px;width:36px;height:36px}
    #w-magic .zrm-name{position:absolute;left:55px;top:1px;white-space:nowrap;color:#fff;text-shadow:1px 1px #000}
    #w-magic .zrm-level{position:absolute;left:57px;top:30px;white-space:pre-line;color:#e7c45d;text-shadow:1px 1px #000;line-height:12px}
    #w-magic .zrm-exp{position:absolute;right:6px;top:17px;color:#e7c45d;text-shadow:1px 1px #000;white-space:nowrap}
    #w-magic .zrm-key{position:absolute;left:9px;top:9px;width:36px;height:36px;display:flex;align-items:center;justify-content:center;color:aquamarine;font:bold 13px Arial,sans-serif;text-shadow:1px 1px #000;pointer-events:none}
    #w-magic .zrm-exp-track{position:absolute;left:110px;top:36px;height:8px;overflow:hidden}
    #w-magic .zrm-exp-fill{position:absolute;left:0;top:0;height:100%;max-width:100%;image-rendering:pixelated}
    #w-magic .zrm-scroll{position:absolute;left:389px;top:70px;width:20px;height:408px;pointer-events:auto}
    #w-magic .zrm-scroll img{position:absolute;left:1px;image-rendering:pixelated;pointer-events:none}
    #w-magic .zrm-scroll-up{top:1px}.zrm-scroll-down{bottom:1px}.zrm-scroll-thumb{top:16px}
  `;
  document.head.append(style);
}

function addImage(parent, library, index, className) {
  const image = document.createElement('img');
  image.src = asset(library, index);
  image.className = className;
  image.draggable = false;
  parent.append(image);
  return image;
}

function currentKey(user) {
  if (!user) return '';
  const set = Math.min(4, Math.max(1, Number(state.spellSet) || 1));
  return String(user[`Set${set}KeyLabel`] ?? user[`set${set}KeyLabel`] ?? user[`Set${set}Key`] ?? user[`set${set}Key`] ?? '').replace(/^None$/i, '');
}

function expTarget(info, user) {
  const level = Number(user?.Level ?? user?.level ?? 0);
  if (level === 0) return Number(info.Experience1) || 0;
  if (level === 1) return Number(info.Experience2) || 0;
  if (level === 2) return Number(info.Experience3) || 0;
  return Math.max(0, (level - 2) * 500);
}

function renderCell(info, learned) {
  const cell = document.createElement('div');
  cell.className = 'zrm-cell';
  cell.dataset.magic = String(info.Magic);
  cell.title = info.Description || info.Name || '';
  addImage(cell, 'Interface', 165, 'zrm-cell-bg');

  const user = learned.get(Number(info.Magic));
  const learnedMagic = Boolean(user);
  const playerMeetsLevel = Number(state.level) >= Number(info.NeedLevel1);
  if (!learnedMagic && !playerMeetsLevel) cell.style.opacity = '0.3';

  if (learnedMagic && LEVEL_BORDER[Number(info.School)]) {
    addImage(cell, 'GameInter2', LEVEL_BORDER[Number(info.School)], 'zrm-level-border');
  }
  addImage(cell, 'MagicIcon', Number(info.Icon), 'zrm-icon');

  const name = document.createElement('div');
  name.className = 'zrm-name';
  name.textContent = info.Name;
  cell.append(name);

  const level = document.createElement('div');
  level.className = 'zrm-level';
  const experience = document.createElement('div');
  experience.className = 'zrm-exp';

  if (learnedMagic) {
    const magicLevel = Number(user.Level ?? user.level ?? 0);
    const magicExperience = Number(user.Experience ?? user.experience ?? 0);
    level.textContent = `Level: ${magicLevel}`;
    if (!playerMeetsLevel) {
      experience.textContent = `Required Level: ${info.NeedLevel1}`;
      experience.style.color = '#ff4545';
    } else {
      const target = expTarget(info, user);
      experience.textContent = target > 0 ? `Experience: ${magicExperience}/${target}` : 'Experience: Max Level';
      if (target > 0) {
        const track = document.createElement('div');
        track.className = 'zrm-exp-track';
        const fill = addImage(track, 'GameInter2', 812, 'zrm-exp-fill');
        fill.style.clipPath = `inset(0 ${100 - Math.min(100, Math.max(0, (magicExperience / target) * 100))}% 0 0)`;
        cell.append(track);
      }
    }
    const key = currentKey(user);
    if (key) {
      const keyLabel = document.createElement('div');
      keyLabel.className = 'zrm-key';
      keyLabel.textContent = key;
      cell.append(keyLabel);
    }
  } else {
    level.textContent = 'Not\nLearned';
    level.style.top = '17px';
    level.style.color = '#ff4545';
    experience.textContent = `Required Level: ${info.NeedLevel1}`;
    experience.style.color = playerMeetsLevel ? '#32cd32' : '#ff4545';
  }

  cell.append(level, experience);
  return cell;
}

function renderScrollbar(runtime, viewport) {
  const scroll = document.createElement('div');
  scroll.className = 'zrm-scroll';
  addImage(scroll, 'Interface', 61, 'zrm-scroll-up');
  const thumb = addImage(scroll, 'Interface', 60, 'zrm-scroll-thumb');
  addImage(scroll, 'Interface', 62, 'zrm-scroll-down');
  runtime.append(scroll);

  const sync = () => {
    const max = Math.max(0, viewport.scrollHeight - viewport.clientHeight);
    const range = Math.max(0, scroll.clientHeight - 48);
    const top = 16 + (max ? (viewport.scrollTop / max) * range : 0);
    thumb.style.top = `${Math.round(top)}px`;
    thumb.style.opacity = max ? '1' : '0.35';
  };
  viewport.addEventListener('scroll', sync, { passive: true });
  scroll.addEventListener('wheel', event => {
    event.preventDefault();
    viewport.scrollTop += Math.sign(event.deltaY) * 59;
  }, { passive: false });
  requestAnimationFrame(sync);
}

function renderSchool(runtime, rows, schoolId) {
  runtime.querySelector('.zrm-viewport')?.remove();
  runtime.querySelector('.zrm-scroll')?.remove();
  const viewport = document.createElement('div');
  viewport.className = 'zrm-viewport';
  const list = document.createElement('div');
  list.className = 'zrm-list';
  const learned = userMagicMap();
  for (const info of rows.filter(row => Number(row.School) === schoolId)) list.append(renderCell(info, learned));
  viewport.append(list);
  runtime.append(viewport);
  renderScrollbar(runtime, viewport);
}

async function hydrate(root = document.querySelector('#w-magic')) {
  if (!root || root.dataset.zirconMagicHydrated === 'loading') return;
  root.dataset.zirconMagicHydrated = 'loading';
  try {
    injectStyles();
    const rows = playerRows(await loadMagicInfo());
    root.querySelector('.zrm-runtime')?.remove();
    root.querySelector('.zrm-header')?.remove();

    const header = document.createElement('img');
    header.src = asset('Interface', HEADER_INDEX[state.class]);
    header.className = 'zrm-header';
    header.draggable = false;
    root.prepend(header);

    const runtime = document.createElement('div');
    runtime.className = 'zrm-runtime';
    runtime.dataset.playerClass = CLASS_BY_ID[state.class];
    runtime.dataset.magicInfoSource = MAGIC_INFO_URL.pathname;
    root.append(runtime);

    const bySchool = [...new Set(rows.map(row => Number(row.School)))].sort((a, b) => a - b);
    if (!bySchool.length) {
      root.dataset.zirconMagicHydrated = 'true';
      return;
    }
    if (!bySchool.includes(selectedSchool)) selectedSchool = bySchool[0];

    const tabs = document.createElement('div');
    tabs.className = 'zrm-tabs';
    runtime.append(tabs);
    for (const schoolId of bySchool) {
      const school = SCHOOL[schoolId];
      const button = document.createElement('button');
      button.type = 'button';
      button.className = 'zrm-tab';
      button.title = school.name;
      button.dataset.school = String(schoolId);
      const tabImage = document.createElement('img');
      const updateImage = hover => {
        const active = schoolId === selectedSchool;
        tabImage.src = asset('Interface', school.tab + (active || hover ? 1 : 0));
      };
      updateImage(false);
      button.append(tabImage);
      button.addEventListener('mouseenter', () => updateImage(true));
      button.addEventListener('mouseleave', () => updateImage(false));
      button.addEventListener('click', () => {
        selectedSchool = schoolId;
        tabs.querySelectorAll('.zrm-tab').forEach(tab => {
          const id = Number(tab.dataset.school);
          const image = tab.querySelector('img');
          image.src = asset('Interface', SCHOOL[id].tab + (id === selectedSchool ? 1 : 0));
        });
        renderSchool(runtime, rows, schoolId);
      });
      tabs.append(button);
    }
    renderSchool(runtime, rows, selectedSchool);
    root.dataset.zirconMagicHydrated = 'true';
  } catch (error) {
    root.dataset.zirconMagicHydrated = 'error';
    console.error('[ORIGINS] Zircon MagicDialog runtime failed.', error);
  }
}

function refresh() {
  const root = document.querySelector('#w-magic');
  if (root) {
    root.dataset.zirconMagicHydrated = '';
    hydrate(root);
  }
}

window.OriginsZirconMagicRuntime = Object.freeze({
  get classes() { return { ...CLASS }; },
  get state() { return { ...state, magics: [...state.magics] }; },
  setPlayerState(next = {}) {
    state = {
      ...state,
      ...next,
      class: next.class === undefined ? state.class : normalizeClass(next.class),
      level: next.level === undefined ? state.level : Number(next.level),
      spellSet: next.spellSet === undefined ? state.spellSet : Number(next.spellSet),
      magics: next.magics === undefined ? state.magics : next.magics,
    };
    selectedSchool = null;
    refresh();
  },
  async load() { await loadMagicInfo(); refresh(); return magicInfo; },
  refresh,
});

const observer = new MutationObserver(mutations => {
  for (const mutation of mutations) {
    for (const node of mutation.addedNodes) {
      if (!(node instanceof Element)) continue;
      if (node.id === 'w-magic') hydrate(node);
      else node.querySelector?.('#w-magic') && hydrate(node.querySelector('#w-magic'));
    }
  }
});
observer.observe(document.documentElement, { childList: true, subtree: true });
hydrate();
