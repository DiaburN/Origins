// MiniMapDialog overrides Draw() and does not draw TimeOfDayImage as a normal
// child. DrawTimeOfDay() first derives GameInter 210/212/214/216/218 from the
// live GameScene.TimeOfDay and only then draws the image. Constructor Index=0
// is therefore a sentinel, not neutral artwork. Do not request a fake #0 PNG.
const stage=document.querySelector('#stage');
let spec=null;

function item(){return spec?.windows?.find(value=>value.field==='MiniMapBox')||null}
function sourceContract(control){
  const p=control?.properties||{};
  return control?.name==='TimeOfDayImage'&&control?.type==='DXImageControl'&&p.LibraryFile==='LibraryFile.GameInter'&&String(p.Index).trim()==='0';
}
function install(root){
  if(!(root instanceof Element)||root.id!=='w-minimap'||!spec)return;
  const windowItem=item();if(!windowItem)return;
  const draw=spec.customDrawAudit?.entries?.find(entry=>entry.field==='MiniMapBox');
  if(draw?.policy!=='RUNTIME_MAP_DRAW')throw new Error(`MiniMap custom draw policy drifted: ${JSON.stringify(draw)}`);
  const index=(windowItem.controls||[]).findIndex(sourceContract);
  if(index<0)throw new Error('MiniMap TimeOfDayImage constructor sentinel contract drifted');
  const element=root.querySelector(`[data-control-index="${index}"]`);
  if(element)element.remove();
  root.dataset.sourceTimeOfDayDraw='DrawTimeOfDay runtime-only; constructor GameInter#0 sentinel suppressed';
  root.dataset.runtimeTimeOfDayInvented='false';
}
function scan(node){if(!(node instanceof Element))return;if(node.id==='w-minimap')queueMicrotask(()=>install(node));node.querySelectorAll?.('#w-minimap').forEach(root=>queueMicrotask(()=>install(root)))}
new MutationObserver(records=>records.forEach(record=>record.addedNodes.forEach(scan))).observe(stage,{childList:true,subtree:true});
fetch('ui-source-spec.json',{cache:'no-store'}).then(r=>{if(!r.ok)throw new Error(`ui-source-spec.json ${r.status}`);return r.json()}).then(value=>{spec=value;const root=document.querySelector('#w-minimap');if(root)install(root);console.info('ORIGINS MiniMap time-of-day runtime draw boundary active')}).catch(error=>console.error('Unable to apply MiniMap time-of-day fidelity',error));