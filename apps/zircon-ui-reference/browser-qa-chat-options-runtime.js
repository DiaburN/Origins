const params=new URLSearchParams(window.location.search);

if(params.get('qaChatOptions')==='1'){
  const sleep=ms=>new Promise(resolve=>setTimeout(resolve,ms));
  const result=document.createElement('pre');result.id='chat-options-qa-result';result.dataset.status='running';result.hidden=true;document.body.append(result);
  const failures=[];const browserErrors=[];
  window.addEventListener('error',event=>browserErrors.push(String(event.error?.stack||event.message||'window error')));
  window.addEventListener('unhandledrejection',event=>browserErrors.push(String(event.reason?.stack||event.reason||'unhandled rejection')));
  const waitFor=async(predicate,timeout=15000,interval=25)=>{const start=performance.now();while(performance.now()-start<timeout){const value=predicate();if(value)return value;await sleep(interval)}return null};
  const checkedTrue=new Set(['LocalCheckBox','WhisperCheckBox','GroupCheckBox','GuildCheckBox','ShoutCheckBox','GlobalCheckBox','ObserverCheckBox','HintCheckBox','SystemCheckBox','GainsCheckBox','AlertCheckBox']);
  const checkedFalse=new Set(['TransparentCheckBox','HideTabCheckBox','ReverseListCheckBox','CleanUpCheckBox','FadeOutCheckBox']);
  function counts(){return{listItems:document.querySelectorAll('.chat-options-local-list-item').length,panels:document.querySelectorAll('.chat-options-local-panel').length,tabControls:document.querySelectorAll('.chat-options-local-tab-control').length,chatTabs:document.querySelectorAll('.chat-options-local-chat-tab').length}}
  function finish(extra={}){const report={status:failures.length||browserErrors.length?'fail':'pass',failures,browserErrors,...extra};result.textContent=JSON.stringify(report,null,2);result.dataset.status=report.status;result.hidden=false;document.documentElement.dataset.chatOptionsQa=report.status;console.info(`ORIGINS Chat Options QA ${report.status.toUpperCase()}`,report)}
  (async()=>{
    const sourceStatus=await waitFor(()=>/65 GameScene \+ 15 nested\/transient/.test(document.querySelector('#source-status')?.textContent||''));
    if(!sourceStatus)failures.push('full generated source manifest did not become active');
    const button=await waitFor(()=>document.querySelector('.catalog-item[data-window-id="chat-options"]'));
    if(!button){failures.push('chat-options catalog button missing');finish();return}
    document.querySelector('[data-close-all]')?.click();button.click();
    const root=await waitFor(()=>document.querySelector('#w-chat-options'));
    if(!root){failures.push('ChatOptions root did not open');finish();return}
    const add=await waitFor(()=>root.querySelector('[data-source-local-action="AddNewTab(null)"]'));
    if(!add){failures.push('source AddNewTab local action did not attach');finish();return}
    if(root.dataset.constructorPrecreatedLocalTabs!=='0')failures.push(`constructor local tab count is ${root.dataset.constructorPrecreatedLocalTabs}, expected 0`);
    const before=counts();if(Object.values(before).some(value=>value!==0))failures.push(`local Chat Options state existed before Add: ${JSON.stringify(before)}`);
    add.click();
    const created=await waitFor(()=>{const c=counts();return c.listItems===1&&c.panels===1&&c.tabControls===1&&c.chatTabs===1?c:null},5000);
    if(!created){failures.push(`Add did not create exactly one local source tree: ${JSON.stringify(counts())}`);finish({before,afterAdd:counts()});return}
    const listItem=document.querySelector('.chat-options-local-list-item');const panel=document.querySelector('.chat-options-local-panel');const tabControl=document.querySelector('.chat-options-local-tab-control');const chatTab=document.querySelector('.chat-options-local-chat-tab');
    if(listItem?.textContent?.trim()!=='Window 0')failures.push(`first local list item is ${JSON.stringify(listItem?.textContent?.trim())}, expected Window 0`);
    if(tabControl?.dataset.sourceType!=='DXTabControl'||tabControl?.dataset.localStateOnly!=='true')failures.push('local DXTabControl source/local markers missing');
    if(chatTab?.dataset.sourceType!=='ChatTab'||chatTab?.dataset.sourceOpacity!=='0.5'||chatTab?.dataset.allowResize!=='true')failures.push('local ChatTab source state drifted');
    const checks=[...panel.querySelectorAll('.chat-options-local-checkbox')];if(checks.length!==16)failures.push(`local ChatOptionsPanel has ${checks.length} checkboxes, expected 16`);
    const seen=new Set();for(const check of checks){const name=check.dataset.sourceCheckbox||'';seen.add(name);const actual=check.dataset.checked==='true';const expected=checkedTrue.has(name);if(!checkedTrue.has(name)&&!checkedFalse.has(name))failures.push(`unexpected checkbox ${name}`);else if(actual!==expected)failures.push(`${name} checked=${actual}, expected ${expected}`)}
    for(const name of [...checkedTrue,...checkedFalse])if(!seen.has(name))failures.push(`source checkbox missing after Add: ${name}`);
    const textPanel=chatTab?.querySelector('.chat-options-local-text-panel');const scroll=chatTab?.querySelector('.chat-options-local-scrollbar');const alert=tabControl?.querySelector('img[data-source-type="DXImageControl"][data-source-visible="false"]');
    if(!textPanel||textPanel.dataset.runtimeMessages!=='none'||textPanel.childElementCount!==0)failures.push('local ChatTab TextPanel must exist and contain zero messages');
    if(!scroll||scroll.dataset.sourceType!=='DXVScrollBar'||scroll.dataset.neutralRuntime!=='true')failures.push('local ChatTab neutral DXVScrollBar missing');
    if(!alert||getComputedStyle(alert).display!=='none'||!String(alert.getAttribute('src')||'').endsWith('/00240.png'))failures.push('local ChatTab hidden GameInter 240 AlertIcon missing');
    const nameInput=panel?.querySelector('.chat-options-local-name input');if(nameInput?.value!=='Window 0')failures.push(`local name textbox value ${JSON.stringify(nameInput?.value)}, expected Window 0`);
    const remove=panel?.querySelector('[data-source-action="RemoveButton.MouseClick"]');if(!remove)failures.push('source RemoveButton local action missing');else remove.click();
    await waitFor(()=>Object.values(counts()).every(value=>value===0),3000);
    const afterRemove=counts();if(Object.values(afterRemove).some(value=>value!==0))failures.push(`Remove did not clear local tab tree: ${JSON.stringify(afterRemove)}`);
    finish({before,afterAdd:created,checkboxes:checks.length,afterRemove,expectedCheckedTrue:[...checkedTrue].sort(),expectedCheckedFalse:[...checkedFalse].sort(),manifestControlsAdded:0,runtimePayloadsInvented:false});
  })().catch(error=>{failures.push(String(error?.stack||error));finish()});
}
