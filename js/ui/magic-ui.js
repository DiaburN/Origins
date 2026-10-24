window.G = window.G || {};

G.MagicUI = (() => {
  const A = G.GameUiAssets || { sheets: {}, sprites: {} };

  const DESIGN_FILES = Object.freeze({
    warrior: 'data/magics/origins-warrior-evolution.json',
    wizard: 'data/magics/origins-elemental-evolution.json',
    taoist: 'data/magics/origins-taoist-evolution.json',
    assassin: 'data/magics/origins-assassin-evolution.json'
  });

  const designCache = Object.create(null);
  const designPromises = Object.create(null);
  const designErrors = Object.create(null);
  const selectionByClass = Object.create(null);

  let magicRuntime = null;
  let magicRuntimePromise = null;
  let observerBound = false;

  function escapeHtml(value) {
    return String(value ?? '').replace(/[&<>\'"]/g, ch => ({
      '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;'
    })[ch]);
  }

  function humanize(value) {
    const text = String(value || '')
      .replace(/([a-z0-9])([A-Z])/g, '$1 $2')
      .replace(/[_-]+/g, ' ')
      .trim();
    return text ? text.charAt(0).toUpperCase() + text.slice(1) : 'Magic';
  }

  function currentClass() {
    const character = G.Session?.currentCharacter?.() || {};
    return String(character.className || 'warrior').toLowerCase();
  }

  function sprite(name, extraClass = '') {
    const spec = A.sprites?.[name];
    if (!spec) return '';
    const sheet = A.sheets?.[spec.sheet];
    if (!sheet) return '';
    return `<i class="origins-magic-sprite ${extraClass}" aria-hidden="true" style="width:${spec.w}px;height:${spec.h}px;background-image:url('${sheet}');background-position:-${spec.x}px -${spec.y}px"></i>`;
  }

  function stage(name, magicId, role = '', behavior = '') {
    return {
      name: String(name || ''),
      magicId: Number(magicId),
      role: String(role || ''),
      behavior: String(behavior || '')
    };
  }

  async function loadJson(url) {
    const response = await fetch(url, { cache: 'no-store' });
    if (!response.ok) throw new Error(`${response.status} ${response.statusText}: ${url}`);
    return response.json();
  }

  function ensureMagicRuntime() {
    if (magicRuntimePromise) return magicRuntimePromise;
    magicRuntimePromise = loadJson('assets/ui/magic/runtime.json')
      .then(data => {
        magicRuntime = data;
        refreshOpenBook();
        return data;
      })
      .catch(error => {
        console.warn('Magic runtime unavailable:', error);
        magicRuntime = null;
        return null;
      });
    return magicRuntimePromise;
  }

  function ensureDesign(className) {
    className = String(className || '').toLowerCase();
    if (!DESIGN_FILES[className]) return Promise.resolve(null);
    if (designCache[className]) return Promise.resolve(designCache[className]);
    if (designPromises[className]) return designPromises[className];

    designPromises[className] = loadJson(DESIGN_FILES[className])
      .then(data => {
        const normalized = normalizeDesign(className, data);
        designCache[className] = normalized;
        designErrors[className] = null;
        refreshOpenBook();
        return normalized;
      })
      .catch(error => {
        designErrors[className] = error;
        console.error(`Could not load ${className} magic design:`, error);
        refreshOpenBook();
        return null;
      });

    return designPromises[className];
  }

  function normalizeDesign(className, data) {
    switch (className) {
      case 'warrior': return normalizeWarrior(data);
      case 'wizard': return normalizeWizard(data);
      case 'taoist': return normalizeTaoist(data);
      case 'assassin': return normalizeAssassin(data);
      default: return { className, branches: [] };
    }
  }

  function normalizeWarrior(data) {
    const branches = [];

    for (const [id, source] of Object.entries(data.branches || {})) {
      const stages = (source.stages || []).map((value, index) => stage(
        value.sourceMagic || source.evolution?.[index] || '',
        value.sourceMagicId,
        value.role,
        value.originsBehavior || source.designNote || ''
      )).filter(value => value.name && Number.isFinite(value.magicId));

      if (stages.length) {
        branches.push({ id, label: humanize(id), stages, replacePrevious: true, note: source.designNote || '' });
      }
    }

    const utility = data.arcaneUtility;
    if (utility?.controlEvolution?.length) {
      const stages = utility.controlEvolution.map(name => {
        const info = utility.skills?.[name] || {};
        return stage(name, info.sourceMagicId, info.role, utility.designNote || '');
      }).filter(value => Number.isFinite(value.magicId));

      if (stages.length) {
        branches.push({
          id: 'utility',
          label: utility.workingName || 'Utility',
          stages,
          replacePrevious: true,
          note: utility.designNote || ''
        });
      }
    }

    return { className: 'warrior', branches };
  }

  function normalizeWizard(data) {
    const branches = [];

    for (const [id, source] of Object.entries(data.elements || {})) {
      let stages = [];
      if (Array.isArray(source.stages) && source.stages.length) {
        stages = source.stages.map((value, index) => stage(
          value.originsName || value.sourceMagic || source.evolution?.[index] || `Stage ${index + 1}`,
          value.sourceMagicId,
          value.nameStatus === 'pending' ? 'Evolution name pending' : '',
          value.behavior || source.designNote || ''
        ));
      } else {
        stages = (source.evolution || []).map(name => stage(
          name,
          source.sourceMagicIds?.[name],
          '',
          source.designNote || ''
        ));
      }

      stages = stages.filter(value => value.name && Number.isFinite(value.magicId));
      if (stages.length) {
        branches.push({
          id,
          label: humanize(id),
          stages,
          replacePrevious: data.rules?.evolutionReplacesPreviousSkill !== false,
          note: source.designNote || ''
        });
      }
    }

    const utility = data.wizardUtilitySchool?.skills || {};
    if (utility.MagicShield && utility.SuperiorMagicShield) {
      branches.push({
        id: 'shield',
        label: 'Shield',
        stages: [
          stage('MagicShield', utility.MagicShield.sourceMagicId, utility.MagicShield.role),
          stage('SuperiorMagicShield', utility.SuperiorMagicShield.sourceMagicId, utility.SuperiorMagicShield.role)
        ],
        replacePrevious: true,
        note: ''
      });
    }

    for (const name of ['Teleportation', 'GeoManipulation', 'Renounce']) {
      const value = utility[name];
      if (!value?.sourceMagicId) continue;
      branches.push({
        id: name.toLowerCase(),
        label: name,
        stages: [stage(name, value.sourceMagicId, value.role, value.zirconBehavior || '')],
        replacePrevious: true,
        note: value.zirconBehavior || ''
      });
    }

    return { className: 'wizard', branches };
  }

  function normalizeTaoist(data) {
    const branches = [];

    for (const [id, source] of Object.entries(data.branches || {})) {
      let stages = [];
      if (Array.isArray(source.evolution) && source.evolution.length) {
        stages = source.evolution.map(name => stage(
          name,
          source.sourceMagicIds?.[name],
          '',
          source.designNote || ''
        ));
      } else if (source.sourceMagicId) {
        stages = [stage(humanize(id), source.sourceMagicId, '', source.designNote || '')];
      } else if (source.sourceMagicIds) {
        const name = Object.keys(source.sourceMagicIds).find(key => !key.startsWith('Augment'));
        if (name) stages = [stage(name, source.sourceMagicIds[name], '', source.designNote || '')];
      }

      stages = stages.filter(value => value.name && Number.isFinite(value.magicId));
      if (stages.length) {
        branches.push({
          id,
          label: humanize(id),
          stages,
          replacePrevious: source.stacking !== 'cumulative',
          note: source.designNote || ''
        });
      }
    }

    return { className: 'taoist', branches };
  }

  function normalizeAssassin(data) {
    const core = data.coreKit || {};
    const branches = [];

    function addEvolution(id, label, source, behaviorResolver) {
      if (!source?.evolution?.length) return;
      const stages = source.evolution.map(name => stage(
        name,
        source.sourceMagicIds?.[name],
        '',
        behaviorResolver?.(name) || source.designNote || ''
      )).filter(value => Number.isFinite(value.magicId));
      if (stages.length) branches.push({ id, label, stages, replacePrevious: true, note: source.designNote || '' });
    }

    addEvolution('primaryLotusCombo', 'Lotus Combo', core.primaryLotusCombo, () => core.primaryLotusCombo?.originsBehavior?.rotation || '');

    if (core.cloak?.sourceMagicIds?.Cloak) {
      branches.push({
        id: 'cloak',
        label: 'Cloak',
        stages: [stage('Cloak', core.cloak.sourceMagicIds.Cloak, '', core.cloak.designNote || '')],
        replacePrevious: true,
        note: core.cloak.designNote || ''
      });
    }

    addEvolution('fireFarm', 'Fire / Farm', core.fireFarm, name => core.fireFarm?.originsBehavior?.[name] || '');
    addEvolution('mobilityExecution', 'Mobility', core.mobilityExecution);
    addEvolution('areaClear', 'Area Clear', core.areaClear);

    return { className: 'assassin', branches };
  }

  function magicInfo(magicId) {
    return magicRuntime?.byMagicId?.[String(magicId)] || null;
  }

  function magicIcon(magicId, extraClass = '') {
    const info = magicInfo(magicId);
    const icon = info?.icon;
    const sheet = magicRuntime?.sheet;

    if (icon && sheet) {
      return `<i class="origins-real-magic-icon ${extraClass}" aria-hidden="true" style="width:${icon.w}px;height:${icon.h}px;background-image:url('${sheet}');background-position:-${icon.x}px -${icon.y}px"></i>`;
    }

    return `<span class="origins-magic-icon-empty ${extraClass}" data-magic-id="${magicId}"></span>`;
  }

  function playerProgress(magicId, displayLevel) {
    const runtime = G.PlayerMagicRuntime?.byMagicId?.[magicId] || G.PlayerMagicRuntime?.byMagicId?.[String(magicId)];
    if (!runtime) return null;

    const levelData = runtime.levels?.[displayLevel] || runtime.levels?.[displayLevel - 1] || runtime.expByLevel?.[displayLevel];
    if (levelData) {
      const current = levelData.currentExp ?? levelData.current ?? levelData.experience;
      return Number.isFinite(Number(current)) ? Number(current) : null;
    }

    const currentLevel = Number(runtime.displayLevel ?? runtime.level);
    const current = Number(runtime.currentExp ?? runtime.experience);
    if (Number.isFinite(currentLevel) && Number.isFinite(current) && (currentLevel === displayLevel || currentLevel + 1 === displayLevel)) {
      return current;
    }
    return null;
  }

  function selected(config, className) {
    let state = selectionByClass[className];
    if (!state || !config.branches.some(branch => branch.id === state.branchId)) {
      state = { branchId: config.branches[0]?.id || '', stageIndex: 0 };
      selectionByClass[className] = state;
    }

    const branch = config.branches.find(value => value.id === state.branchId) || config.branches[0];
    const stageIndex = Math.max(0, Math.min(branch.stages.length - 1, Number(state.stageIndex) || 0));
    state.stageIndex = stageIndex;
    return { branch, stageIndex, stage: branch.stages[stageIndex] };
  }

  function renderNode(branch, value, index, selectedBranchId, selectedStageIndex) {
    const isSelected = branch.id === selectedBranchId && index === selectedStageIndex;
    const info = magicInfo(value.magicId);
    const label = info?.name || value.name;

    return `<button type="button" class="origins-tree-node${isSelected ? ' is-selected' : ''}" data-magic-branch="${escapeHtml(branch.id)}" data-magic-stage="${index}" title="${escapeHtml(label)}">
      <span class="origins-tree-node-frame">${sprite('gameinter2-816')}</span>
      ${magicIcon(value.magicId, 'origins-tree-node-icon')}
      <span class="origins-tree-node-name">${escapeHtml(label)}</span>
    </button>`;
  }

  function renderBranch(branch, selectedBranchId, selectedStageIndex) {
    return `<div class="origins-tree-branch${branch.id === selectedBranchId ? ' is-active' : ''}">
      <button type="button" class="origins-tree-branch-label" data-magic-branch-label="${escapeHtml(branch.id)}">${escapeHtml(branch.label)}</button>
      <div class="origins-tree-chain">
        ${branch.stages.map((value, index) => `${index ? '<span class="origins-tree-link" aria-hidden="true"></span>' : ''}${renderNode(branch, value, index, selectedBranchId, selectedStageIndex)}`).join('')}
      </div>
    </div>`;
  }

  function renderLevel(value, level) {
    const info = magicInfo(value.magicId);
    const required = Number(info?.experience?.[level - 1]);
    const needLevel = Number(info?.needLevels?.[level - 1]);
    const current = playerProgress(value.magicId, level);
    const hasRequired = Number.isFinite(required) && required > 0;
    const hasCurrent = Number.isFinite(current) && current >= 0;
    const percent = hasRequired && hasCurrent ? Math.max(0, Math.min(100, current / required * 100)) : 0;

    return `<div class="origins-detail-level">
      <div class="origins-detail-level-head">
        <strong>Level ${level}</strong>
        <span>${hasCurrent ? current : '--'} / ${hasRequired ? required : '--'}</span>
      </div>
      <div class="origins-detail-level-need">${Number.isFinite(needLevel) && needLevel > 0 ? `Character Lv ${needLevel}` : '&nbsp;'}</div>
      <div class="origins-detail-exp">
        <span class="origins-detail-exp-empty">${sprite('gameinter2-812')}</span>
        <span class="origins-detail-exp-fill" style="width:${percent.toFixed(2)}%">${sprite('gameinter2-812')}</span>
      </div>
    </div>`;
  }

  function renderEvolution(branch, stageIndex) {
    const current = branch.stages[stageIndex];
    const next = branch.stages[stageIndex + 1] || null;

    if (!next) {
      return `<div class="origins-detail-evolution is-final">
        <span class="origins-detail-section-title">EVOLUTION</span>
        <div class="origins-final-stage">Final stage</div>
      </div>`;
    }

    return `<div class="origins-detail-evolution">
      <span class="origins-detail-section-title">EVOLUTION AFTER LEVEL 3</span>
      <div class="origins-evolution-flow">
        <div class="origins-evolution-mini">
          <span class="origins-evolution-frame">${sprite('gameinter2-816')}</span>
          ${magicIcon(current.magicId, 'origins-evolution-mini-icon')}
        </div>
        <span class="origins-evolution-arrow">›</span>
        <button type="button" class="origins-evolution-next" data-magic-branch="${escapeHtml(branch.id)}" data-magic-stage="${stageIndex + 1}">
          <span class="origins-evolution-frame">${sprite('gameinter2-816')}</span>
          ${magicIcon(next.magicId, 'origins-evolution-mini-icon')}
          <span>${escapeHtml(magicInfo(next.magicId)?.name || next.name)}</span>
        </button>
      </div>
      <p>${branch.replacePrevious ? 'The new magic replaces the previous stage.' : 'The new stage keeps the earlier effects.'}</p>
    </div>`;
  }

  function renderLoading(className, text) {
    return `<div class="origins-mission-magic" data-origins-magic>
      ${sprite('interface-293', 'origins-mission-magic-bg')}
      <button type="button" class="origins-mission-close" data-magic-close>${sprite('interface-15')}</button>
      <div class="origins-mission-title">MAGIC</div>
      <div class="origins-mission-class">${escapeHtml(humanize(className))}</div>
      <div class="origins-mission-loading">${escapeHtml(text)}</div>
    </div>`;
  }

  function renderBook(className, config) {
    if (!config?.branches?.length) return renderLoading(className, 'No magic branches configured.');

    const pick = selected(config, className);
    const info = magicInfo(pick.stage.magicId);
    const description = info?.description || pick.stage.behavior || pick.branch.note || '';

    return `<div class="origins-mission-magic" data-origins-magic>
      ${sprite('interface-293', 'origins-mission-magic-bg')}
      <button type="button" class="origins-mission-close" data-magic-close aria-label="Close">${sprite('interface-15')}</button>
      <div class="origins-mission-title">MAGIC</div>
      <div class="origins-mission-class">${escapeHtml(humanize(className))}</div>

      <section class="origins-magic-tree-panel">
        <div class="origins-tree-heading">MAGIC EVOLUTION</div>
        <div class="origins-tree-scroll">
          ${config.branches.map(branch => renderBranch(branch, pick.branch.id, pick.stageIndex)).join('')}
        </div>
      </section>

      <aside class="origins-magic-detail">
        <div class="origins-detail-selected">
          <span class="origins-detail-selected-frame">${sprite('gameinter2-816')}</span>
          ${magicIcon(pick.stage.magicId, 'origins-detail-selected-icon')}
          <div class="origins-detail-selected-copy">
            <strong>${escapeHtml(info?.name || pick.stage.name)}</strong>
            <span>${escapeHtml(pick.branch.label)}</span>
          </div>
        </div>

        <div class="origins-detail-levels">
          ${renderLevel(pick.stage, 1)}
          ${renderLevel(pick.stage, 2)}
          ${renderLevel(pick.stage, 3)}
        </div>

        <div class="origins-detail-description">
          <span class="origins-detail-section-title">MAGIC</span>
          <p>${escapeHtml(description || 'No description available in MagicInfo.')}</p>
        </div>

        ${renderEvolution(pick.branch, pick.stageIndex)}
      </aside>
    </div>`;
  }

  function render(forceClass) {
    const className = String(forceClass || currentClass() || 'warrior').toLowerCase();
    ensureDesign(className);
    ensureMagicRuntime();

    if (designErrors[className]) return renderLoading(className, 'Could not load magic data.');
    if (!designCache[className]) return renderLoading(className, `Loading ${humanize(className)} magic...`);
    return renderBook(className, designCache[className]);
  }

  function applyWindowLayout() {
    const windowEl = document.getElementById('ui-window-magic');
    if (!windowEl) return;
    windowEl.classList.add('origins-mission-magic-window');
    if (windowEl.dataset.userMoved !== '1') {
      windowEl.style.left = `${Math.max(0, Math.round((innerWidth - 732) / 2))}px`;
      windowEl.style.top = `${Math.max(0, Math.round((innerHeight - 480) / 2) - 20)}px`;
    }
  }

  function refreshOpenBook() {
    const windowEl = document.getElementById('ui-window-magic');
    const body = windowEl?.querySelector('.ingame-window-body');
    if (!windowEl || !body || windowEl.hidden) return;
    applyWindowLayout();
    body.innerHTML = render(currentClass());
  }

  function handleClick(event) {
    if (event.target.closest('[data-magic-close]')) {
      G.IngameUI?.closeWindow?.('magic');
      return;
    }

    const className = currentClass();
    const config = designCache[className];
    if (!config) return;

    const branchLabel = event.target.closest('[data-magic-branch-label]');
    if (branchLabel) {
      const branchId = branchLabel.dataset.magicBranchLabel;
      if (config.branches.some(branch => branch.id === branchId)) {
        selectionByClass[className] = { branchId, stageIndex: 0 };
        refreshOpenBook();
      }
      return;
    }

    const node = event.target.closest('[data-magic-branch][data-magic-stage]');
    if (!node) return;

    const branchId = node.dataset.magicBranch;
    const stageIndex = Number(node.dataset.magicStage);
    const branch = config.branches.find(value => value.id === branchId);
    if (!branch || !Number.isFinite(stageIndex) || !branch.stages[stageIndex]) return;

    selectionByClass[className] = { branchId, stageIndex };
    refreshOpenBook();
  }

  function bindObserver() {
    if (observerBound) return;

    const windowEl = document.getElementById('ui-window-magic');
    const body = windowEl?.querySelector('.ingame-window-body');
    if (!windowEl || !body) {
      setTimeout(bindObserver, 0);
      return;
    }

    observerBound = true;

    new MutationObserver(() => {
      if (!windowEl.hidden) queueMicrotask(refreshOpenBook);
    }).observe(windowEl, { attributes: true, attributeFilter: ['hidden'] });

    new MutationObserver(() => {
      if (!windowEl.hidden && !body.querySelector('[data-origins-magic]')) queueMicrotask(refreshOpenBook);
    }).observe(body, { childList: true });
  }

  function init() {
    document.addEventListener('click', handleClick);
    ensureMagicRuntime();
    Object.keys(DESIGN_FILES).forEach(ensureDesign);
    bindObserver();
  }

  addEventListener('DOMContentLoaded', init, { once: true });

  return Object.freeze({
    render,
    refresh: refreshOpenBook,
    get runtime() { return magicRuntime; }
  });
})();
