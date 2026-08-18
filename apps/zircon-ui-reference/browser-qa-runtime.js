const params = new URLSearchParams(window.location.search);

if (params.get('qa') === '1') {
  const stage = document.querySelector('#stage');
  const closeAll = document.querySelector('[data-close-all]');
  const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
  const failures = [];
  const warnings = [];
  const browserErrors = [];

  window.addEventListener('error', event => {
    browserErrors.push(String(event.error?.stack || event.message || 'window error'));
  });
  window.addEventListener('unhandledrejection', event => {
    browserErrors.push(String(event.reason?.stack || event.reason || 'unhandled rejection'));
  });

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

  const syntheticTechnicalText = text => {
    const patterns = [
      /\bUNMAPPED\b/i,
      /\bruntime data\b/i,
      /\bsource preview\b/i,
      /\bregistry only\b/i,
      /\bruntime-only\b/i,
    ];
    return patterns.filter(pattern => pattern.test(text)).map(pattern => pattern.source);
  };

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
    if (!sourceStatus) {
      failures.push({
        id: 'source-status',
        issue: `Full generated manifest did not become active: ${document.querySelector('#source-status')?.textContent?.trim() || '(missing)'}`,
      });
    }

    let qaSpec = null;
    let gameControlCount = 0;
    let nestedControlCount = 0;
    try {
      const response = await fetch('ui-source-spec.json', { cache: 'no-store' });
      if (!response.ok) throw new Error(`ui-source-spec.json ${response.status}`);
      qaSpec = await response.json();
      if ((qaSpec.windows || []).length !== 65 || (qaSpec.nestedWindows || []).length !== 15) {
        failures.push({ id: 'manifest', issue: `Manifest inventory mismatch: ${(qaSpec.windows || []).length}+${(qaSpec.nestedWindows || []).length}` });
      }
      gameControlCount = (qaSpec.windows || []).reduce((sum, item) => sum + (item.controls || []).length, 0);
      nestedControlCount = (qaSpec.nestedWindows || []).reduce((sum, item) => sum + (item.controls || []).length, 0);
      if (gameControlCount < 2507) failures.push({ id: 'manifest', issue: `Expanded GameScene control coverage regressed: ${gameControlCount} < 2507` });
      if (nestedControlCount < 143) failures.push({ id: 'manifest', issue: `Nested control coverage regressed: ${nestedControlCount} < 143` });
      if (qaSpec.finalSupplementalSourceMatrix?.passed !== true) failures.push({ id: 'manifest', issue: 'Final supplemental source matrix missing/not PASS in built artifact' });
      if (qaSpec.finalSupplementalSourceMatrix?.minimumGameSceneControls !== 2507) failures.push({ id: 'manifest', issue: `Final source floor mismatch: ${JSON.stringify(qaSpec.finalSupplementalSourceMatrix)}` });
      if (qaSpec.deterministicSourceRowAudit?.passed !== true) failures.push({ id: 'manifest', issue: 'Deterministic source row audit missing/not PASS in built artifact' });
      if (qaSpec.guildMemberRowAudit?.passed !== true) failures.push({ id: 'manifest', issue: 'Guild member deterministic row audit missing/not PASS in built artifact' });
      if (qaSpec.guildRootHelperAudit?.passed !== true) failures.push({ id: 'manifest', issue: 'Guild root helper audit missing/not PASS in built artifact' });
      if (qaSpec.gameStoreCompositeAudit?.passed !== true) failures.push({ id: 'manifest', issue: 'GameStore composite audit missing/not PASS in built artifact' });
      if (qaSpec.communicationReceivedRowAudit?.passed !== true) failures.push({ id: 'manifest', issue: 'Communication received-row audit missing/not PASS in built artifact' });
      if (qaSpec.consignmentCompositeAudit?.passed !== true) failures.push({ id: 'manifest', issue: 'Consignment compatibility audit missing/not PASS in built artifact' });
      if (qaSpec.consignmentDeterministicAudit?.passed !== true) failures.push({ id: 'manifest', issue: 'Consignment strict deterministic audit missing/not PASS in built artifact' });
      if (qaSpec.currencyTreeAudit?.passed !== true) failures.push({ id: 'manifest', issue: 'Currency tree audit missing/not PASS in built artifact' });
      if (qaSpec.companionBonusRowAudit?.passed !== true) failures.push({ id: 'manifest', issue: 'Companion bonus-row audit missing/not PASS in built artifact' });
      if (qaSpec.npcQuestListRowAudit?.passed !== true) failures.push({ id: 'manifest', issue: 'NPC quest-list row audit missing/not PASS in built artifact' });
      if (qaSpec.helpMenuShellAudit?.passed !== true) failures.push({ id: 'manifest', issue: 'Help menu shell audit missing/not PASS in built artifact' });
      if (qaSpec.anonymousConstructorControlAudit?.passed !== true) failures.push({ id: 'manifest', issue: 'Anonymous constructor control audit missing/not PASS in built artifact' });
      if (qaSpec.targetTypedCustomControlAudit?.passed !== true) failures.push({ id: 'manifest', issue: 'Target-typed custom control audit missing/not PASS in built artifact' });
      if (qaSpec.customCompositeInventory?.passed !== true) failures.push({ id: 'manifest', issue: 'Custom composite inventory missing/not PASS in built artifact' });
      if (qaSpec.directCustomCompositeInventory?.passed !== true) failures.push({ id: 'manifest', issue: 'Direct custom composite inventory missing/not PASS in built artifact' });
      if (qaSpec.uiCreationHelperInventory?.passed !== true) failures.push({ id: 'manifest', issue: 'UI creation helper inventory missing/not PASS in built artifact' });
      if (qaSpec.sourceSearchFlowAudit?.passed !== true) failures.push({ id: 'manifest', issue: 'Source search flow audit missing/not PASS in built artifact' });
      const rowAudit = qaSpec.deterministicSourceRowAudit || {};
      if (rowAudit.rankingRows !== 12 || rowAudit.dungeonRows !== 9 || rowAudit.fortuneRows !== 9 || rowAudit.bigMapRows !== 48) {
        failures.push({ id: 'manifest', issue: `Deterministic row matrix mismatch: ${JSON.stringify(rowAudit)}` });
      }
      const guildRows = qaSpec.guildMemberRowAudit || {};
      if (guildRows.headerRows !== 1 || guildRows.memberRows !== 17 || guildRows.sourceControls !== 108 || guildRows.netControlsAdded !== 107) {
        failures.push({ id: 'manifest', issue: `Guild deterministic member row matrix mismatch: ${JSON.stringify(guildRows)}` });
      }
      const guildRoot = qaSpec.guildRootHelperAudit || {};
      if (guildRoot.deterministicControls !== 16 || guildRoot.panels !== 6 || guildRoot.buttons !== 10 || guildRoot.runtimeCastlePanelsInvented !== false || guildRoot.clickCreatedModalsInvented !== false) {
        failures.push({ id: 'manifest', issue: `Guild root helper matrix mismatch: ${JSON.stringify(guildRoot)}` });
      }
      const gameStore = qaSpec.gameStoreCompositeAudit || {};
      if (gameStore.deterministicControls !== 215 || gameStore.itemRows !== 10 || gameStore.topRows !== 5 || gameStore.runtimeStoreInfoInvented !== false || gameStore.runtimeItemsInvented !== false) {
        failures.push({ id: 'manifest', issue: `GameStore deterministic composite matrix mismatch: ${JSON.stringify(gameStore)}` });
      }
      const communication = qaSpec.communicationReceivedRowAudit || {};
      if (communication.rows !== 5 || communication.deterministicControls !== 25 || communication.runtimeMailInvented !== false) {
        failures.push({ id: 'manifest', issue: `Communication received-row matrix mismatch: ${JSON.stringify(communication)}` });
      }
      const consignment = qaSpec.consignmentCompositeAudit || {};
      if (consignment.contractVersion !== 2 || consignment.deterministicControls !== 135 || consignment.headerLabels !== 10 || consignment.itemTypeButtons !== 38 || consignment.searchRows !== 6 || consignment.consignRows !== 6 || consignment.runtimeMarketInfoInvented !== false || consignment.runtimeItemsInvented !== false) {
        failures.push({ id: 'manifest', issue: `Consignment compatibility matrix mismatch: ${JSON.stringify(consignment)}` });
      }
      const consignmentStrict = qaSpec.consignmentDeterministicAudit || {};
      if (consignmentStrict.deterministicControls !== 135 || consignmentStrict.headerLabels !== 10 || consignmentStrict.itemTypeButtons !== 38 || consignmentStrict.searchRows !== 6 || consignmentStrict.consignRows !== 6 || consignmentStrict.runtimeMarketInfoInvented !== false) {
        failures.push({ id: 'manifest', issue: `Consignment strict deterministic matrix mismatch: ${JSON.stringify(consignmentStrict)}` });
      }
      const groupLfg = qaSpec.windows?.find(item => item.field === 'GroupBox')?.groupLFGRowAudit || {};
      if (groupLfg.passed !== true || groupLfg.rows !== 5 || groupLfg.deterministicControls !== 20 || groupLfg.runtimeLfgInvented !== false) {
        failures.push({ id: 'manifest', issue: `Group LFG deterministic row matrix mismatch: ${JSON.stringify(groupLfg)}` });
      }
      const currency = qaSpec.currencyTreeAudit || {};
      if (currency.deterministicControls !== 2 || currency.runtimeHeadersInvented !== false || currency.runtimeCurrencyItemsInvented !== false || currency.runtimeCurrencyDataInvented !== false) {
        failures.push({ id: 'manifest', issue: `Currency tree deterministic matrix mismatch: ${JSON.stringify(currency)}` });
      }
      const companion = qaSpec.companionBonusRowAudit || {};
      if (companion.rows !== 7 || companion.deterministicControls !== 21 || companion.targetTypedNewSource !== true || companion.runtimeBonusStatsInvented !== false || companion.runtimeBonusTextInvented !== false) {
        failures.push({ id: 'manifest', issue: `Companion deterministic bonus matrix mismatch: ${JSON.stringify(companion)}` });
      }
      const npcQuest = qaSpec.npcQuestListRowAudit || {};
      if (npcQuest.rows !== 6 || npcQuest.deterministicControls !== 18 || npcQuest.blankRowsVisibleAtConstruction !== true || npcQuest.runtimeQuestInfoInvented !== false || npcQuest.runtimeUserQuestInvented !== false || npcQuest.runtimeQuestTextInvented !== false) {
        failures.push({ id: 'manifest', issue: `NPC quest-list deterministic matrix mismatch: ${JSON.stringify(npcQuest)}` });
      }
      const helpMenu = qaSpec.helpMenuShellAudit || {};
      if (helpMenu.deterministicControls !== 2 || helpMenu.runtimeButtonsInvented !== false || helpMenu.runtimeHelpContainersInvented !== false || helpMenu.runtimeHelpTabsInvented !== false || helpMenu.runtimeHelpItemsInvented !== false || helpMenu.runtimeHelpInfoInvented !== false) {
        failures.push({ id: 'manifest', issue: `Help menu deterministic shell mismatch: ${JSON.stringify(helpMenu)}` });
      }
      const anonymous = qaSpec.anonymousConstructorControlAudit || {};
      if (anonymous.parserSyntheticSmokePassed !== true || anonymous.sourceAnonymousControls !== anonymous.manifestAnonymousControls || anonymous.tradeAnonymousGoldLabels !== 2 || anonymous.runtimePayloadsInvented !== false) {
        failures.push({ id: 'manifest', issue: `Anonymous constructor coverage mismatch: ${JSON.stringify(anonymous)}` });
      }
      const targetTyped = qaSpec.targetTypedCustomControlAudit || {};
      if (targetTyped.allResolvedCustomControlsMaterialized !== true || Number(targetTyped.resolvedCustomCreations || 0) < 7 || targetTyped.eventCallbackBodiesExcluded !== true || targetTyped.runtimePayloadsInvented !== false) {
        failures.push({ id: 'manifest', issue: `Target-typed custom coverage mismatch: ${JSON.stringify(targetTyped)}` });
      }
      const custom = qaSpec.customCompositeInventory || {};
      if (custom.version !== 3 || custom.constructorAndHelperReachability !== true || custom.eventCallbacksExcluded !== true || custom.runtimePayloadsInvented !== false) {
        failures.push({ id: 'manifest', issue: `Custom composite inventory mismatch: ${JSON.stringify(custom)}` });
      }
      const direct = qaSpec.directCustomCompositeInventory || {};
      if (direct.allDirectCustomTypesMaterialized !== true || direct.eventCallbackBodiesExcluded !== true || direct.runtimePayloadsInvented !== false) {
        failures.push({ id: 'manifest', issue: `Direct custom composite coverage mismatch: ${JSON.stringify(direct)}` });
      }
      const helperAudit = qaSpec.uiCreationHelperInventory || {};
      if (helperAudit.version !== 2 || helperAudit.chatOptionsAddNewTabDeferredLocal !== true || helperAudit.helpPagesRemainRuntimeBound !== true || helperAudit.magicTabsRemainRuntimeBound !== true || helperAudit.knownBigMapHelpersMaterialized !== true || helperAudit.guildConstructorHelpersMaterialized !== true || helperAudit.guildWarRuntimeCastlePanelsRemainNeutral !== true || helperAudit.eventCallbacksExcludedFromCreationClassification !== true || helperAudit.staticGlobalsDoNotImplyRuntimeData !== true) {
        failures.push({ id: 'manifest', issue: `UI helper boundary matrix mismatch: ${JSON.stringify(helperAudit)}` });
      }
    } catch (error) {
      failures.push({ id: 'manifest', issue: String(error?.stack || error) });
    }
    const specById = new Map([...(qaSpec?.windows || []), ...(qaSpec?.nestedWindows || [])].map(item => [item.id, item]));

    const buttons = await waitFor(() => {
      const found = [...document.querySelectorAll('.catalog-item[data-window-id]')];
      return found.length >= 80 ? found : null;
    }, 15000);

    if (!buttons) {
      failures.push({ id: 'catalog', issue: `Expected 80 catalog entries, found ${document.querySelectorAll('.catalog-item[data-window-id]').length}` });
    } else {
      const ids = buttons.map(button => button.dataset.windowId);
      if (ids.length !== 80 || new Set(ids).size !== 80) {
        failures.push({ id: 'catalog', issue: `Window identity mismatch: ${ids.length} entries / ${new Set(ids).size} unique` });
      }

      for (const id of ids) {
        closeAll?.click();
        await sleep(10);
        const button = document.querySelector(`.catalog-item[data-window-id="${CSS.escape(id)}"]`);
        if (!button) {
          failures.push({ id, issue: 'Catalog button disappeared' });
          continue;
        }

        button.click();
        const root = await waitFor(() => document.getElementById(`w-${id}`), 3000);
        if (!root) {
          failures.push({ id, issue: 'Window root was not created' });
          continue;
        }

        await sleep(40);
        const images = await waitForImages(root);
        const rect = root.getBoundingClientRect();
        if (!(rect.width > 0 && rect.height > 0)) {
          failures.push({ id, issue: `Invalid root size ${rect.width}x${rect.height}` });
        }

        const stageRect = stage?.getBoundingClientRect();
        if (stageRect) {
          const intersects = rect.right > stageRect.left && rect.left < stageRect.right && rect.bottom > stageRect.top && rect.top < stageRect.bottom;
          if (!intersects) failures.push({ id, issue: 'Window does not intersect the 1024x768 stage' });
        }

        const broken = [...new Set(images.filter(image => image.complete && image.naturalWidth === 0).map(image => image.getAttribute('src') || '(empty src)'))];
        if (broken.length) failures.push({ id, issue: 'Broken image assets', assets: broken });

        const text = root.innerText || '';
        const technical = syntheticTechnicalText(text);
        if (technical.length) failures.push({ id, issue: 'Technical/reference text leaked into game window', patterns: technical });

        const sourceItem = specById.get(id);
        if (!sourceItem) {
          failures.push({ id, issue: 'Window not present in generated source manifest' });
        } else {
          const internalNames = new Set((sourceItem.controls || []).map(control => String(control.name || '').trim()).filter(Boolean));
          const leakedNames = [...new Set([...root.querySelectorAll('*')]
            .map(directText)
            .filter(value => value && internalNames.has(value)))];
          if (leakedNames.length) failures.push({ id, issue: 'C# control name leaked as visible game text', names: leakedNames });
        }

        const syntheticTitle = [...root.querySelectorAll('.generic-window-title,.window-title,.generic-title')]
          .map(node => node.textContent?.trim())
          .filter(Boolean)
          .find(value => value === root.dataset.sourceField || value === root.dataset.sourceClass);
        if (syntheticTitle) failures.push({ id, issue: `Internal source name leaked as title: ${syntheticTitle}` });

        const visibleUnmapped = [...root.querySelectorAll('.unmapped-control,[data-unmapped="true"]')].filter(node => {
          const style = getComputedStyle(node);
          const r = node.getBoundingClientRect();
          return style.display !== 'none' && style.visibility !== 'hidden' && Number(style.opacity) !== 0 && r.width > 0 && r.height > 0;
        });
        if (visibleUnmapped.length) failures.push({ id, issue: `Visible unmapped controls: ${visibleUnmapped.length}` });

        const controls = root.querySelectorAll('[data-control-index]').length;
        if (controls === 0 && !['main-panel'].includes(id)) warnings.push({ id, issue: 'No tagged source controls rendered' });
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
    console.info(`ORIGINS browser QA ${report.status.toUpperCase()}: ${report.testedWindows}/80 windows; controls=${gameControlCount}+${nestedControlCount}; failures=${failures.length}; browserErrors=${browserErrors.length}`);
  };

  run().catch(error => {
    const report = { status: 'fail', expectedWindows: 80, testedWindows: 0, sourceStatus: null, gameControlCount: 0, nestedControlCount: 0, failures: [{ id: 'runner', issue: String(error?.stack || error) }], warnings, browserErrors };
    resultNode.textContent = JSON.stringify(report, null, 2);
    resultNode.dataset.status = 'fail';
    resultNode.hidden = false;
    document.documentElement.dataset.browserQa = 'fail';
  });
}
