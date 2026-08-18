// External visual-review harness for the reconstructed Zircon desktop.
// It is enabled only with ?review=1, lives outside #stage, and never injects
// game/player/server data or modifies source controls inside reconstructed windows.
const params=new URLSearchParams(window.location.search);
if(params.get('review')==='1'){
  const stage=document.querySelector('#stage');
  const closeAll=document.querySelector('[data-close-all]');
  const topActions=document.querySelector('.top-actions')||document.querySelector('.topbar');
  const sleep=ms=>new Promise(resolve=>setTimeout(resolve,ms));
  const waitFor=async(predicate,timeout=15000)=>{const start=performance.now();while(performance.now()-start<timeout){const value=predicate();if(value)return value;await sleep(25)}return null};
  const harness=document.createElement('div');
  harness.id='visual-review-harness';
  harness.dataset.externalReferenceTool='true';
  harness.style.cssText='display:flex;align-items:center;gap:5px;border:1px solid #715426;background:#100d09;padding:3px 6px;color:#d8b96d;font:10px Arial,sans-serif;white-space:nowrap';
  const previous=document.createElement('button');previous.type='button';previous.textContent='Prev';previous.dataset.reviewPrevious='true';
  const status=document.createElement('span');status.dataset.reviewStatus='true';status.style.cssText='min-width:180px;text-align:center;color:#e7c776';
  const next=document.createElement('button');next.type='button';next.textContent='Next';next.dataset.reviewNext='true';
  harness.append(previous,status,next);topActions?.prepend(harness);

  let entries=[];let current=-1;let moving=false;
  function visibleEntryButtons(){
    return [...document.querySelectorAll('.catalog-item[data-window-id]')].filter(button=>button.dataset.windowId);
  }
  function updateStatus(){
    const entry=entries[current];
    status.textContent=entry?`${current+1} / ${entries.length} — ${entry.dataset.windowId}`:`0 / ${entries.length}`;
    previous.disabled=current<=0;next.disabled=current<0||current>=entries.length-1;
    harness.dataset.reviewIndex=String(current);
    harness.dataset.reviewCount=String(entries.length);
    harness.dataset.reviewWindowId=entry?.dataset.windowId||'';
  }
  async function show(index,{focus=true}={}){
    if(moving||!entries.length)return;
    const target=Math.max(0,Math.min(entries.length-1,index));
    const entry=entries[target];if(!entry)return;
    moving=true;
    try{
      closeAll?.click();await sleep(20);
      entry.click();
      const id=entry.dataset.windowId;
      const root=await waitFor(()=>document.getElementById(`w-${CSS.escape(id)}`),4000);
      if(!root){status.textContent=`${target+1} / ${entries.length} — ${id} (not opened)`;return}
      current=target;updateStatus();
      const url=new URL(window.location.href);url.searchParams.set('review','1');url.searchParams.set('reviewWindow',id);history.replaceState(null,'',url);
      document.querySelectorAll('.catalog-item.review-current').forEach(node=>node.classList.remove('review-current'));
      entry.classList.add('review-current');entry.scrollIntoView({block:'nearest'});
      root.dataset.visualReviewTarget='true';
      if(focus)harness.focus?.();
    }finally{moving=false}
  }
  previous.addEventListener('click',()=>show(current-1));next.addEventListener('click',()=>show(current+1));
  window.addEventListener('keydown',event=>{
    if(event.defaultPrevented||event.metaKey||event.ctrlKey||event.altKey)return;
    const active=document.activeElement;if(active&&/^(INPUT|TEXTAREA|SELECT)$/.test(active.tagName))return;
    if(event.key==='ArrowLeft'){event.preventDefault();show(current-1)}
    else if(event.key==='ArrowRight'){event.preventDefault();show(current+1)}
  });

  waitFor(()=>{const found=visibleEntryButtons();return found.length>=80?found:null}).then(found=>{
    if(!found){status.textContent='Catalog unavailable';harness.dataset.reviewReady='false';return}
    entries=found;
    const requested=params.get('reviewWindow');
    const index=requested?entries.findIndex(button=>button.dataset.windowId===requested):0;
    harness.dataset.reviewReady='true';updateStatus();show(index>=0?index:0,{focus:false});
    console.info(`ORIGINS visual review harness ready: ${entries.length} windows; external to 1024x768 stage`);
  });

  // Deliberately no MutationObserver writing into #stage: reconstructed UI remains untouched.
  if(stage)stage.dataset.visualReviewHarnessExternal='true';
}
