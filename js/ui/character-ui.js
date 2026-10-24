window.G = window.G || {};

G.CharacterUI = (() => {
  const A = () => G.GameUiAssets || { sheets: {}, sprites: {} };
  let scheduled = false;

  function esc(value) {
    return String(value ?? '').replace(/[&<>'"]/g, ch => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' })[ch]);
  }

  function spriteHtml(name, className = '') {
    const assets = A();
    const s = assets.sprites?.[name];
    if (!s) return '';
    const sheet = assets.sheets?.[s.sheet];
    if (!sheet) return '';
    return `<i class="zircon-sprite ${className}" style="width:${s.w}px;height:${s.h}px;background-image:url('${sheet}');background-position:-${s.x}px -${s.y}px"></i>`;
  }

  function topTab(label, selected = false) {
    return `<button class="zircon-tab-button${selected ? ' is-selected' : ''}" type="button">${spriteHtml(selected ? 'tab-selected-60' : 'tab-deselected-60', 'tab-bg')}<span>${esc(label)}</span></button>`;
  }

  function statTab(label, selected = false) {
    return `<button class="character-stat-tab${selected ? ' is-selected' : ''}" type="button"><span class="character-stat-tab-art">${spriteHtml(selected ? 'tab-selected-60' : 'tab-deselected-60')}</span><span class="character-stat-tab-label">${esc(label)}</span></button>`;
  }

  function hudValue(id, fallback = '0') {
    const value = document.getElementById(id)?.textContent?.trim();
    return value || fallback;
  }

  function attackStatsHtml() {
    const dc = hudValue('panel-dc');
    const mc = hudValue('panel-mc');
    const sc = hudValue('panel-sc');
    const rows = [
      ['DC:', `0-${dc}`, 'left', 0],
      ['MC:', `0-${mc}`, 'left', 1],
      ['SC:', `0-${sc}`, 'left', 2],
      ['Crit. Damage:', '0', 'left', 3],
      ['Accuracy:', '5', 'right', 0],
      ['A. Speed:', '0', 'right', 1],
      ['Luck:', '0', 'right', 2],
      ['Crit. Chance:', '0', 'right', 3]
    ];

    return rows.map(([label, value, side, row]) => {
      const x = side === 'left' ? 15 : 168;
      const valueX = x + 45;
      const y = 6 + row * 22;
      return `<span class="character-stat-label" style="left:${x}px;top:${y}px">${esc(label)}</span><span class="character-stat-value" style="left:${valueX}px;top:${y}px">${esc(value)}</span>`;
    }).join('');
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
      <div class="character-tabs exact-character-tabs">
        ${topTab('Character', true)}
        ${topTab('Discipline')}
        ${topTab('Hermit')}
        ${topTab('Crafting')}
      </div>

      <div class="exact-character-name-panel">
        <strong>${esc(character.name || '')}</strong>
        <span class="exact-character-guild"></span>
        <span class="exact-character-rank"></span>
      </div>

      <!-- Zircon draws this area from ProgUse + Equip layers at source origin 130,270.
           Do not substitute a pre-rendered class preview. -->
      <div class="character-paperdoll-origin" data-character-paperdoll-origin aria-hidden="true"></div>

      <div class="character-stats-tabs">
        ${statTab('Att', true)}
        ${statTab('Def')}
        ${statTab('Wt')}
        ${statTab('Oth')}
        ${statTab('E.Att')}
        ${statTab('E.Adv')}
        ${statTab('E.Dis')}
      </div>

      <div class="character-stats-content character-stats-attack">
        ${attackStatsHtml()}
      </div>`;
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

    observer.observe(layer, { childList: true, subtree: true, attributes: true, attributeFilter: ['hidden'] });
    scheduleRender();
  }

  return Object.freeze({ init, render });
})();

addEventListener('DOMContentLoaded', () => G.CharacterUI.init(), { once: true });
