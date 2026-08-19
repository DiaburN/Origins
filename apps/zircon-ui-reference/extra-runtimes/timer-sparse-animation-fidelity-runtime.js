// TimerDialog's constructor starts _eggTimer at GameInter 960 with six frames
// over 333ms. In the original GameInter.Zl, 961-964 are empty slots while 960
// and 965 contain artwork. MirLibrary therefore draws nothing for those middle
// frames. Keep the source timing/range, but never turn an empty .Zl slot into a
// broken PNG request. No timer/server payload is fabricated.
const stage=document.querySelector('#stage');
let spec=null;
const observers=new WeakMap();

function timerItem(){return spec?.windows?.find(item=>item.field==='TimerBox')||null}
function timerControl(item){
  const index=(item?.controls||[]).findIndex(control=>control.name==='_eggTimer'&&control.type==='DXAnimatedControl');
  return {index,control:index>=0?item.controls[index]:null};
}
function assertContract(item,control){
  const p=control?.properties||{};
  const expected={Index:'960',FrameCount:'6',AnimationDelay:'TimeSpan.FromMilliseconds(333)',LibraryFile:'LibraryFile.GameInter',Animated:'true',Loop:'false'};
  for(const [key,value] of Object.entries(expected))if(String(p[key]??'').trim()!==value)throw new Error(`Timer _eggTimer ${key} drifted: ${String(p[key]??'')}`);
  const meta=spec?.assetMeta?.GameInter||{};
  if(!meta['960']||!meta['965'])throw new Error('Timer populated GameInter 960/965 frame metadata missing');
  for(const frame of ['961','962','963','964'])if(meta[frame])throw new Error(`Timer GameInter ${frame} is no longer an empty .Zl frame`);
  if(item?.root?.Size!=='new Size(120, 100)')throw new Error(`Timer root size drifted: ${item?.root?.Size}`);
}
function frameFromSrc(image){
  const match=String(image.getAttribute('src')||'').match(/(?:^|\/)GameInter\/(\d+)\.png(?:$|[?#])/);
  return match?Number(match[1]):null;
}
function install(root){
  if(!(root instanceof Element)||root.id!=='w-timer'||!spec)return;
  const item=timerItem();if(!item)throw new Error('TimerBox missing from source manifest');
  const {index,control}=timerControl(item);if(index<0||!control)throw new Error('Timer _eggTimer missing from source manifest');
  assertContract(item,control);
  const image=root.querySelector(`img[data-control-index="${index}"]`);
  if(!(image instanceof HTMLImageElement)||observers.has(image))return;

  const state={lastGoodSrc:null,restoring:false};
  const sync=()=>{
    const raw=image.getAttribute('src')||'';
    const frame=frameFromSrc(image);
    if(frame===null||frame<960||frame>965)return;

    if(state.restoring){
      state.restoring=false;
      image.style.visibility='hidden';
      image.dataset.sourceSparseFrame='empty-zl-slot';
      return;
    }

    const frameMeta=spec?.assetMeta?.GameInter?.[String(frame)]||null;
    if(frameMeta?.width>0&&frameMeta?.height>0){
      state.lastGoodSrc=raw;
      image.style.visibility='';
      delete image.dataset.sourceSparseFrame;
      image.dataset.sourceSparseFrameArtwork='present';
      return;
    }

    // Exact .Zl empty frame: visually draw nothing while retaining a valid,
    // already-loaded source URI underneath the hidden element. This prevents
    // the browser from manufacturing a 404 that MirLibrary never performs.
    image.style.visibility='hidden';
    image.dataset.sourceSparseFrame='empty-zl-slot';
    image.dataset.sourceSparseFrameIndex=String(frame);
    if(state.lastGoodSrc&&raw!==state.lastGoodSrc){
      state.restoring=true;
      image.setAttribute('src',state.lastGoodSrc);
    }
  };

  const observer=new MutationObserver(records=>{
    if(records.some(record=>record.type==='attributes'&&record.attributeName==='src'))sync();
  });
  observer.observe(image,{attributes:true,attributeFilter:['src']});
  observers.set(image,observer);
  root.dataset.sourceTimerAnimation='GameInter 960-965 / 333ms / Loop=false; .Zl empty frames 961-964 draw nothing';
  root.dataset.runtimeTimerDataInvented='false';
  sync();
}
function scan(node){
  if(!(node instanceof Element))return;
  if(node.id==='w-timer')queueMicrotask(()=>install(node));
  node.querySelectorAll?.('#w-timer').forEach(root=>queueMicrotask(()=>install(root)));
}
new MutationObserver(records=>records.forEach(record=>record.addedNodes.forEach(scan))).observe(stage,{childList:true,subtree:true});
fetch('ui-source-spec.json',{cache:'no-store'})
  .then(response=>{if(!response.ok)throw new Error(`ui-source-spec.json ${response.status}`);return response.json()})
  .then(value=>{spec=value;const root=document.querySelector('#w-timer');if(root)install(root);console.info('ORIGINS Timer sparse .Zl animation fidelity active')})
  .catch(error=>console.error('Unable to apply Timer sparse animation fidelity',error));