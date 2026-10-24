window.G = window.G || {};

G.CharacterUI = (() => {
  const CHARACTER_TAB_Y = 19 + 26;
  const STAT_TABS = ['Att','Def','Wt','Oth','E.Att','E.Adv','E.Dis'];
  const EQUIPMENT_SLOTS = [
    { id:'weapon', x:58, y:122, w:65, h:90, hidden:true },
    { id:'armour', x:120, y:123, w:70, h:150, hidden:true },
    { id:'shield', x:170, y:170, w:36, h:36, hidden:true, fixedBorder:true },
    { id:'helmet', x:140, y:90, w:35, h:35, hidden:true, fixedBorder:true },
    { id:'emblem', x:244, y:118, art:104 },
    { id:'horseArmour', x:283, y:118, art:82 },
    { id:'torch', x:10, y:196, art:38 },
    { id:'necklace', x:10, y:157, art:33 },
    { id:'braceletL', x:244, y:157, art:32 },
    { id:'braceletR', x:283, y:157, art:32 },
    { id:'ringL', x:244, y:196, art:31 },
    { id:'ringR', x:283, y:196, art:31 },
    { id:'flower', x:244, y:235, art:81 },
    { id:'poison', x:244, y:274, art:40 },
    { id:'amulet', x:283, y:235, w:36, h:75, art:39 },
    { id:'shoes', x:10, y:235, w:36, h:75, art:36 },
    { id:'costume', x:10, y:118, art:34 }
  ];

  let scheduled = false;
  let selectedStatTab = 'Att';

  function esc(value) {
    return String(value ?? '').replace(/[&<>'"]/g, ch => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' })[ch]);
  }

  function regularRows(rows) {
    return rows.map(([label, value, side, row]) => {
      const x = side === 'left' ? 15 : 168;
      const valueX = x + 45;
      const y = 6 + row * 22;
      return `<span class="character-stat-label" style="left:${x}px;top:${y}px">${esc(label)}</span><span class="character-stat-value" style="left:${valueX}px;top:${y}px">${esc(value)}</span>`;
    }).join('');
  }

  function attackStatsHtml() {
    return regularRows([
      ['DC:', '0-0', 'left', 0],
      ['MC:', '0-0', 'left', 1],
      ['SC:', '0-0', 'left', 2],
      ['Crit. Damage:', '0', 'left', 3],
      ['Accuracy:', '0', 'right', 0],
      ['A. Speed:', '0', 'right', 1],
      ['Luck:', '0', 'right', 2],
      ['Crit. Chance:', '0', 'right', 3]
    ]);
  }

  function defenseStatsHtml() {
    return regularRows([
      ['AC:', '0-0', 'left', 0],
      ['MR:', '0-0', 'left', 1],
      ['Agility:', '0', 'right', 0],
      ['Life Steal:', '0', 'right', 1]
    ]);
  }

  function weightStatsHtml() {
    return regularRows([
      ['Body W:', '0 / 0', 'left', 0],
      ['Hand W:', '0 / 0', 'left', 1]
    ]);
  }

  function otherStatsHtml() {
    return regularRows([
      ['Comfort:', '0', 'left', 0],
      ['Pickup Radius:', '0', 'left', 1],
      ['Gold Rate:', '0', 'right', 0],
      ['Drop Rate:', '0', 'right', 1],
      ['Exp Rate:', '0', 'right', 2]
    ]);
  }

  function elementIconWidth(name) {
    if (name === 'Physical') return G.MainPanelAssets?.sprites?.['gameinter-1517']?.w ?? null;
    const index = G.CharacterPaperdollAssets?.elementIcons?.[name];
    if (index == null) return null;
    return G.CharacterPaperdollAssets?.frames?.[String(index)]?.w ?? null;
  }

  function elementRows(mode) {
    const left = [['Fire',0],['Ice',1],['Lightning',2],['Wind',3]];
    const right = [['Holy',0],['Dark',1],['Phantom',2]];
    if (mode !== 'attack') right.push(['Physical',3]);
    const rows = [...left.map(([name,row]) => [name,'left',row]), ...right.map(([name,row]) => [name,'right',row])];

    return rows.map(([name, side, row]) => {
      const x = side === 'left' ? 15 : 168;
      const y = 6 + row * 22;
      const iconX = x + 75;
      const width = elementIconWidth(name);
      const valueHtml = width == null ? '' : `<span class="character-element-value" style="left:${iconX + width}px;top:${y}px">0</span>`;
      return `<span class="character-stat-label" style="left:${x}px;top:${y}px">${name}:</span>${valueHtml}`;
    }).join('');
  }

  function statsHtml(tab) {
    switch (tab) {
      case 'Def': return defenseStatsHtml();
      case 'Wt': return weightStatsHtml();
      case 'Oth': return otherStatsHtml();
      case 'E.Att': return elementRows('attack');
      case 'E.Adv': return elementRows('advantage');
      case 'E.Dis': return elementRows('disadvantage');
      default: return attackStatsHtml();
    }
  }

  function appendTopTabs(container) {
    if (!container) return;
    container.replaceChildren();
    ['Character','Discipline','Hermit','Crafting'].forEach((label, index) => {
      const button = G.ZirconPrimitives?.makeButton?.({
        type: index === 0 ? 'selected-tab' : 'deselected-tab',
        width:60,
        label,
        className:'character-top-tab',
        selected:index === 0
      });
      if (button) container.appendChild(button);
    });
  }

  function refreshStatsContent(body) {
    const content = body.querySelector('[data-character-stats-content]');
    if (content) content.innerHTML = statsHtml(selectedStatTab);
  }

  function appendStatTabs(container, body) {
    if (!container) return;
    container.replaceChildren();
    STAT_TABS.forEach(label => {
      const selected = label === selectedStatTab;
      const button = G.ZirconPrimitives?.makeButton?.({
        type:selected ? 'selected-tab' : 'deselected-tab',
        width:40,
        label,
        className:'character-stat-tab',
        selected
      });
      if (!button) return;
      button.dataset.statTab = label;
      button.addEventListener('click', async () => {
        if (selectedStatTab === label) return;
        selectedStatTab = label;
        for (const sibling of container.querySelectorAll('[data-stat-tab]')) {
          const isSelected = sibling.dataset.statTab === selectedStatTab;
          sibling.dataset.selected = isSelected ? '1' : '0';
          await G.ZirconPrimitives?.repaintButton?.(sibling, isSelected ? 'selected-tab' : 'deselected-tab');
        }
        refreshStatsContent(body);
      });
      container.appendChild(button);
    });
  }

  function mountTabs(body) {
    appendTopTabs(body.querySelector('[data-character-top-tabs]'));
    appendStatTabs(body.querySelector('[data-character-stat-tabs]'), body);
  }

  function slotArt(index, cellWidth, cellHeight) {
    const a = G.ZirconPrimitiveAssets || {};
    const s = a.sprites?.[`interface-${index}`];
    if (!s || !a.sheet) return null;
    const art = document.createElement('i');
    art.className = 'character-slot-art';
    art.style.width = `${s.w}px`;
    art.style.height = `${s.h}px`;
    art.style.left = `${Math.floor((cellWidth - s.w) / 2)}px`;
    art.style.top = `${Math.floor((cellHeight - s.h) / 2)}px`;
    art.style.backgroundImage = `url('${a.sheet}')`;
    art.style.backgroundPosition = `-${s.x}px -${s.y}px`;
    art.style.backgroundRepeat = 'no-repeat';
    return art;
  }

  function mountEquipmentCells(body) {
    const host = body.querySelector('[data-character-equipment]');
    if (!host) return;
    host.replaceChildren();

    for (const slot of EQUIPMENT_SLOTS) {
      const w = slot.w || 36;
      const h = slot.h || 36;
      const cell = G.ZirconPrimitives?.makeItemCell?.({
        width:w,
        height:h,
        hidden:slot.hidden === true,
        fixedBorder:slot.fixedBorder === true,
        className:'character-equipment-cell'
      });
      if (!cell) continue;

      cell.dataset.equipmentSlot = slot.id;
      cell.style.left = `${slot.x}px`;
      cell.style.top = `${CHARACTER_TAB_Y + slot.y}px`;

      // CharacterDialog.Draw(cell,index): placeholder art is only drawn while
      // the equipment cell is empty and is centered at 20% opacity.
      if (!slot.hidden && slot.art != null) {
        const art = slotArt(slot.art, w, h);
        if (art) cell.insertBefore(art, cell.firstChild);
      }
      host.appendChild(cell);
    }
  }

  function render() {
    const windowEl = document.getElementById('ui-window-character');
    if (!windowEl || windowEl.hidden) return;
    const body = windowEl.querySelector('.ingame-window-body');
    if (!body) return;

    const character = G.Session?.currentCharacter?.() || {};
    const expectedName = String(character.name || '');
    if (body.dataset.exactCharacter === '1' && body.dataset.characterName === expectedName) return;

    body.dataset.exactCharacter = '1';
    body.dataset.characterName = expectedName;
    body.innerHTML = `
      <div class="character-tabs exact-character-tabs" data-character-top-tabs></div>
      <div class="exact-character-name-panel">
        <strong>${esc(character.name || '')}</strong>
        <span class="exact-character-guild"></span>
        <span class="exact-character-rank"></span>
      </div>
      <div class="character-equipment-layer" data-character-equipment></div>
      <div class="character-paperdoll-origin" data-character-paperdoll-origin aria-hidden="true"></div>
      <div class="character-stats-tabs" data-character-stat-tabs></div>
      <div class="character-stats-content" data-character-stats-content>${statsHtml(selectedStatTab)}</div>`;

    mountTabs(body);
    mountEquipmentCells(body);
    G.CharacterAppearance?.render?.(body.querySelector('[data-character-paperdoll-origin]'), character);
  }

  function scheduleRender() {
    if (scheduled) return;
    scheduled = true;
    requestAnimationFrame(() => {
      scheduled = false;
      render();
    });
  }

  function init() {
    const layer = document.getElementById('ui-window-layer');
    if (!layer) return;
    const observer = new MutationObserver(mutations => {
      for (const mutation of mutations) {
        const target = mutation.target instanceof Element ? mutation.target : mutation.target?.parentElement;
        if (target?.closest?.('#ui-window-character') || target?.id === 'ui-window-character') {
          const body = document.querySelector('#ui-window-character .ingame-window-body');
          if (body && !body.querySelector('.exact-character-name-panel')) body.dataset.exactCharacter = '0';
          scheduleRender();
          break;
        }
      }
    });
    observer.observe(layer, { childList:true, subtree:true, attributes:true, attributeFilter:['hidden'] });
    scheduleRender();
  }

  return Object.freeze({ init, render });
})();

addEventListener('DOMContentLoaded', () => G.CharacterUI.init(), { once:true });
