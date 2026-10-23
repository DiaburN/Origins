window.G = window.G || {};

G.MagicUI = (() => {
  const A = G.MagicUiAssets || {};

  // Values below are read from the user-provided System.db.
  // The evolution order and 5-socket rule are ORIGINS X design decisions agreed for the Fire branch.
  const STAGES = Object.freeze([
    {
      id: 'fire-ball',
      name: 'Fire Ball',
      magic: 201,
      icon: 'iconFireBall0',
      need: [7, 9, 11],
      basePower: [0, 4],
      levelPower: [6, 10],
      baseCost: 1,
      levelCost: 3,
      delay: 0,
      description: 'The most basic Fire spell. Its damage increases with training.'
    },
    {
      id: 'adamantine-fire-ball',
      name: 'Adamantine Fire Ball',
      magic: 208,
      icon: 'iconAdamantine8',
      need: [15, 17, 19],
      basePower: [7, 11],
      levelPower: [15, 19],
      baseCost: 6,
      levelCost: 6,
      delay: 0,
      description: 'A spell that is more powerful than the Fireball. Its damage increases with training.'
    },
    {
      id: 'fire-bounce',
      name: 'Fire Bounce',
      magic: 231,
      icon: 'iconFireBall0',
      need: [15, 17, 19],
      basePower: [7, 11],
      levelPower: [15, 19],
      baseCost: 6,
      levelCost: 6,
      delay: 0,
      description: 'Bounces a powerful fireball between close targets. The number of bounces increase with training.'
    },
    {
      id: 'meteor-shower',
      name: 'Meteor Shower',
      magic: 226,
      icon: 'iconMeteor224',
      need: [43, 45, 47],
      basePower: [14, 22],
      levelPower: [32, 40],
      baseCost: 40,
      levelCost: 38,
      delay: 0,
      description: 'A spell that damages enemies within a set range. Its damage and the number of enemies affected increases with training.'
    },
    {
      id: 'asteroid',
      name: 'Asteroid',
      magic: 240,
      icon: 'iconAsteroid392',
      need: [80, 82, 84],
      basePower: [50, 80],
      levelPower: [70, 120],
      baseCost: 200,
      levelCost: 200,
      delay: 3300,
      description: 'Summons fire from the sky to inflict massive area damage, leaving fire walls in its wake. Damage increases with training.'
    }
  ]);

  const EFFECT_STONES = Object.freeze([
    {
      id: 'burning',
      name: 'Burning',
      magic: 234,
      icon: 'iconBurning484',
      need: [76, 80, 86],
      basePower: [12, 18],
      levelPower: [12, 16],
      baseCost: 20,
      levelCost: 120,
      delay: 0,
      description: 'Ignites the enemy and inflicts a continuous fire attack for a certain period of time. Passively applies to all fire skills. Damage and duration increase with training.'
    },
    {
      id: 'scorched-earth',
      name: 'Scorched Earth',
      magic: 212,
      icon: 'iconScorchedEarth16',
      need: [20, 22, 24],
      basePower: [12, 16],
      levelPower: [14, 18],
      baseCost: 15,
      levelCost: 11,
      delay: 0,
      description: 'A spell that shoots out line of fire along the ground, damaging all enemies caught within the fire. Its damage increases with training.'
    },
    {
      id: 'fire-wall',
      name: 'Fire Wall',
      magic: 216,
      icon: 'iconFireWall42',
      need: [24, 26, 28],
      basePower: [1, 6],
      levelPower: [2, 9],
      baseCost: 30,
      levelCost: 22,
      delay: 0,
      description: 'A spell that creates a wall of fire in the shape of a cross damaging enemies over a period of time. Its damage increases with training.'
    },
    {
      id: 'fire-storm',
      name: 'Fire Storm',
      magic: 220,
      icon: 'iconFireStorm44',
      need: [32, 34, 36],
      basePower: [14, 18],
      levelPower: [14, 18],
      baseCost: 20,
      levelCost: 15,
      delay: 0,
      description: 'A spell that deals fire damage to all enemies within a fixed area(3x3) of choice. Its damage increases with training.'
    }
  ]);

  const CURRENT_STAGE = 2; // Fire Bounce: visual prototype state agreed for the Fire branch.
  const OPEN_SOCKETS = CURRENT_STAGE + 1;
  const EQUIPPED_STONE_IDS = Object.freeze(['burning', 'scorched-earth', 'fire-wall']);

  let selectedKind = 'stage';
  let selectedId = STAGES[CURRENT_STAGE].id;

  function img(asset, alt = '') {
    const src = A[asset] || '';
    return `<img src="${src}" alt="${escapeHtml(alt)}" draggable="false">`;
  }

  function render() {
    const selected = getSelected();
    return `
      <div class="origins-magic-book" data-magic-book>
        <img class="origins-magic-header-art" src="${A.interfaceWizardHeader161 || ''}" alt="" draggable="false">
        <img class="origins-magic-background-art" src="${A.interfaceBackground164 || ''}" alt="" draggable="false">
        <button class="origins-magic-close" type="button" data-magic-close aria-label="Cerrar">${img('interfaceClose15')}</button>
        <div class="origins-magic-title">MAGIAS · WIZARD</div>

        <nav class="origins-magic-school-tabs" aria-label="Escuelas de magia">
          ${schoolTab('Fuego', 'tabFireSelected175', true)}
          ${schoolTab('Hielo', 'tabIce176', false)}
          ${schoolTab('Rayo', 'tabLightning178', false)}
          ${schoolTab('Viento', 'tabWind180', false)}
          ${schoolTab('Phantom', 'tabPhantom182', false)}
        </nav>

        <div class="origins-magic-content">
          <div class="origins-magic-section-label">EVOLUCIÓN · FUEGO</div>
          <div class="origins-magic-evolution" role="list">
            ${STAGES.map((stage, index) => renderStage(stage, index)).join('')}
          </div>

          ${renderDetail(selected)}

          <div class="origins-magic-socket-title">
            <span>ENGARCES DE PIEDRA</span>
            <strong>${OPEN_SOCKETS}/5</strong>
          </div>
          <div class="origins-magic-sockets">
            ${Array.from({ length: 5 }, (_, index) => renderSocket(index)).join('')}
          </div>

          <div class="origins-magic-effect-title">EFECTOS MIR DISPONIBLES</div>
          <div class="origins-magic-effect-palette">
            ${EFFECT_STONES.map(renderEffectStone).join('')}
          </div>
        </div>
      </div>`;
  }

  function schoolTab(label, asset, active) {
    return `<button type="button" class="origins-school-tab${active ? ' is-active' : ''}" ${active ? '' : 'disabled'} title="${escapeHtml(label)}">
      <img src="${A[asset] || ''}" alt="${escapeHtml(label)}" draggable="false">
    </button>`;
  }

  function renderStage(stage, index) {
    const state = index < CURRENT_STAGE ? 'is-complete' : index === CURRENT_STAGE ? 'is-current' : 'is-future';
    const frame = index <= CURRENT_STAGE ? 'gameInter2Slot816' : 'gameInter2SlotLocked815';
    const selected = selectedKind === 'stage' && selectedId === stage.id;
    return `<button type="button" role="listitem" class="origins-magic-stage ${state}${selected ? ' is-selected' : ''}" data-magic-stage="${stage.id}" title="${escapeHtml(stage.name)}">
      <span class="origins-slot-art">
        <img class="origins-slot-frame" src="${A[frame] || ''}" alt="" draggable="false">
        <img class="origins-slot-icon" src="${A[stage.icon] || ''}" alt="" draggable="false">
      </span>
      <span class="origins-stage-name">${escapeHtml(stage.name)}</span>
    </button>`;
  }

  function renderDetail(info) {
    return `<div class="origins-magic-detail">
      <img class="origins-magic-detail-art" src="${A.interfaceCell165 || ''}" alt="" draggable="false">
      <img class="origins-magic-detail-icon" src="${A[info.icon] || ''}" alt="" draggable="false">
      <strong class="origins-magic-detail-name">${escapeHtml(info.name)}</strong>
      <span class="origins-magic-detail-stats">Req. ${info.need[0]} · MP ${info.baseCost} · Power ${info.basePower[0]}-${info.basePower[1]} · Magic ${info.magic}</span>
      <p class="origins-magic-description">${escapeHtml(info.description)}</p>
      <span class="origins-magic-source">System.db · MIcon index ${getIconIndex(info.icon)}</span>
    </div>`;
  }

  function renderSocket(index) {
    const isOpen = index < OPEN_SOCKETS;
    const stone = isOpen ? EFFECT_STONES.find(item => item.id === EQUIPPED_STONE_IDS[index]) : null;
    const frame = isOpen ? 'gameInter2Slot816' : 'gameInter2SlotLocked815';
    const selected = stone && selectedKind === 'stone' && selectedId === stone.id;
    return `<button type="button" class="origins-stone-socket${isOpen ? ' is-open' : ' is-locked'}${selected ? ' is-selected' : ''}" ${stone ? `data-magic-stone="${stone.id}"` : 'disabled'} title="${stone ? escapeHtml(stone.name) : 'Engarce cerrado'}">
      <img class="origins-slot-frame" src="${A[frame] || ''}" alt="" draggable="false">
      ${stone ? `<img class="origins-slot-icon" src="${A[stone.icon] || ''}" alt="" draggable="false">` : ''}
      <span>${index + 1}</span>
    </button>`;
  }

  function renderEffectStone(stone) {
    const selected = selectedKind === 'stone' && selectedId === stone.id;
    return `<button type="button" class="origins-effect-stone${selected ? ' is-selected' : ''}" data-magic-stone="${stone.id}" title="${escapeHtml(stone.name)}">
      <img src="${A[stone.icon] || ''}" alt="" draggable="false">
      <span>${escapeHtml(stone.name)}</span>
    </button>`;
  }

  function getSelected() {
    if (selectedKind === 'stone') {
      return EFFECT_STONES.find(item => item.id === selectedId) || EFFECT_STONES[0];
    }
    return STAGES.find(item => item.id === selectedId) || STAGES[CURRENT_STAGE];
  }

  function getIconIndex(asset) {
    const match = String(asset).match(/(\d+)$/);
    return match ? match[1] : '?';
  }

  function refreshOpenBook() {
    const body = document.querySelector('#ui-window-magic .ingame-window-body');
    if (!body) return;
    body.innerHTML = render();
  }

  function handleClick(event) {
    const close = event.target.closest('[data-magic-close]');
    if (close) {
      G.IngameUI?.closeWindow?.('magic');
      return;
    }

    const stage = event.target.closest('[data-magic-stage]');
    if (stage) {
      selectedKind = 'stage';
      selectedId = stage.dataset.magicStage;
      refreshOpenBook();
      return;
    }

    const stone = event.target.closest('[data-magic-stone]');
    if (stone) {
      selectedKind = 'stone';
      selectedId = stone.dataset.magicStone;
      refreshOpenBook();
    }
  }

  function init() {
    document.addEventListener('click', handleClick);

    const panel = document.querySelector('.main-panel-image');
    if (panel && A.gameInterMain50) panel.src = A.gameInterMain50;

    const magicWindow = document.getElementById('ui-window-magic');
    const body = magicWindow?.querySelector('.ingame-window-body');

    if (magicWindow) {
      new MutationObserver(() => {
        if (!magicWindow.hidden) refreshOpenBook();
      }).observe(magicWindow, { attributes: true, attributeFilter: ['hidden'] });
    }

    if (body) {
      new MutationObserver(() => {
        if (!magicWindow?.hidden && !body.querySelector('[data-magic-book]')) {
          queueMicrotask(refreshOpenBook);
        }
      }).observe(body, { childList: true });
    }
  }

  function escapeHtml(value) {
    return String(value ?? '').replace(/[&<>'"]/g, char => ({
      '&':'&amp;', '<':'&lt;', '>':'&gt;', "'":'&#39;', '"':'&quot;'
    })[char]);
  }

  addEventListener('DOMContentLoaded', init, { once: true });

  return Object.freeze({ render, stages: STAGES, effectStones: EFFECT_STONES });
})();
