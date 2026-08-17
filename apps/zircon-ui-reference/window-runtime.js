import { buildWindowLayout } from './layout-resolver-derived.js';

const stage = document.querySelector('#stage');
let zCounter = 100;
let sourceSpec = null;

function isWindow(element) {
  return element instanceof HTMLElement && (element.classList.contains('window') || element.classList.contains('generic-window'));
}

function focusWindow(root) {
  if (!isWindow(root)) return;
  zCounter += 1;
  root.style.zIndex = String(zCounter);
  document.querySelectorAll('.window.focused,.generic-window.focused').forEach(element => {
    if (element !== root) element.classList.remove('focused');
  });
  root.classList.add('focused');
}

function storageKey(root) {
  return root.id ? `origins-zircon-window:${root.id}` : null;
}

function restorePosition(root) {
  const key = storageKey(root);
  if (!key) return;
  try {
    const saved = JSON.parse(sessionStorage.getItem(key) || 'null');
    if (!saved || !Number.isFinite(saved.x) || !Number.isFinite(saved.y)) return;
    root.style.left = `${saved.x}px`;
    root.style.top = `${saved.y}px`;
  } catch {
    // A malformed transient browser value must never break the UI reference.
  }
}

function savePosition(root) {
  const key = storageKey(root);
  if (!key) return;
  const x = Number.parseFloat(root.style.left || '0');
  const y = Number.parseFloat(root.style.top || '0');
  if (!Number.isFinite(x) || !Number.isFinite(y)) return;
  sessionStorage.setItem(key, JSON.stringify({x, y}));
}

function clearCatalogState(root) {
  if (!isWindow(root) || !root.id?.startsWith('w-')) return;
  const id = root.id.slice(2);
  document.querySelector(`[data-window-id="${CSS.escape(id)}"]`)?.classList.remove('active');
}

function isInteractiveTarget(target) {
  return target instanceof Element && Boolean(target.closest('button,input,textarea,select,.close,.ui-button,.dx-generated-button,.dx-checkbox,.dx-scrollbar'));
}

function sourceItemForRoot(root) {
  if (!sourceSpec || !root?.id?.startsWith('w-')) return null;
  const id=root.id.slice(2);
  return [...(sourceSpec.windows||[]),...(sourceSpec.nestedWindows||[])].find(item=>item.id===id) || null;
}

function intersect(a,b) {
  const left=Math.max(a.left,b.left),top=Math.max(a.top,b.top),right=Math.min(a.right,b.right),bottom=Math.min(a.bottom,b.bottom);
  return {left,top,right,bottom,width:Math.max(0,right-left),height:Math.max(0,bottom-top)};
}

function sourceClipArea(node,layout) {
  let clip={left:node.x,top:node.y,right:node.x+node.width,bottom:node.y+node.height,width:node.width,height:node.height};
  let parent=node.parent;
  // Zircon DXControl.UpdateClipArea(): static controls intersect Parent.ClipArea;
  // top-level controls intersect the active scene. Drag-out exception is only
  // active while a parent itself is moving, which is not a child-layout state.
  while(parent) {
    const parentArea={left:parent.x,top:parent.y,right:parent.x+parent.width,bottom:parent.y+parent.height,width:parent.width,height:parent.height};
    clip=intersect(clip,parentArea);
    parent=parent.parent;
  }
  return clip;
}

function numericStyle(element,key,fallback) {
  const value=Number.parseFloat(element.style[key]||'');
  return Number.isFinite(value)?value:fallback;
}

function applyClipToElement(element,node,clip) {
  if (!(element instanceof HTMLElement) && !(element instanceof SVGElement)) return;
  const apply=()=>{
    const x=numericStyle(element,'left',node.x),y=numericStyle(element,'top',node.y);
    const width=numericStyle(element,'width',element.offsetWidth||node.width),height=numericStyle(element,'height',element.offsetHeight||node.height);
    const box={left:x,top:y,right:x+width,bottom:y+height,width,height};
    const visible=intersect(box,clip);
    element.dataset.sourceClipArea=`${clip.left},${clip.top},${clip.right},${clip.bottom}`;
    if(visible.width<=0||visible.height<=0) {
      element.style.visibility='hidden';
      element.dataset.sourceFullyClipped='true';
      return;
    }
    element.style.visibility='';
    element.dataset.sourceFullyClipped='false';
    const top=Math.max(0,visible.top-box.top),right=Math.max(0,box.right-visible.right),bottom=Math.max(0,box.bottom-visible.bottom),left=Math.max(0,visible.left-box.left);
    if(top||right||bottom||left) {
      element.style.clipPath=`inset(${top}px ${right}px ${bottom}px ${left}px)`;
      element.dataset.sourceClipApplied='true';
    } else {
      element.style.clipPath='';
      element.dataset.sourceClipApplied='false';
    }
  };
  apply();
  if(element instanceof HTMLImageElement && !element.complete) element.addEventListener('load',apply,{once:true});
}

