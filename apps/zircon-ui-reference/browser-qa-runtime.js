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

  const run = async () => {
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
    console.info(`ORIGINS browser QA ${report.status.toUpperCase()}: ${report.testedWindows}/80 windows; failures=${failures.length}; browserErrors=${browserErrors.length}`);
  };

  run().catch(error => {
    const report = { status: 'fail', expectedWindows: 80, testedWindows: 0, failures: [{ id: 'runner', issue: String(error?.stack || error) }], warnings, browserErrors };
    resultNode.textContent = JSON.stringify(report, null, 2);
    resultNode.dataset.status = 'fail';
    resultNode.hidden = false;
    document.documentElement.dataset.browserQa = 'fail';
  });
}
