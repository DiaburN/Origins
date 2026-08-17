// Root DXImageControl windows must obey their own source properties. The legacy
// viewer added a synthetic field-name title, close button and drop shadow to
// every image-backed window; Zircon does not.
const stage=document.querySelector('#stage');
let spec=null;

function boolFrom(raw,fallback){const v=String(raw??'').trim().toLowerCase();return v==='true'?true:v==='false'?false:fallback}
function floatFrom(raw,fallback){const v=String(raw??'').trim().replace(/[fFdDmM]$/,'');return /^-?(?:\d+(?:\.\d*)?|\.\d+)$/.test(v)?Number(v):fallback}
function itemFor(root){if(!spec||!root?.id?.startsWith('w-'))return null;const id=root.id.slice(2);return [...(spec.windows||[]),...(spec.nestedWindows||[])].find(item=>item.id===id)||null}
function apply(root){
  if(!(root instanceof Element)||!root.classList.contains('window'))return;
  const item=itemFor(root);if(!item)return;const p=item.root||{};

  // addImageWindow() inspection chrome is not part of DXImageControl.
  root.querySelectorAll(':scope > .window-title').forEach(element=>element.remove());
  root.querySelectorAll(':scope > img.close:not([data-control-index])').forEach(element=>element.remove());

  const background=root.querySelector(':scope > img.window-img');
  const drawImage=boolFrom(p.DrawImage,true);
  const opacity=Math.max(0,Math.min(1,floatFrom(p.ImageOpacity,1)));
  const gray=boolFrom(p.GrayScale,false);
  const enabled=boolFrom(p.IsEnabled,true);
  const dropShadow=boolFrom(p.DropShadow,false);
  if(background){
    background.style.display=drawImage?'':'none';
    background.style.opacity=String(opacity);
    const filters=[];if(gray||!enabled)filters.push('grayscale(1)');if(!enabled)filters.push(`brightness(${75/255})`);
    background.style.filter=filters.join(' ');
  }
  root.style.filter=dropShadow?'drop-shadow(0 0 8px rgba(0,0,0,.5))':'none';
  root.dataset.sourceRootImage=`draw=${drawImage}; opacity=${opacity}; gray=${gray}; enabled=${enabled}; shadow=${dropShadow}`;
  root.dataset.sourceSyntheticChromeRemoved='field-title, synthetic-close';
}
function scan(node){if(!(node instanceof Element))return;if(node.matches?.('.window'))queueMicrotask(()=>apply(node));node.querySelectorAll?.('.window').forEach(root=>queueMicrotask(()=>apply(root)))}
new MutationObserver(records=>records.forEach(record=>record.addedNodes.forEach(scan))).observe(stage,{childList:true,subtree:true});
fetch('ui-source-spec.json',{cache:'no-store'}).then(r=>{if(!r.ok)throw new Error(`ui-source-spec.json ${r.status}`);return r.json()}).then(value=>{spec=value;stage.querySelectorAll('.window').forEach(apply);console.info('ORIGINS root DXImageControl window fidelity active')}).catch(error=>console.error('Unable to load root image-window fidelity manifest',error));