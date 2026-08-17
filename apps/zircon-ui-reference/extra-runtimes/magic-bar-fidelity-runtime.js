// Deterministic neutral behavior for MagicBarDialog's constructor loop.
// Spell icons, school borders and cooldowns remain player runtime data.
const stage=document.querySelector('#stage');
let spec=null;

function itemFor(root){
  if(!spec||!root?.id?.startsWith('w-'))return null;
  const id=root.id.slice(2);return [...(spec.windows||[]),...(spec.nestedWindows||[])].find(item=>item.id===id)||null;
}
function controlElement(root,name){return root.querySelector(`[data-control-name="${CSS.escape(name)}"]`)}
function styleSlotLabel(label){
  label.style.position='absolute';label.style.right='8px';label.style.bottom='7px';
  label.style.fontFamily='"MS Sans Serif",Arial,sans-serif';label.style.fontSize='10.6667px';label.style.fontStyle='italic';
  label.style.color='#fff';label.style.textShadow='1px 0 #000,0 1px #000,-1px 0 #000,0 -1px #000';label.style.pointerEvents='none';label.style.zIndex='4';
}
function install(root){
  if(!(root instanceof Element)||root.id!=='w-magic-bar')return;
  const item=itemFor(root);if(!item?.magicBarSourceLoop)return;
  if(root.dataset.sourceMagicBarRuntime==='true')return;
  root.dataset.sourceMagicBarRuntime='true';root.dataset.runtimeMagicData='neutral/no fabricated player spells';

  for(let slot=1;slot<=12;slot++){
    const border=controlElement(root,`MagicBarSlotBorder${String(slot).padStart(2,'0')}`);if(!border)continue;
    if(border.querySelector(':scope > .source-magicbar-key'))continue;
    const label=document.createElement('span');label.className='source-magicbar-key';label.textContent=String(slot);styleSlotLabel(label);border.append(label);
  }

  const setLabel=controlElement(root,'SetLabel');
  let spellSet=1;
  const showSet=()=>{if(setLabel){setLabel.textContent=String(spellSet);setLabel.dataset.sourceSpellSet='true'}};
  showSet();
  const up=controlElement(root,'UpButton'),down=controlElement(root,'DownButton');
  up?.addEventListener('click',event=>{event.preventDefault();event.stopPropagation();spellSet=Math.max(1,spellSet-1);showSet()});
  down?.addEventListener('click',event=>{event.preventDefault();event.stopPropagation();spellSet=Math.min(4,spellSet+1);showSet()});
  root.dataset.sourceMagicBarSlots='24 source slots; 12 constructor-visible; Config.ShowMagicBarFrames=true';
}
function scan(node){
  if(!(node instanceof Element))return;
  if(node.id==='w-magic-bar')queueMicrotask(()=>install(node));
  node.querySelectorAll?.('#w-magic-bar').forEach(root=>queueMicrotask(()=>install(root)));
}
new MutationObserver(records=>records.forEach(record=>record.addedNodes.forEach(scan))).observe(stage,{childList:true,subtree:true});
fetch('ui-source-spec.json',{cache:'no-store'}).then(r=>{if(!r.ok)throw new Error(`ui-source-spec.json ${r.status}`);return r.json()}).then(value=>{spec=value;const root=document.querySelector('#w-magic-bar');if(root)install(root);console.info('ORIGINS MagicBar neutral constructor-loop runtime active')}).catch(error=>console.error('Unable to load MagicBar fidelity manifest',error));