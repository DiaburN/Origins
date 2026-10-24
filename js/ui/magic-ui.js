window.G = window.G || {};

G.MagicUI = (() => {
  const A = G.GameUiAssets || { sheets: {}, sprites: {} };

  const DESIGN_FILES = Object.freeze({
    warrior: 'data/magics/origins-warrior-evolution.json',
    wizard: 'data/magics/origins-elemental-evolution.json',
    taoist: 'data/magics/origins-taoist-evolution.json',
    assassin: 'data/magics/origins-assassin-evolution.json'
  });

  const HEADER_INDEX = Object.freeze({
    warrior: 160,
    wizard: 161,
    taoist: 162,
    assassin: 163
  });

  const designCache = Object.create(null);
  const designErrors = Object.create(null);
  const designPromises = Object.create(null);
  const selectedBranchByClass = Object.create(null);
  const selectedStageByClass = Object.create(null);

  let magicRuntime = null;
  let magicRuntimePromise = null;
  let magicRuntimeError = null;
  let observerBound = false;

  function escapeHtml(value) {
    return String(value ?? '').replace(/[&<>'"]/g, char => ({
      '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;'
    })[char]);
  }

  function currentClass() {
    const character = G.Session?.currentCharacter?.() || {};
    return String(character.className || '').toLowerCase();
  }

  function humanize(value) {
    const text = String(value || '').replace(/([a-z0-9])([A-Z])/g, '$1 $2').replace(/[_-]+/g, ' ');
    return text ? text.charAt(0).toUpperCase() + text.slice(1) : 'Magic';
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
        magicRuntimeError = null;
        refreshOpenBook();
        return data;
      })
      .catch(error => {
        magicRuntimeError = error;
        magicRuntime = null;
        console.warn('Magic runtime not available yet:', error);
        refreshOpenBook();
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
      const stages = (source.stages || []).map((value, index) => {
        const fallbackName = source.evolution?.[index] || '';
        return stage(
          value.sourceMagic || fallbackName,
          value.sourceMagicId,
          value.role,
          value.originsBehavior || source.designNote || ''
        );
      }).filter(value => value.name && Number.isFinite(value.magicId));

      if (stages.length) {
        branches.push({
          id,
          label: humanize(id),
          stages,
          replacePrevious: true,
          note: source.designNote || ''
        });
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
      if (!stages.length) continue;

      branches.push({
        id,
        label: humanize(id),
        stages,
        replacePrevious: data.rules?.evolutionReplacesPreviousSkill !== false,
        note: source.designNote || ''
      });
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
        const name = id.charAt(0).toUpperCase() + id.slice(1);
        stages = [stage(name, source.sourceMagicId, '', source.designNote || '')];
      } else if (source.sourceMagicIds) {
        const mainName = Object.keys(source.sourceMagicIds).find(name => !name.startsWith('Augment'));
        if (mainName) stages = [stage(mainName, source.sourceMagicIds[mainName], '', source.designNote || '')];
      }

      stages = stages.filter(value => value.name && Number.isFinite(value.magicId));
      if (!stages.length) continue;

      branches.push({
        id,
        label: humanize(id),
        stages,
        replacePrevious: source.stacking !== 'cumulative',
        note: source.designNote || ''
      });
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
      if (!stages.length) return;
      branches.push({ id, label, stages, replacePrevious: true, note: source.designNote || '' });
    }

    addEvolution('primaryLotusCombo', 'Lotus Combo', core.primaryLotusCombo, () => core.primaryLotusCombo?.originsBehavior?.rotation || '');

    if (core.cloak?.activeSkill && core.cloak?.sourceMagicIds?.[core.cloak.activeSkill]) {
      branches.push({
        id: 'cloak',
        label: 'Cloak',
        stages: [stage('Cloak', core.cloak.sourceMagicIds.Cloak, '', core.cloak.designNote || '')],
        replacePrevious: true,
        note: core.cloak.designNote || ''
      });
    }

    addEvolution('fireFarm', 'Fire / Farm', core.fireFarm, name => core.fireFarm?.originsBehavior?.[name] || '');
    addEvolution('mobilityExecution', 'Mobility / Execution', core.mobilityExecution);
    addEvolution('areaClear', 'Area Clear', core.areaClear);

    return { className: 'assassin', branches };
  }

  function magicInfo(magicId) {
    return magicRuntime?.byMagicId?.[String(magicId)] || null;
  }

  function playerProgress(magicId, displayLevel) {
    const source = G.PlayerMagicRuntime?.byMagicId?.[magicId] || G.PlayerMagicRuntime?.byMagicId?.[String(magicId)];
    if (!source) return null;

    const levelData = source.levels?.[displayLevel] || source.levels?.[displayLevel - 1] || source.expByLevel?.[displayLevel];
    if (levelData) {
      const current = levelData.currentExp ?? levelData.current ?? levelData.experience;
      return Number.isFinite(Number(current)) ? Number(current) : null;
    }

    const currentLevel = Number(source.displayLevel ?? source.level);
    const current = source.currentExp ?? source.experience;
    if (Number.isFinite(currentLevel) && (currentLevel === displayLevel || currentLevel + 1 === displayLevel) && Number.isFinite(Number(current))) {
      return Number(current);
    }

    return null;
  }

  function magicIcon(magicId, extraClass = '') {
    const info = magicInfo(magicId);
    const icon = info?.icon;
    const sheet = magicRuntime?.sheet;

    if (icon && sheet) {
      return `<i class="origins-real-magic-icon ${extraClass}" aria-hidden="true" style="width:${icon.w}px;height:${icon.h}px;background-image:url('${sheet}');background-position:-${icon.x}px -${icon.y}px"></i>`;
    }

    return `<span class="origins-magic-icon-empty ${extraClass}" data-magic-id="${magicId}" title="Magic icon unavailable"></span>`;
  }

  function tabDefinitions(className) {
    switch (className) {
      case 'wizard':
        return [
          { branch: 'fire', off: 174, on: 175, label: 'Fire' },
          { branch: 'ice', off: 176, on: 177, label: 'Ice' },
          { branch: 'lightning', off: 178, on: 179, label: 'Lightning' },
          { branch: 'wind', off: 180, on: 181, label: 'Wind' }
        ];
      case 'taoist':
        return [
          { branch: 'holy', off: 184, on: 185, label: 'Holy' },
          { branch: 'dark', off: 186, on: 187, label: 'Dark' }
        ];
      case 'assassin':
        return [
          { branch: 'primaryLotusCombo', off: 188, on: 189, label: 'Physical' },
          { branch: 'fireFarm', off: 190, on: 191, label: 'Atrocity' },
          { branch: 'areaClear', off: 192, on: 193, label: 'Kill' },
          { branch: 'mobilityExecution', off: 194, on: 195, label: 'Assassination' }
        ];
      case 'warrior':
      default:
        return [{ branch: null, off: 166, on: 167, label: 'Active' }];
    }
  }

  function renderTabs(className, selectedBranch) {
    return tabDefinitions(className).map(tab => {
      const selected = tab.branch == null || tab.branch === selectedBranch;
      const art = sprite(`interface-${selected ? tab.on : tab.off}`);
      if (tab.branch == null) {
        return `<span class="origins-school-tab is-static" title="${escapeHtml(tab.label)}">${art}</span>`;
      }
      return `<button type="button" class="origins-school-tab${selected ? ' is-selected' : ''}" data-magic-tab="${escapeHtml(tab.branch)}" title="${escapeHtml(tab.label)}">${art}</button>`;
    }).join('');
  }

  function selectedBranch(className, config) {
    let id = selectedBranchByClass[className];
    let found = config.branches.find(value => value.id === id);
    if (!found) {
      found = config.branches[0] || null;
      id = found?.id || '';
      selectedBranchByClass[className] = id;
      selectedStageByClass[className] = 0;
    }
    return found;
  }

  function selectedStage(className, branch) {
    let index = Number(selectedStageByClass[className] ?? 0);
    if (!Number.isFinite(index)) index = 0;
    index = Math.max(0, Math.min(branch.stages.length - 1, index));
    selectedStageByClass[className] = index;
    return { index, value: branch.stages[index] };
  }

  function renderBranchRow(className, item, selectedId, selectedIndex) {
    const active = item.id === selectedId;
    const index = active ? selectedIndex : 0;
    const current = item.stages[index] || item.stages[0];
    const next = item.stages[index + 1] || null;

    return `<button type="button" class="origins-magic-branch${active ? ' is-selected' : ''}" data-magic-branch="${escapeHtml(item.id)}">
      ${sprite('interface-165', 'origins-cell-art')}
      ${magicIcon(current.magicId, 'origins-list-icon')}
      <span class="origins-branch-name">${escapeHtml(current.name)}</span>
      <span class="origins-branch-meta">${escapeHtml(next ? `Next: ${next.name}` : item.label)}</span>
    </button>`;
  }

  function renderLevel(currentStage, displayLevel) {
    const info = magicInfo(currentStage.magicId);
    const required = Number(info?.experience?.[displayLevel - 1]);
    const needLevel = Number(info?.needLevels?.[displayLevel - 1]);
    const current = playerProgress(currentStage.magicId, displayLevel);
    const hasRequired = Number.isFinite(required) && required > 0;
    const hasCurrent = Number.isFinite(current) && current >= 0;
    const percent = hasRequired && hasCurrent ? Math.max(0, Math.min(100, (current / required) * 100)) : 0;

    return `<div class="origins-level-row">
      <div class="origins-level-top">
        <strong>Level ${displayLevel}</strong>
        <span>Actual ${hasCurrent ? current : '--'} / Required ${hasRequired ? required : '--'}</span>
      </div>
      <div class="origins-level-sub">${Number.isFinite(needLevel) && needLevel > 0 ? `Character Lv ${needLevel}` : '&nbsp;'}</div>
      <div class="origins-exp-track">
        <span class="origins-exp-empty">${sprite('gameinter2-812')}</span>
        <span class="origins-exp-fill-clip" style="width:${percent.toFixed(2)}%">${sprite('gameinter2-812')}</span>
      </div>
    </div>`;
  }

  function renderStageButton(value, index, selectedIndex) {
    return `<button type="button" class="origins-stage-button${index === selectedIndex ? ' is-selected' : ''}" data-magic-stage="${index}" title="${escapeHtml(value.name)}">
      ${magicIcon(value.magicId, 'origins-stage-icon')}
      <span>${escapeHtml(value.name)}</span>
    </button>`;
  }

  function renderLoading(className, message) {
    const header = HEADER_INDEX[className] || 160;
    return `<div class="origins-magic-book" data-origins-magic>
      <section class="origins-magic-main">
        ${sprite(`interface-${header}`, 'origins-header-art')}
        ${sprite('interface-164', 'origins-background-art')}
        <button class="origins-magic-close" type="button" data-magic-close aria-label="Close">${sprite('interface-15')}</button>
        <div class="origins-magic-title">MAGIC</div>
        <div class="origins-magic-loading">${escapeHtml(message)}</div>
      </section>
      <aside class="origins-magic-progress">
        <div class="origins-progress-header-clip">${sprite(`interface-${header}`, 'origins-progress-header-art')}</div>
        <div class="origins-progress-bg-clip">${sprite('interface-164', 'origins-progress-bg-art')}</div>
        <div class="origins-progress-title">PROGRESS / EVOLUTION</div>
      </aside>
    </div>`;
  }

  function renderBook(className, config) {
    if (!config?.branches?.length) return renderLoading(className, 'No magic branches configured.');

    const branch = selectedBranch(className, config);
    if (!branch) return renderLoading(className, 'No magic branches configured.');

    const selected = selectedStage(className, branch);
    const currentStage = selected.value;
    const next = branch.stages[selected.index + 1] || null;
    const info = magicInfo(currentStage.magicId);
    const header = HEADER_INDEX[className] || 160;
    const description = info?.description || currentStage.behavior || branch.note || '';

    return `<div class="origins-magic-book" data-origins-magic>
      <section class="origins-magic-main">
        ${sprite(`interface-${header}`, 'origins-header-art')}
        ${sprite('interface-164', 'origins-background-art')}
        <button class="origins-magic-close" type="button" data-magic-close aria-label="Close">${sprite('interface-15')}</button>
        <div class="origins-magic-title">MAGIC</div>
        <nav class="origins-magic-tabs">${renderTabs(className, branch.id)}</nav>

        <div class="origins-branch-list">
          ${config.branches.map(item => renderBranchRow(className, item, branch.id, selected.index)).join('')}
        </div>

        <div class="origins-scroll-art" aria-hidden="true">
          ${sprite('interface-61', 'origins-scroll-up')}
          ${sprite('interface-60', 'origins-scroll-position')}
          ${sprite('interface-62', 'origins-scroll-down')}
        </div>
      </section>

      <aside class="origins-magic-progress">
        <div class="origins-progress-header-clip">${sprite(`interface-${header}`, 'origins-progress-header-art')}</div>
        <div class="origins-progress-bg-clip">${sprite('interface-164', 'origins-progress-bg-art')}</div>
        <div class="origins-progress-title">PROGRESS / EVOLUTION</div>

        <div class="origins-selected-magic">
          ${sprite('interface-165', 'origins-selected-cell-art')}
          ${magicIcon(currentStage.magicId, 'origins-selected-icon')}
          <div class="origins-selected-copy">
            <strong>${escapeHtml(info?.name || currentStage.name)}</strong>
            <span>${escapeHtml(currentStage.role || branch.label)}</span>
          </div>
        </div>

        <div class="origins-level-list">
          ${renderLevel(currentStage, 1)}
          ${renderLevel(currentStage, 2)}
          ${renderLevel(currentStage, 3)}
        </div>

        <div class="origins-current-effect">
          <span class="origins-caption">CURRENT MAGIC</span>
          <p>${escapeHtml(description || 'No description available in the current data.')}</p>
        </div>

        <div class="origins-evolution-block">
          <span class="origins-caption">EVOLUTION</span>
          <div class="origins-evolution-card${next ? '' : ' is-final'}">
            ${sprite('interface-165', 'origins-evolution-cell-art')}
            ${next ? magicIcon(next.magicId, 'origins-evolution-icon') : ''}
            <div class="origins-evolution-copy">
              <small>${next ? 'After Level 3' : 'Final stage'}</small>
              <strong>${escapeHtml(next ? next.name : currentStage.name)}</strong>
            </div>
          </div>
        </div>

        <div class="origins-branch-path">
          <span class="origins-caption">${escapeHtml(branch.label.toUpperCase())}</span>
          <div class="origins-stage-buttons">
            ${branch.stages.map((value, index) => renderStageButton(value, index, selected.index)).join('<span class="origins-stage-arrow">›</span>')}
          </div>
          <p>${branch.replacePrevious ? 'After Level 3, the next evolution replaces the previous magic.' : 'This branch is cumulative: earlier effects remain when the next stage is learned.'}</p>
        </div>
      </aside>
    </div>`;
  }

  function render(forceClass) {
    const className = String(forceClass || currentClass() || 'warrior').toLowerCase();
    ensureDesign(className);
    ensureMagicRuntime();

    if (designErrors[className]) return renderLoading(className, 'Could not load magic design data.');
    if (!designCache[className]) return renderLoading(className, `Loading ${humanize(className)} magic...`);

    return renderBook(className, designCache[className]);
  }

  function applyWindowLayout() {
    const windowEl = document.getElementById('ui-window-magic');
    if (!windowEl) return;
    windowEl.classList.add('origins-magic-expanded');
    if (windowEl.dataset.userMoved !== '1') {
      windowEl.style.left = `${Math.max(0, Math.round((innerWidth - 720) / 2))}px`;
      windowEl.style.top = `${Math.max(0, Math.min(72, innerHeight - 512))}px`;
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
    const close = event.target.closest('[data-magic-close]');
    if (close) {
      G.IngameUI?.closeWindow?.('magic');
      return;
    }

    const className = currentClass();
    const config = designCache[className];
    if (!config) return;

    const tab = event.target.closest('[data-magic-tab]');
    if (tab) {
      const id = tab.dataset.magicTab;
      if (config.branches.some(branch => branch.id === id)) {
        selectedBranchByClass[className] = id;
        selectedStageByClass[className] = 0;
        refreshOpenBook();
      }
      return;
    }

    const branchButton = event.target.closest('[data-magic-branch]');
    if (branchButton) {
      const id = branchButton.dataset.magicBranch;
      if (config.branches.some(branch => branch.id === id)) {
        selectedBranchByClass[className] = id;
        selectedStageByClass[className] = 0;
        refreshOpenBook();
      }
      return;
    }

    const stageButton = event.target.closest('[data-magic-stage]');
    if (stageButton) {
      const index = Number(stageButton.dataset.magicStage);
      if (Number.isFinite(index)) {
        selectedStageByClass[className] = index;
        refreshOpenBook();
      }
    }
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
      if (!windowEl.hidden) {
        queueMicrotask(refreshOpenBook);
      }
    }).observe(windowEl, { attributes: true, attributeFilter: ['hidden'] });

    new MutationObserver(() => {
      if (!windowEl.hidden && !body.querySelector('[data-origins-magic]')) {
        queueMicrotask(refreshOpenBook);
      }
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
    get runtime() { return magicRuntime; },
    get runtimeError() { return magicRuntimeError; }
  });
})();
