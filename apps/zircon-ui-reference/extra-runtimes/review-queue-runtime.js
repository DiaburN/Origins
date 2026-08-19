// QA-shell-only sequential review control. It lives outside #stage and therefore
// never masquerades as Zircon game artwork. It lets the owner/reviewer walk the
// 80 source windows deterministically without searching the catalog each time.
const stage=document.querySelector('#stage');
const topActions=document.querySelector('.top-actions');
let ids=[],index=-1;
function currentRoot(){return index>=0?document.querySelector(`#w-${CSS.escape(ids[index])}`):null}
function catalogButton(id){return document.querySelector(`[data-window-id="${CSS.escape(id)}"]`)}
function openAt(next){if(!ids.length)return;index=(next%ids.length+ids.length)%ids.length;const id=ids[index];catalogButton(id)?.click();render()}
function render(){if(!panel)return;const id=index>=0?ids[index]:'—';counter.textContent=index>=0?`${index+1} / ${ids.length}`:`0 / ${ids.length}`;name.textContent=id;prev.disabled=!ids.length;next.disabled=!ids.length;open.disabled=!ids.length}
const panel=document.createElement('div');panel.className='source-review-queue';panel.dataset.qaShell='true';panel.style.display='inline-flex';panel.style.alignItems='center';panel.style.gap='6px';
const prev=document.createElement('button');prev.type='button';prev.textContent='◀';prev.title='Previous source window';
const next=document.createElement('button');next.type='button';next.textContent='▶';next.title='Next source window';
const open=document.createElement('button');open.type='button';open.textContent='Open';open.title='Open current source window';
const counter=document.createElement('span'),name=document.createElement('span');name.style.minWidth='120px';name.style.fontFamily='monospace';name.style.fontSize='11px';
panel.append(prev,counter,name,open,next);topActions?.append(panel);
prev.addEventListener('click',()=>openAt(index<0?ids.length-1:index-1));next.addEventListener('click',()=>openAt(index<0?0:index+1));open.addEventListener('click',()=>{if(index<0)openAt(0);else catalogButton(ids[index])?.click()});
document.addEventListener('keydown',event=>{if(event.target instanceof HTMLElement&&(event.target.isContentEditable||/INPUT|TEXTAREA|SELECT/.test(event.target.tagName)))return;if(event.key===']'){event.preventDefault();openAt(index<0?0:index+1)}else if(event.key==='['){event.preventDefault();openAt(index<0?ids.length-1:index-1)}});
fetch('ui-source-spec.json',{cache:'no-store'}).then(r=>{if(!r.ok)throw new Error(`ui-source-spec.json ${r.status}`);return r.json()}).then(spec=>{ids=[...(spec.windows||[]),...(spec.nestedWindows||[])].map(item=>item.id).filter(Boolean);if(ids.length!==80)console.warn(`ORIGINS review queue expected 80 source windows, got ${ids.length}`);render();console.info(`ORIGINS sequential source review queue ready: ${ids.length} windows; [ / ] shortcuts`)}).catch(error=>{panel.hidden=true;console.error('Unable to load source review queue',error)});
render();