function applySourceClipTree(root) {
  const item=sourceItemForRoot(root);
  if(!item||!sourceSpec) return;
  const layout=buildWindowLayout(sourceSpec,item);
  let applied=0;
  for(let i=0;i<layout.nodes.length;i++) {
    const node=layout.nodes[i];
    const element=root.querySelector(`[data-control-index="${i}"]`);
    if(!element) continue;
    applyClipToElement(element,node,sourceClipArea(node,layout));
    applied++;
  }
  root.dataset.sourceClipNodes=String(applied);
  root.dataset.sourceClipPolicy='DXControl.UpdateClipArea';
}

function installDrag(root) {
  if (!isWindow(root) || root.dataset.originsDesktopRuntime === '1') return;
  root.dataset.originsDesktopRuntime = '1';
  restorePosition(root);
  focusWindow(root);
  queueMicrotask(()=>applySourceClipTree(root));

  root.addEventListener('origins:focus', () => focusWindow(root));
  root.addEventListener('pointerdown', event => {
    focusWindow(root);
    if (event.button !== 0 || isInteractiveTarget(event.target)) return;

    const rect = root.getBoundingClientRect();
    const localY = event.clientY - rect.top;
    const explicitHandle = event.target instanceof Element && Boolean(event.target.closest('.window-title,.generic-window-header'));
    if (!explicitHandle && localY > 34) return;

    event.preventDefault();
    root.setPointerCapture?.(event.pointerId);

    const stageRect = stage.getBoundingClientRect();
    const startX = event.clientX;
    const startY = event.clientY;
    const startLeft = Number.parseFloat(root.style.left || '0');
    const startTop = Number.parseFloat(root.style.top || '0');

    const move = moveEvent => {
      const width = root.offsetWidth;
      const height = root.offsetHeight;
      const rawX = startLeft + (moveEvent.clientX - startX);
      const rawY = startTop + (moveEvent.clientY - startY);
      const maxX = Math.max(0, stageRect.width - Math.min(width, stageRect.width));
      const maxY = Math.max(0, stageRect.height - Math.min(34, height));
      root.style.left = `${Math.round(Math.max(0, Math.min(maxX, rawX)))}px`;
      root.style.top = `${Math.round(Math.max(0, Math.min(maxY, rawY)))}px`;
    };

    const end = endEvent => {
      root.releasePointerCapture?.(endEvent.pointerId);
      root.removeEventListener('pointermove', move);
      root.removeEventListener('pointerup', end);
      root.removeEventListener('pointercancel', end);
      savePosition(root);
    };

    root.addEventListener('pointermove', move);
    root.addEventListener('pointerup', end);
    root.addEventListener('pointercancel', end);
  });
}

function scan(node) {
  if (!(node instanceof Element)) return;
  if (isWindow(node)) installDrag(node);
  node.querySelectorAll?.('.window,.generic-window').forEach(installDrag);
}

function scanRemoved(node) {
  if (!(node instanceof Element)) return;
  if (isWindow(node)) clearCatalogState(node);
  node.querySelectorAll?.('.window,.generic-window').forEach(clearCatalogState);
}

new MutationObserver(records => {
  for (const record of records) {
    record.addedNodes.forEach(scan);
    record.removedNodes.forEach(scanRemoved);
  }
}).observe(stage, {childList: true, subtree: true});

fetch('ui-source-spec.json',{cache:'no-store'})
  .then(response=>{if(!response.ok)throw new Error(`ui-source-spec.json ${response.status}`);return response.json()})
  .then(spec=>{
    sourceSpec=spec;
    stage.querySelectorAll('.window,.generic-window').forEach(root=>{installDrag(root);applySourceClipTree(root)});
    console.info('ORIGINS source ClipArea runtime active (DXControl.UpdateClipArea policy)');
  })
  .catch(error=>console.error('Unable to load Zircon ClipArea manifest',error));

stage.querySelectorAll('.window,.generic-window').forEach(installDrag);

document.querySelector('#reset-layout')?.addEventListener('click', () => {
  for (const key of Object.keys(sessionStorage)) {
    if (key.startsWith('origins-zircon-window:')) sessionStorage.removeItem(key);
  }
});
