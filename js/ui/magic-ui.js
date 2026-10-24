window.G = window.G || {};

G.MagicUI = (() => {
  const A = G.GameUiAssets || { sheets: {}, sprites: {} };

  const BRANCHES = Object.freeze([
    {
      id: 'line',
      label: 'Line',
      stages: [
        {
          name: 'Slaying',
          magicId: 102,
          role: 'Passive foundation',
          behavior: 'Slaying remains learned as the foundation of the line branch. Its passive bonuses persist after the branch evolves.'
        },
        {
          name: 'Thrusting',
          magicId: 103,
          role: 'Toggle active',
          behavior: 'Extends the strike forward through additional cells and can be switched on or off.'
        },
        {
          name: 'CrushingWave',
          magicId: 126,
          role: 'Final line evolution',
          behavior: 'Projects a long forward wave with lateral secondary coverage.'
        }
      ]
    },
    {
      id: 'moon',
      label: 'Moon',
      stages: [
        {
          name: 'HalfMoon',
          magicId: 104,
          role: 'Frontal sweep',
          behavior: 'Toggle attack modifier that adds adjacent secondary hits.'
        },
        {
          name: 'DragonRise',
          magicId: 107,
          role: 'Wider sweep',
          behavior: 'Charged wider sweep evolution.'
        },
        {
          name: 'DestructiveSurge',
          magicId: 109,
          role: '360-degree sweep',
          behavior: 'Complete circular attack around the Warrior.'
        },
        {
          name: 'FireSword',
          magicId: 136,
          role: 'Final fire evolution',
          behavior: 'Fire-enhanced circular final evolution.'
        }
      ]
    },
    {
      id: 'dash',
      label: 'Dash',
      stages: [
        {
          name: 'ShoulderDash',
          magicId: 105,
          role: 'Dash and push',
          behavior: 'Movement attack that pushes targets.'
        },
        {
          name: 'Assault',
          magicId: 115,
          role: 'Enhanced dash/control',
          behavior: 'Evolves the dash with the paralysis/silence control concept from Zircon.'
        },
        {
          name: 'HundredFist',
          magicId: 133,
          role: 'Advanced rush',
          behavior: 'Advanced target rush with heavy displacement.'
        }
      ]
    },
    {
      id: 'power',
      label: 'Power Strike',
      stages: [
        {
          name: 'FlamingSword',
          magicId: 106,
          role: 'Charged heavy strike',
          behavior: 'Charged heavy strike foundation for the branch.'
        },
        {
          name: 'DefensiveBlow',
          magicId: 130,
          role: 'Defence reduction',
          behavior: 'Charged strike that applies the defence-reduction concept.'
        },
        {
          name: 'BladeStorm',
          magicId: 108,
          role: 'Final heavy evolution',
          behavior: 'Final evolution delivering three consecutive heavy strikes.'
        }
      ]
    },
    {
      id: 'utility',
      label: 'Utility',
      stages: [
        {
          name: 'Beckon',
          magicId: 112,
          role: 'Single-target pull/control',
          behavior: 'Single-target pull and control skill.'
        },
        {
          name: 'MassBeckon',
          magicId: 123,
          role: 'Mass pull/control',
          behavior: 'Mass pull/control evolution.'
        }
      ]
    }
  ]);

  let selectedBranchId = 'moon';
  let selectedStageIndex = 0;
  let stylesReady = false;

  function escapeHtml(value) {
    return String(value ?? '').replace(/[&<>'\"]/g, char => ({
      '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '\"': '&quot;'
    })[char]);
  }

  function currentClass() {
    const character = G.Session?.currentCharacter?.() || {};
    return String(character.className || '').toLowerCase();
  }

  function sprite(name, extraClass = '') {
    const spec = A.sprites?.[name];
    if (!spec) return '';
    const sheet = A.sheets?.[spec.sheet];
    if (!sheet) return '';
    return `<i class="origins-magic-sprite ${extraClass}" aria-hidden="true" style="width:${spec.w}px;height:${spec.h}px;background-image:url('${sheet}');background-position:-${spec.x}px -${spec.y}px"></i>`;
  }

  function branch() {
    return BRANCHES.find(item => item.id === selectedBranchId) || BRANCHES[0];
  }

  function stage() {
    const stages = branch().stages;
    return stages[Math.max(0, Math.min(selectedStageIndex, stages.length - 1))];
  }

  function nextStage() {
    return branch().stages[selectedStageIndex + 1] || null;
  }

  function realProgress(magicId, level) {
    const source = G.PlayerMagicRuntime?.byMagicId?.[magicId] || G.MagicRuntime?.byMagicId?.[magicId];
    if (!source) return null;

    const levelData = source.levels?.[level] || source.expByLevel?.[level] || null;
    if (levelData) {
      return {
        current: levelData.currentExp ?? levelData.current ?? '--',
        required: levelData.requiredExp ?? levelData.required ?? '--'
      };
    }

    return {
      current: source.currentExp ?? '--',
      required: source.requiredExp ?? '--'
    };
  }

  function expText(magicId, level) {
    const progress = realProgress(magicId, level);
    if (!progress) return 'EXP -- / --';
    return `EXP ${escapeHtml(progress.current)} / ${escapeHtml(progress.required)}`;
  }

  function magicIcon(magicId, extraClass = '') {
    const icons = G.MagicIconAssets;
    if (icons?.sprites) {
      const key = icons.byMagicId?.[magicId] || `magic-${magicId}`;
      const spec = icons.sprites[key];
      const sheet = spec && (icons.sheets?.[spec.sheet] || icons.sheet);
      if (spec && sheet) {
        return `<i class="origins-real-magic-icon ${extraClass}" aria-hidden="true" style="width:${spec.w}px;height:${spec.h}px;background-image:url('${sheet}');background-position:-${spec.x}px -${spec.y}px"></i>`;
      }
    }

    return `<span class="origins-magic-icon-empty ${extraClass}" title="MIcon pendiente de exportar" data-magic-id="${magicId}"></span>`;
  }

  function renderBranchRow(item) {
    const active = item.id === selectedBranchId;
    const current = item.stages[0];
    const chain = item.stages.map(value => value.name).join('  ›  ');

    return `<button type="button" class="origins-warrior-branch${active ? ' is-selected' : ''}" data-warrior-branch="${item.id}">
      ${sprite('interface-165', 'origins-cell-art')}
      ${magicIcon(current.magicId, 'origins-list-icon')}
      <span class="origins-branch-name">${escapeHtml(current.name)}</span>
      <span class="origins-branch-chain">${escapeHtml(chain)}</span>
    </button>`;
  }

  function renderLevel(level) {
    const current = stage();
    return `<div class="origins-level-row">
      <div class="origins-level-copy">
        <strong>Level ${level}</strong>
        <span>${expText(current.magicId, level)}</span>
      </div>
      <div class="origins-level-exp">${sprite('gameinter2-812', 'origins-exp-art')}</div>
    </div>`;
  }

  function renderStageButton(value, index) {
    const selected = index === selectedStageIndex;
    return `<button type="button" class="origins-stage-button${selected ? ' is-selected' : ''}" data-warrior-stage="${index}">${escapeHtml(value.name)}</button>`;
  }

  function render() {
    ensureStyles();

    const currentBranch = branch();
    const currentStage = stage();
    const evolution = nextStage();

    return `<div class="origins-warrior-magic" data-warrior-magic>
      <section class="origins-magic-main">
        ${sprite('interface-160', 'origins-header-art')}
        ${sprite('interface-164', 'origins-background-art')}
        <button class="origins-magic-close" type="button" data-warrior-magic-close aria-label="Cerrar">${sprite('interface-15')}</button>
        <div class="origins-magic-title">MAGIC</div>
        <div class="origins-active-tab" title="Active">${sprite('interface-167')}</div>

        <div class="origins-branch-list">
          ${BRANCHES.map(renderBranchRow).join('')}
        </div>

        <div class="origins-scroll-art" aria-hidden="true">
          ${sprite('interface-61', 'origins-scroll-up')}
          ${sprite('interface-60', 'origins-scroll-position')}
          ${sprite('interface-62', 'origins-scroll-down')}
        </div>
      </section>

      <aside class="origins-magic-progress">
        <div class="origins-progress-header-clip">${sprite('interface-160', 'origins-progress-header-art')}</div>
        <div class="origins-progress-bg-clip">${sprite('interface-164', 'origins-progress-bg-art')}</div>
        <div class="origins-progress-title">PROGRESS / EVOLUTION</div>

        <div class="origins-selected-magic">
          ${sprite('interface-165', 'origins-selected-cell-art')}
          ${magicIcon(currentStage.magicId, 'origins-selected-icon')}
          <div class="origins-selected-copy">
            <strong>${escapeHtml(currentStage.name)}</strong>
            <span>${escapeHtml(currentStage.role)}</span>
          </div>
        </div>

        <div class="origins-level-list">
          ${renderLevel(1)}
          ${renderLevel(2)}
          ${renderLevel(3)}
        </div>

        <div class="origins-behaviour">
          <span class="origins-caption">CURRENT EFFECT</span>
          <p>${escapeHtml(currentStage.behavior)}</p>
        </div>

        <div class="origins-evolution">
          <span class="origins-caption">EVOLUTION</span>
          <div class="origins-evolution-card${evolution ? '' : ' is-final'}">
            ${sprite('interface-165', 'origins-evolution-cell-art')}
            ${evolution ? magicIcon(evolution.magicId, 'origins-evolution-icon') : ''}
            <div class="origins-evolution-copy">
              <small>${evolution ? 'After Level 3' : 'Final stage'}</small>
              <strong>${escapeHtml(evolution ? evolution.name : currentStage.name)}</strong>
            </div>
          </div>
        </div>

        <div class="origins-branch-path">
          <span class="origins-caption">${escapeHtml(currentBranch.label.toUpperCase())} BRANCH</span>
          <div class="origins-stage-buttons">
            ${currentBranch.stages.map(renderStageButton).join('<span class="origins-stage-arrow">›</span>')}
          </div>
          <p>Al completar Level 3, la evolución sustituye a la magia anterior.</p>
        </div>
      </aside>
    </div>`;
  }

  function ensureStyles() {
    if (stylesReady || document.getElementById('origins-warrior-magic-styles')) return;
    stylesReady = true;

    const style = document.createElement('style');
    style.id = 'origins-warrior-magic-styles';
    style.textContent = `
      #ui-window-magic.origins-warrior-magic-window{width:720px!important;height:512px!important}
      #ui-window-magic.origins-warrior-magic-window>.ingame-window-body{width:720px!important;height:512px!important;overflow:visible}
      .origins-warrior-magic{position:relative;width:720px;height:512px;color:#fff;font-family:"Microsoft Sans Serif",Arial,sans-serif;image-rendering:pixelated}
      .origins-magic-sprite{position:absolute;display:block;background-repeat:no-repeat;image-rendering:pixelated;pointer-events:none}
      .origins-magic-main{position:absolute;left:0;top:0;width:420px;height:512px;overflow:hidden;background:#100808}
      .origins-header-art{left:0;top:0;z-index:2}.origins-background-art{left:0;top:66px;z-index:1}
      .origins-magic-title{position:absolute;left:0;top:3px;width:420px;height:24px;z-index:8;display:flex;align-items:center;justify-content:center;color:#c6a663;font:10px/24px "Microsoft Sans Serif",Arial,sans-serif;text-shadow:1px 1px #000}
      .origins-magic-close{position:absolute;right:3px;top:3px;width:32px;height:32px;border:0;padding:0;background:transparent;z-index:20}.origins-magic-close .origins-magic-sprite{left:0;top:0}.origins-magic-close:hover{filter:brightness(1.2)}
      .origins-active-tab{position:absolute;left:56px;top:40px;width:60px;height:24px;z-index:9}.origins-active-tab .origins-magic-sprite{left:0;top:0}
      .origins-branch-list{position:absolute;left:10px;top:76px;width:369px;display:flex;flex-direction:column;gap:5px;z-index:8}
      .origins-warrior-branch{position:relative;width:369px;height:54px;border:0;padding:0;background:transparent;text-align:left;color:#fff;overflow:hidden}.origins-warrior-branch:hover{filter:brightness(1.12)}.origins-warrior-branch.is-selected:after{content:"";position:absolute;inset:2px;border:1px solid #c6a663;box-shadow:0 0 5px rgba(198,166,99,.4) inset;z-index:6;pointer-events:none}
      .origins-cell-art{left:0;top:0;z-index:0}.origins-magic-icon-empty,.origins-real-magic-icon{position:absolute;display:block;width:36px;height:36px;box-sizing:border-box;background:#100808;border:1px solid #635332;image-rendering:pixelated}.origins-list-icon{left:9px;top:9px;z-index:3}.origins-branch-name{position:absolute;left:55px;top:7px;right:8px;color:#fff;font-size:9px;line-height:14px;text-shadow:1px 1px #000;z-index:3}.origins-branch-chain{position:absolute;left:55px;top:28px;right:10px;color:#c6a663;font-size:7px;line-height:12px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;text-shadow:1px 1px #000;z-index:3}
      .origins-scroll-art{position:absolute;right:6px;top:77px;width:20px;height:389px;z-index:9}.origins-scroll-up{left:0;top:0}.origins-scroll-position{left:0;top:31px}.origins-scroll-down{left:0;bottom:0}
      .origins-magic-progress{position:absolute;left:420px;top:0;width:300px;height:512px;overflow:hidden;background:#100808;border-left:1px solid #635332;box-shadow:inset 1px 0 #1b1108}
      .origins-progress-header-clip{position:absolute;left:0;top:0;width:300px;height:66px;overflow:hidden;z-index:1}.origins-progress-header-art{left:-120px;top:0}.origins-progress-bg-clip{position:absolute;left:0;top:66px;width:300px;height:446px;overflow:hidden;z-index:0}.origins-progress-bg-art{left:-120px;top:0}.origins-progress-title{position:absolute;left:0;top:3px;width:300px;height:24px;display:flex;align-items:center;justify-content:center;color:#c6a663;font-size:9px;text-shadow:1px 1px #000;z-index:8}
      .origins-selected-magic{position:absolute;left:10px;top:76px;width:280px;height:54px;overflow:hidden;z-index:5}.origins-selected-cell-art{left:0;top:0}.origins-selected-icon{left:9px;top:9px;z-index:2}.origins-selected-copy{position:absolute;left:55px;top:7px;right:8px;display:flex;flex-direction:column;z-index:3}.origins-selected-copy strong{font-size:10px;line-height:16px;color:#fff;text-shadow:1px 1px #000}.origins-selected-copy span{font-size:7px;line-height:13px;color:#c6a663}
      .origins-level-list{position:absolute;left:12px;top:140px;width:276px;z-index:5}.origins-level-row{position:relative;height:51px;border-bottom:1px solid rgba(99,83,50,.45)}.origins-level-copy{position:absolute;left:2px;right:2px;top:2px;display:flex;align-items:center;justify-content:space-between}.origins-level-copy strong{font-size:9px;color:#fff}.origins-level-copy span{font-size:7px;color:#c6a663}.origins-level-exp{position:absolute;left:2px;top:27px;width:248px;height:6px;overflow:hidden}.origins-exp-art{left:0;top:0}
      .origins-caption{display:block;height:18px;color:#c6a663;font-size:8px;line-height:18px;text-shadow:1px 1px #000}.origins-behaviour{position:absolute;left:12px;top:298px;width:276px;z-index:5}.origins-behaviour p{margin:1px 2px 0;color:#cbbd9f;font-size:7px;line-height:11px}
      .origins-evolution{position:absolute;left:10px;top:354px;width:280px;z-index:5}.origins-evolution-card{position:relative;width:280px;height:54px;overflow:hidden}.origins-evolution-cell-art{left:0;top:0}.origins-evolution-icon{left:9px;top:9px;z-index:2}.origins-evolution-copy{position:absolute;left:55px;top:7px;right:8px;display:flex;flex-direction:column;z-index:3}.origins-evolution-copy small{font-size:7px;color:#c6a663;line-height:13px}.origins-evolution-copy strong{font-size:10px;color:#fff;line-height:17px;text-shadow:1px 1px #000}.origins-evolution-card.is-final .origins-evolution-copy{left:12px}
      .origins-branch-path{position:absolute;left:10px;top:430px;width:280px;z-index:5}.origins-stage-buttons{display:flex;align-items:center;flex-wrap:wrap;gap:3px}.origins-stage-button{border:1px solid #635332;background:#100808;color:#a99d82;padding:2px 4px;font-size:7px;line-height:11px}.origins-stage-button:hover{border-color:#c6a663}.origins-stage-button.is-selected{color:#fff1bd;border-color:#c6a663;background:#281807}.origins-stage-arrow{color:#c6a663;font-size:10px}.origins-branch-path p{margin:6px 2px 0;color:#8f846e;font-size:7px;line-height:10px}
      @media(max-width:760px){#ui-window-magic.origins-warrior-magic-window{transform:scale(.82);transform-origin:top left}}
    `;
    document.head.appendChild(style);
  }

  function applyWindowMode() {
    const windowEl = document.getElementById('ui-window-magic');
    if (!windowEl) return;

    if (currentClass() !== 'warrior') {
      windowEl.classList.remove('origins-warrior-magic-window');
      return;
    }

    windowEl.classList.add('origins-warrior-magic-window');
    if (windowEl.dataset.userMoved !== '1') {
      windowEl.style.left = `${Math.max(0, innerWidth - 720)}px`;
    }
  }

  function refreshOpenBook() {
    if (currentClass() !== 'warrior') return;

    const windowEl = document.getElementById('ui-window-magic');
    const body = windowEl?.querySelector('.ingame-window-body');
    if (!windowEl || !body || windowEl.hidden) return;

    ensureStyles();
    applyWindowMode();
    body.innerHTML = render();
  }

  function handleClick(event) {
    const close = event.target.closest('[data-warrior-magic-close]');
    if (close) {
      G.IngameUI?.closeWindow?.('magic');
      return;
    }

    const branchButton = event.target.closest('[data-warrior-branch]');
    if (branchButton) {
      selectedBranchId = branchButton.dataset.warriorBranch;
      selectedStageIndex = 0;
      refreshOpenBook();
      return;
    }

    const stageButton = event.target.closest('[data-warrior-stage]');
    if (stageButton) {
      selectedStageIndex = Number(stageButton.dataset.warriorStage) || 0;
      refreshOpenBook();
    }
  }

  function init() {
    ensureStyles();
    document.addEventListener('click', handleClick);

    const windowEl = document.getElementById('ui-window-magic');
    const body = windowEl?.querySelector('.ingame-window-body');
    if (!windowEl || !body) return;

    new MutationObserver(() => {
      if (!windowEl.hidden) {
        queueMicrotask(refreshOpenBook);
      } else {
        windowEl.classList.remove('origins-warrior-magic-window');
      }
    }).observe(windowEl, { attributes: true, attributeFilter: ['hidden'] });

    new MutationObserver(() => {
      if (!windowEl.hidden && currentClass() === 'warrior' && !body.querySelector('[data-warrior-magic]')) {
        queueMicrotask(refreshOpenBook);
      }
    }).observe(body, { childList: true });
  }

  addEventListener('DOMContentLoaded', init, { once: true });

  return Object.freeze({ render, branches: BRANCHES, refresh: refreshOpenBook });
})();
