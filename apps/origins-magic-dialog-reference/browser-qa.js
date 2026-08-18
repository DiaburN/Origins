const qaEnabled = new URLSearchParams(location.search).get('qa') === '1';

if (qaEnabled) {
  const failures = [];
  const browserErrors = [];
  const expectedCounts = {Warrior:17,Wizard:25,Taoist:25,Assassin:17,Archer:21,Monk:9};

  addEventListener('error', event => browserErrors.push(String(event.error?.stack || event.message || event.error || 'window error')));
  addEventListener('unhandledrejection', event => browserErrors.push(String(event.reason?.stack || event.reason || 'unhandled rejection')));

  const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
  const fail = (id, issue, details={}) => failures.push({id, issue, ...details});
  const approx = (actual, expected, tolerance=0.75) => Math.abs(actual-expected) <= tolerance;

  async function waitForReady() {
    for (let i=0;i<200;i++) {
      const status = document.querySelector('#qa-status')?.textContent || '';
      if (status.includes('114 spells')) return true;
      if (status.startsWith('ERROR:')) throw new Error(status);
      await sleep(50);
    }
    throw new Error('MagicDialog did not become ready');
  }

  async function waitForImages(root) {
    const images = [...root.querySelectorAll('img')];
    await Promise.all(images.map(async image => {
      if (image.complete) return;
      await new Promise(resolve => {
        image.addEventListener('load', resolve, {once:true});
        image.addEventListener('error', resolve, {once:true});
      });
    }));
    return images;
  }

  async function run() {
    await waitForReady();
    const dialog = document.querySelector('#magic-dialog');
    if (!dialog) throw new Error('Magic dialog missing');

    const dialogBox = dialog.getBoundingClientRect();
    if (!approx(dialogBox.width,419) || !approx(dialogBox.height,511))
      fail('geometry.dialog','MagicDialog geometry mismatch',{actual:[dialogBox.width,dialogBox.height],expected:[419,511]});

    const tabs = [...document.querySelectorAll('.class-tab')];
    if (tabs.length !== 6) fail('tabs.count','Expected six class tabs',{actual:tabs.length});

    const classReport = {};
    for (const className of Object.keys(expectedCounts)) {
      const tab = tabs.find(node => node.dataset.class === className);
      if (!tab) { fail(`class.${className}`,'Class tab missing'); continue; }
      tab.click();
      await sleep(25);

      const selected = [...document.querySelectorAll('.class-tab[aria-selected="true"]')];
      if (selected.length !== 1 || selected[0]?.dataset.class !== className)
        fail(`class.${className}.selected`,'Selected tab state is not exclusive',{selected:selected.map(x=>x.dataset.class)});

      if (document.querySelector('#active-class-name')?.textContent !== className)
        fail(`class.${className}.label`,'Active class label mismatch');

      const cells = [...document.querySelectorAll('.magic-cell')];
      const expected = expectedCounts[className];
      if (cells.length !== expected)
        fail(`class.${className}.count`,'Spell cell count mismatch',{actual:cells.length,expected});

      for (const [index,cell] of cells.entries()) {
        const box = cell.getBoundingClientRect();
        if (!approx(box.width,369) || !approx(box.height,54)) {
          fail(`class.${className}.cell.${index}`,'MagicCell geometry mismatch',{actual:[box.width,box.height],expected:[369,54]});
          break;
        }
      }

      await waitForImages(document.querySelector('#list-inner'));
      const iconImages = [...document.querySelectorAll('.magic-icon')];
      const emptyIcons = [...document.querySelectorAll('.magic-icon-empty')];
      const expectedEmpty = className === 'Wizard' ? 1 : 0;
      if (emptyIcons.length !== expectedEmpty)
        fail(`class.${className}.source-empty`,'Unexpected source-incomplete icon count',{actual:emptyIcons.length,expected:expectedEmpty});
      if (iconImages.length !== expected - expectedEmpty)
        fail(`class.${className}.icons`,'Rendered real icon count mismatch',{actual:iconImages.length,expected:expected-expectedEmpty});

      const broken = iconImages.filter(image => !image.complete || image.naturalWidth <= 0 || image.naturalHeight <= 0);
      if (broken.length)
        fail(`class.${className}.icon-load`,'One or more Crystal MagIcon2 frames failed to load',{sources:broken.map(x=>x.getAttribute('src'))});

      classReport[className] = {
        cells: cells.length,
        realIcons: iconImages.length,
        sourceIncompleteIcons: emptyIcons.length,
      };
    }

    // Exercise the real navigation controls on a long list.
    tabs.find(node => node.dataset.class === 'Wizard')?.click();
    await sleep(25);
    const inner = document.querySelector('#list-inner');
    const before = inner?.style.transform || '';
    document.querySelector('.scroll-down')?.click();
    await sleep(25);
    const afterButton = inner?.style.transform || '';
    if (before === afterButton) fail('scroll.button','Down scroll button did not move the list',{before,after:afterButton});

    const viewport = document.querySelector('#list-viewport');
    const beforeWheel = inner?.style.transform || '';
    viewport?.dispatchEvent(new WheelEvent('wheel',{deltaY:120,bubbles:true,cancelable:true}));
    await sleep(25);
    const afterWheel = inner?.style.transform || '';
    if (beforeWheel === afterWheel) fail('scroll.wheel','Mouse wheel did not move the list',{before:beforeWheel,after:afterWheel});

    const allImages = await waitForImages(dialog);
    const brokenShell = allImages.filter(image => !image.complete || image.naturalWidth <= 0 || image.naturalHeight <= 0);
    if (brokenShell.length)
      fail('artwork.load','One or more Zircon/Crystal assets failed to load',{sources:brokenShell.map(x=>x.getAttribute('src'))});

    const report = {
      status: failures.length || browserErrors.length ? 'fail' : 'pass',
      testedClasses: 6,
      testedSpells: Object.values(classReport).reduce((sum,item)=>sum+item.cells,0),
      classReport,
      geometry: {dialog:[dialogBox.width,dialogBox.height],cell:[369,54]},
      scroll: {buttonMoved:before!==afterButton,wheelMoved:beforeWheel!==afterWheel},
      failures,
      browserErrors,
    };

    const pre = document.createElement('pre');
    pre.id = 'magic-browser-qa-result';
    pre.textContent = JSON.stringify(report);
    pre.style.display = 'none';
    document.body.append(pre);
  }

  run().catch(error => {
    const pre = document.createElement('pre');
    pre.id = 'magic-browser-qa-result';
    pre.textContent = JSON.stringify({status:'fail',testedClasses:0,testedSpells:0,failures:[{id:'runner',issue:String(error?.stack||error)}],browserErrors});
    pre.style.display = 'none';
    document.body.append(pre);
  });
}
