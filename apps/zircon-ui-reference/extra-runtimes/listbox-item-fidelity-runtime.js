const stage = document.querySelector('#stage');

// Zircon DXListBoxItem is a structural row whose constructor creates a DXLabel.
// Current GameScene declarations attach these rows to a DXComboBox.ListBox.
// DXComboBox starts with Showing=false, so its list rows must not be drawn in
// the neutral desktop snapshot. Keep the source controls addressable in the DOM
// without leaking the generic UNMAPPED diagnostic text into the game window.
function normalizeSourceListBoxItem(element) {
  if (!(element instanceof HTMLElement)) return;
  if (element.dataset.controlType !== 'DXListBoxItem') return;
  if (element.dataset.sourceListBoxItemNormalized === 'true') return;

  element.classList.remove('unknown-control');
  element.classList.add('dx-listbox-item', 'dx-listbox-item-deferred');
  element.textContent = '';
  element.hidden = true;
  element.style.display = 'none';
  element.dataset.sourceListBoxItemNormalized = 'true';
  element.dataset.sourceInitialVisibility = 'combo-list-closed';
  element.dataset.runtimePayloadInvented = 'false';
}

function normalizeAllSourceListBoxItems(root = stage || document) {
  if (root instanceof HTMLElement && root.dataset.controlType === 'DXListBoxItem') {
    normalizeSourceListBoxItem(root);
  }
  root.querySelectorAll?.('[data-control-type="DXListBoxItem"]').forEach(normalizeSourceListBoxItem);
}

normalizeAllSourceListBoxItems();

if (stage) {
  const observer = new MutationObserver(records => {
    for (const record of records) {
      for (const node of record.addedNodes) {
        if (!(node instanceof HTMLElement)) continue;
        // patch_multiwindow_runtime_core tags rendered controls synchronously
        // before renderSourceWindow returns. Run after that call stack so the
        // stable source type/name metadata is present.
        queueMicrotask(() => normalizeAllSourceListBoxItems(node));
      }
    }
  });
  observer.observe(stage, { childList: true, subtree: true });
}
