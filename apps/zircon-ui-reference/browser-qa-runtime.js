const params = new URLSearchParams(window.location.search);

if (params.get('qa') === '1') {
  const stage = document.querySelector('#stage');
  const closeAll = document.querySelector('[data-close-all]');
  const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
  const failures = [];
  const warnings = [];
  const browserErrors = [];
  const VALIDATED_GAME = 2674;
  const VALIDATED_NESTED = 149;
  const EVIDENCE_SHA = '40d5140805bede9f1c7c5af8c2fb0cefc284856c';
  const EVIDENCE_RUN = 32175607481;

  window.addEventListener('error', event => browserErrors.push(String(event.error?.stack || event.message || 'window error')));
  window.addEventListener('unhandledrejection', event => browserErrors.push(String(event.reason?.stack || event.reason || 'unhandled rejection')));

  const resultNode = document.createElement('pre');
  resultNode.id = 'browser-qa-result';
  resultNode.dataset.status = 'running';
  resultNode.hidden = true;
  document.body.append(resultNode);

  const waitFor = async (predicate, timeoutMs = 10000, intervalMs = 25) => {
    const started = performance.now();
    while (performance.now() - started < timeoutMs) {
      const value = predicate();
      if (value) return value;
      await sleep(intervalMs);
    }
    return null;
  };

  const waitForImages = async root => {
    const images = [...root.querySelectorAll('img')];
    await Promise.all(images.map(async image => {
      if (image.complete) return;
      await Promise.race([
        new Promise(resolve => {
          image.addEventListener('load', resolve, { once: true });
          image.addEventListener('error', resolve, { once: true });
        }),
        sleep(1500),
      ]);
    }));
    return images;
  };

  const technicalPatterns = [
    /\bUNMAPPED\b/i,
    /\bruntime data\b/i,
    /\bsource preview\b/i,
    /\bregistry only\b/i,
    /\bruntime-only\b/i,
  ];
  const directText = element => [...element.childNodes]
    .filter(node => node.nodeType === Node.TEXT_NODE)
    .map(node => node.nodeValue || '')
    .join(' ')
    .trim();

  const run = async () => {
    const sourceStatus = await waitFor(() => {
      const text = document.querySelector('#source-status')?.textContent?.trim() || '';
      return /65 GameScene \+ 15 nested\/transient/.test(text) ? text : null;
    }, 15000);
    if (!sourceStatus) failures.push({ id: 'source-status', issue: 'Full 65+15 generated manifest did not become active' });

    let spec = null;
    let gameControlCount = 0;
    let nestedControlCount = 0;
    try {
      const response = await fetch('ui-source-spec.json', { cache: 'no-store' });
      if (!response.ok) throw new Error(`ui-source-spec.json ${response.status}`);
      spec = await response.json();
      if ((spec.windows || []).length !== 65 || (spec.nestedWindows || []).length !== 15) {
        failures.push({ id: 'manifest', issue: `Manifest inventory mismatch: ${(spec.windows || []).length}+${(spec.nestedWindows || []).length}` });
      }
      gameControlCount = (spec.windows || []).reduce((sum, item) => sum + (item.controls || []).length, 0);
      nestedControlCount = (spec.nestedWindows || []).reduce((sum, item) => sum + (item.controls || []).length, 0);
      if (gameControlCount < VALIDATED_GAME) failures.push({ id: 'manifest', issue: `GameScene controls ${gameControlCount} < validated ${VALIDATED_GAME}` });
      if (nestedControlCount < VALIDATED_NESTED) failures.push({ id: 'manifest', issue: `Nested controls ${nestedControlCount} < validated ${VALIDATED_NESTED}` });

      const pending = gameControlCount !== VALIDATED_GAME || nestedControlCount !== VALIDATED_NESTED;
      const floor = spec.currentSourceControlFloor || {};
      const final = spec.finalSupplementalSourceMatrix || {};
      const floorExpected = {
        passed: true,
        gameScene: gameControlCount,
        nested: nestedControlCount,
        browserValidatedGameScene: VALIDATED_GAME,
        browserValidatedNested: VALIDATED_NESTED,
        browserValidationPending: pending,
        browserValidationEvidenceSha: EVIDENCE_SHA,
        browserValidationEvidenceRun: EVIDENCE_RUN,
      };
      for (const [key, value] of Object.entries(floorExpected)) {
        if (floor[key] !== value) failures.push({ id: 'manifest', issue: `Current floor ${key}=${JSON.stringify(floor[key])}, expected ${JSON.stringify(value)}` });
      }
      const finalExpected = {
        passed: true,
        gameSceneControls: gameControlCount,
        nestedControls: nestedControlCount,
        minimumGameSceneControls: VALIDATED_GAME,
        minimumNestedControls: VALIDATED_NESTED,
        latestSourceAuditedGameSceneFloor: gameControlCount,
        latestSourceAuditedNestedFloor: nestedControlCount,
        browserValidatedGameSceneFloor: VALIDATED_GAME,
        browserValidatedNestedFloor: VALIDATED_NESTED,
        browserValidatedFloorPending: pending,
        browserValidationEvidenceSha: EVIDENCE_SHA,
        browserValidationEvidenceRun: EVIDENCE_RUN,
      };
      for (const [key, value] of Object.entries(finalExpected)) {
        if (final[key] !== value) failures.push({ id: 'manifest', issue: `Final matrix ${key}=${JSON.stringify(final[key])}, expected ${JSON.stringify(value)}` });
      }

      const requiredPasses = [
        'deterministicSourceRowAudit', 'guildMemberRowAudit', 'guildRootHelperAudit', 'gameStoreCompositeAudit',
        'communicationReceivedRowAudit', 'consignmentCompositeAudit', 'consignmentDeterministicAudit', 'currencyTreeAudit',
        'companionBonusRowAudit', 'npcQuestListRowAudit', 'helpMenuShellAudit', 'anonymousConstructorControlAudit',
        'targetTypedCustomControlAudit', 'customCompositeInventory', 'directCustomCompositeInventory', 'uiCreationHelperInventory',
        'sourceSearchFlowAudit', 'browserQaWorkflowAudit', 'visualReviewWorkflowAudit',
      ];
      for (const key of requiredPasses) if (spec[key]?.passed !== true) failures.push({ id: 'manifest', issue: `${key} missing/not PASS` });

      const ranking = (spec.windows || []).find(item => item.field === 'RankingBox');
      if (ranking?.rankingSourceState?.sourceIndex !== 211 || ranking?.rankingSourceState?.fullRanking !== true) {
        failures.push({ id: 'manifest', issue: `Ranking current-source variant drifted: ${JSON.stringify(ranking?.rankingSourceState || {})}` });
      }
      const guild = spec.guildMemberRowAudit || {};
      if (guild.sourceControls !== 108 || guild.netControlsAdded !== 108 || guild.replacedIncompleteCompositeControls !== 0) {
        failures.push({ id: 'manifest', issue: `Guild deterministic tree drifted: ${JSON.stringify(guild)}` });
      }
      const helpers = spec.uiCreationHelperInventory || {};
      if (helpers.version !== 3 || helpers.helperCount !== 56 || helpers.deferredHelperCount !== 35 || helpers.runtimePayloadsInvented !== false) {
        failures.push({ id: 'manifest', issue: `Helper inventory drifted: ${JSON.stringify(helpers)}` });
      }
    } catch (error) {
      failures.push({ id: 'manifest', issue: String(error?.stack || error) });
    }

    const specById = new Map([...(spec?.windows || []), ...(spec?.nestedWindows || [])].map(item => [item.id, item]));
    const buttons = await waitFor(() => {
      const found = [...document.querySelectorAll('.catalog-item[data-window-id]')];
      return found.length >= 80 ? found : null;
    }, 15000);

    if (!buttons) {
      failures.push({ id: 'catalog', issue: `Expected 80 catalog entries, found ${document.querySelectorAll('.catalog-item[data-window-id]').length}` });
    } else {
      const ids = buttons.map(button => button.dataset.windowId);
      if (ids.length !== 80 || new Set(ids).size !== 80) failures.push({ id: 'catalog', issue: `Window identity mismatch: ${ids.length}/${new Set(ids).size}` });

      for (const id of ids) {
        closeAll?.click();
        await sleep(10);
        document.querySelector(`.catalog-item[data-window-id="${CSS.escape(id)}"]`)?.click();
        const root = await waitFor(() => document.getElementById(`w-${id}`), 3000);
        if (!root) {
          failures.push({ id, issue: 'Window root was not created' });
          continue;
        }
        await sleep(40);
        const images = await waitForImages(root);
        const rect = root.getBoundingClientRect();
        if (!(rect.width > 0 && rect.height > 0)) failures.push({ id, issue: `Invalid root size ${rect.width}x${rect.height}` });

        const stageRect = stage?.getBoundingClientRect();
        if (stageRect) {
          const intersects = rect.right > stageRect.left && rect.left < stageRect.right && rect.bottom > stageRect.top && rect.top < stageRect.bottom;
          if (!intersects) failures.push({ id, issue: 'Window does not intersect the 1024x768 stage' });
        }

        const broken = [...new Set(images.filter(image => image.complete && image.naturalWidth === 0).map(image => image.getAttribute('src') || '(empty src)'))];
        if (broken.length) failures.push({ id, issue: 'Broken image assets', assets: broken });

        const text = root.innerText || '';
        const technical = technicalPatterns.filter(pattern => pattern.test(text)).map(pattern => pattern.source);
        if (technical.length) failures.push({ id, issue: 'Technical/reference text leaked into game window', patterns: technical });

        const sourceItem = specById.get(id);
        if (!sourceItem) {
          failures.push({ id, issue: 'Window not present in generated source manifest' });
        } else {
          const internalNames = new Set((sourceItem.controls || []).map(control => String(control.name || '').trim()).filter(Boolean));
          const leakedNames = [...new Set([...root.querySelectorAll('*')].map(directText).filter(value => value && internalNames.has(value)))];
          if (leakedNames.length) failures.push({ id, issue: 'C# control name leaked as visible game text', names: leakedNames });
        }

        const syntheticTitle = [...root.querySelectorAll('.generic-window-title,.window-title,.generic-title')]
          .map(node => node.textContent?.trim()).filter(Boolean)
          .find(value => value === root.dataset.sourceField || value === root.dataset.sourceClass);
        if (syntheticTitle) failures.push({ id, issue: `Internal source name leaked as title: ${syntheticTitle}` });

        const visibleUnmapped = [...root.querySelectorAll('.unmapped-control,[data-unmapped="true"]')].filter(node => {
          const style = getComputedStyle(node);
          const r = node.getBoundingClientRect();
          return style.display !== 'none' && style.visibility !== 'hidden' && Number(style.opacity) !== 0 && r.width > 0 && r.height > 0;
        });
        if (visibleUnmapped.length) failures.push({ id, issue: `Visible unmapped controls: ${visibleUnmapped.length}` });

        const controls = root.querySelectorAll('[data-control-index]').length;
        if (controls === 0 && id !== 'main-panel') warnings.push({ id, issue: 'No tagged source controls rendered' });
      }
    }

    closeAll?.click();
    const report = {
      status: failures.length || browserErrors.length ? 'fail' : 'pass',
      expectedWindows: 80,
      testedWindows: buttons?.length || 0,
      sourceStatus: sourceStatus || null,
      gameControlCount,
      nestedControlCount,
      browserValidatedGameFloor: VALIDATED_GAME,
      browserValidatedNestedFloor: VALIDATED_NESTED,
      failures,
      warnings,
      browserErrors,
      generatedAt: new Date().toISOString(),
    };
    resultNode.textContent = JSON.stringify(report, null, 2);
    resultNode.dataset.status = report.status;
    resultNode.dataset.testedWindows = String(report.testedWindows);
    resultNode.hidden = false;
    document.documentElement.dataset.browserQa = report.status;
    console.info(`ORIGINS browser QA ${report.status.toUpperCase()}: ${report.testedWindows}/80; controls=${gameControlCount}+${nestedControlCount}; failures=${failures.length}; errors=${browserErrors.length}`);
  };

  run().catch(error => {
    const report = { status: 'fail', expectedWindows: 80, testedWindows: 0, gameControlCount: 0, nestedControlCount: 0, failures: [{ id: 'runner', issue: String(error?.stack || error) }], warnings, browserErrors };
    resultNode.textContent = JSON.stringify(report, null, 2);
    resultNode.dataset.status = 'fail';
    resultNode.hidden = false;
    document.documentElement.dataset.browserQa = 'fail';
  });
}
