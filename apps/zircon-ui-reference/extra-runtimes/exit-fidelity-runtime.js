// Source-faithful ExitDialog behavior without pretending to execute application/server exits.
const stage=document.querySelector('#stage');
function control(root,name){return root?.querySelector?.(`[data-control-name="${CSS.escape(name)}"]`)||null}
function install(root){
  if(!root||root.id!=='w-exit'||root.dataset.sourceExitRuntime==='true')return;
  root.dataset.sourceExitRuntime='true';
  root.dataset.sourceModal='true';
  root.dataset.sourceCombatGateSeconds='10';
  root.dataset.sourceExitState='idle';

  const toSelect=control(root,'ToSelectButton');
  if(toSelect)toSelect.addEventListener('click',event=>{
    // Zircon checks MapObject.User.CombatTime + 10s, unless Observer, before C.Logout.
    // Combat/user state is unavailable in the reference viewer.
    event.preventDefault();event.stopImmediatePropagation();
    root.dataset.sourceExitState='logout-request-pending-runtime-check';
    root.dataset.sourceRuntimeCondition='CEnvir.Now >= MapObject.User.CombatTime.AddSeconds(10) || Observer';
    root.dataset.sourceNetworkAction='C.Logout';
    root.dataset.sourceNetworkActionExecuted='false';
  },true);

  const exit=control(root,'ExitButton');
  if(exit)exit.addEventListener('click',event=>{
    // Same combat gate, then Exiting=true and CEnvir.Target.Close(). Do not close the
    // browser/reference viewer: record the exact application-side action only.
    event.preventDefault();event.stopImmediatePropagation();
    root.dataset.sourceExitState='application-exit-pending-runtime-check';
    root.dataset.sourceRuntimeCondition='CEnvir.Now >= MapObject.User.CombatTime.AddSeconds(10) || Observer';
    root.dataset.sourceApplicationAction='Exiting=true; CEnvir.Target.Close()';
    root.dataset.sourceApplicationActionExecuted='false';
  },true);
}
function scan(node){if(!(node instanceof Element))return;if(node.id==='w-exit')queueMicrotask(()=>install(node));node.querySelectorAll?.('#w-exit').forEach(root=>queueMicrotask(()=>install(root)))}
new MutationObserver(records=>records.forEach(record=>record.addedNodes.forEach(scan))).observe(stage,{childList:true,subtree:true});
install(document.querySelector('#w-exit'));
console.info('ORIGINS ExitDialog fidelity runtime active: modal + combat-gated logout/exit remain runtime-neutral');
