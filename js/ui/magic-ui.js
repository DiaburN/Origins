window.G = window.G || {};

G.MagicUI = (() => {
  // Values below are read from the user-provided System.db.
  // The evolution order and 5-socket rule are ORIGINS X design decisions agreed for the Fire branch.
  const STAGES = Object.freeze([
    {
      id: 'fire-ball',
      name: 'Fire Ball',
      magic: 201,
      icon: 'fire-ball',
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
      icon: 'adamantine',
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
      icon: 'fire-ball',
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
      icon: 'meteor',
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
      icon: 'asteroid',
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
      icon: 'burning',
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
      icon: 'scorched-earth',
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
      icon: 'fire-wall',
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
      icon: 'fire-storm',
      need: [32, 34, 36],
      basePower: [14, 18],
      levelPower: [14, 18],
      baseCost: 20,
      levelCost: 15,
      delay: 0,
      description: 'A spell that deals fire damage to all enemies within a fixed area(3x3) of choice. Its damage increases with training.'
    }
  ]);

  const CURRENT_STAGE = 2;
  const OPEN_SOCKETS = CURRENT_STAGE + 1;
  const EQUIPPED_STONE_IDS = Object.freeze(['burning', 'scorched-earth', 'fire-wall']);

  let selectedKind = 'stage';
  let selectedId = STAGES[CURRENT_STAGE].id;

  function asset(name, extraClass = '') {
    return `<span class="mir-magic-asset mir-${name}${extraClass ? ` ${extraClass}` : ''}" aria-hidden="true"></span>`;
  }

  function render() {
    const selected = getSelected();
    return `
      <div class="origins-magic-book" data-magic-book>
        ${asset('wizard-header', 'origins-magic-header-art')}
        ${asset('background', 'origins-magic-background-art')}
        <button class="origins-magic-close" type="button" data-magic-close aria-label="Cerrar">${asset('close')}</button>
        <div class="origins-magic-title">MAGIAS · WIZARD</div>

        <nav class="origins-magic-school-tabs" aria-label="Escuelas de magia">
          ${schoolTab('Fuego', 'fire-tab', true)}
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

  function schoolTab(label, assetName, active) {
    if (!assetName) return '';
    return `<button type="button" class="origins-school-tab${active ? ' is-active' : ''}" ${active ? '' : 'disabled'} title="${escapeHtml(label)}">
      ${asset(assetName)}
    </button>`;
  }

  function renderStage(stage, index) {
    const state = index < CURRENT_STAGE ? 'is-complete' : index === CURRENT_STAGE ? 'is-current' : 'is-future';
    const frame = index <= CURRENT_STAGE ? 'slot-gold' : 'slot-locked';
    const selected = selectedKind === 'stage' && selectedId === stage.id;
    return `<button type="button" role="listitem" class="origins-magic-stage ${state}${selected ? ' is-selected' : ''}" data-magic-stage="${stage.id}" title="${escapeHtml(stage.name)}">
      <span class="origins-slot-art">
        ${asset(frame, 'origins-slot-frame')}
        ${asset(stage.icon, 'origins-slot-icon')}
      </span>
      <span class="origins-stage-name">${escapeHtml(stage.name)}</span>
    </button>`;
  }

  function renderDetail(info) {
    return `<div class="origins-magic-detail">
      ${asset('cell', 'origins-magic-detail-art')}
      ${asset(info.icon, 'origins-magic-detail-icon')}
      <strong class="origins-magic-detail-name">${escapeHtml(info.name)}</strong>
      <span class="origins-magic-detail-stats">Req. ${info.need[0]} · MP ${info.baseCost} · Power ${info.basePower[0]}-${info.basePower[1]} · Magic ${info.magic}</span>
      <p class="origins-magic-description">${escapeHtml(info.description)}</p>
      <span class="origins-magic-source">System.db · MIcon index ${getIconIndex(info.icon)}</span>
    </div>`;
  }

  function renderSocket(index) {
    const isOpen = index < OPEN_SOCKETS;
    const stone = isOpen ? EFFECT_STONES.find(item => item.id === EQUIPPED_STONE_IDS[index]) : null;
    const frame = isOpen ? 'slot-gold' : 'slot-locked';
    const selected = stone && selectedKind === 'stone' && selectedId === stone.id;
    return `<button type="button" class="origins-stone-socket${isOpen ? ' is-open' : ' is-locked'}${selected ? ' is-selected' : ''}" ${stone ? `data-magic-stone="${stone.id}"` : 'disabled'} title="${stone ? escapeHtml(stone.name) : 'Engarce cerrado'}">
      ${asset(frame, 'origins-slot-frame')}
      ${stone ? asset(stone.icon, 'origins-slot-icon') : ''}
      <span>${index + 1}</span>
    </button>`;
  }

  function renderEffectStone(stone) {
    const selected = selectedKind === 'stone' && selectedId === stone.id;
    return `<button type="button" class="origins-effect-stone${selected ? ' is-selected' : ''}" data-magic-stone="${stone.id}" title="${escapeHtml(stone.name)}">
      ${asset(stone.icon)}
      <span>${escapeHtml(stone.name)}</span>
    </button>`;
  }

  function getSelected() {
    if (selectedKind === 'stone') {
      return EFFECT_STONES.find(item => item.id === selectedId) || EFFECT_STONES[0];
    }
    return STAGES.find(item => item.id === selectedId) || STAGES[CURRENT_STAGE];
  }

  function getIconIndex(icon) {
    return ({
      'fire-ball': 0,
      'adamantine': 8,
      'scorched-earth': 16,
      'fire-wall': 42,
      'fire-storm': 44,
      'meteor': 224,
      'asteroid': 392,
      'burning': 484
    })[icon] ?? '?';
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
