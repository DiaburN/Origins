// QA/runtime contracts belong in data-* attributes and the manifest, never as
// visible game text. This guard only strips known inspection placeholders; real
// source/resolved language labels are untouched.
const stage=document.querySelector('#stage');
const TECHNICAL_PATTERNS=[
  /runtime user data/i,
  /runtime colour palette texture/i,
  /runtime color palette texture/i,
  /runtime rows?/i,
  /source preview/i,
  /^UNMAPPED\b/i,
  /GameScene UI reference/i,
  /MiniMap runtime content/i,
  /Zircon GameInter desktop reference/i,
];

function isTechnical(text){const value=String(text??'').trim();return value&&TECHNICAL_PATTERNS.some(pattern=>pattern.test(value))}
function clean(element){
  if(!(element instanceof Element))return;
  if(element.children.length===0&&isTechnical(element.textContent)){
    element.dataset.sourceTechnicalTextRemoved=element.textContent.trim();
    element.textContent='';
  }
  for(const leaf of element.querySelectorAll('*:not(:has(*))')){
    if(!isTechnical(leaf.textContent))continue;
    leaf.dataset.sourceTechnicalTextRemoved=leaf.textContent.trim();leaf.textContent='';
  }
  for(const attr of ['title','aria-label']){
    for(const node of [element,...element.querySelectorAll(`[${attr}]`)]){
      const value=node.getAttribute?.(attr);if(isTechnical(value)){node.dataset.sourceTechnicalAttributeRemoved=value;node.removeAttribute(attr)}
    }
  }
}
new MutationObserver(records=>{for(const record of records){record.addedNodes.forEach(node=>{if(node instanceof Element)clean(node)});if(record.type==='characterData'&&record.target.parentElement)clean(record.target.parentElement)}}).observe(stage,{childList:true,subtree:true,characterData:true});
clean(stage);
console.info('ORIGINS stage technical-text guard active; QA contracts remain data-only');