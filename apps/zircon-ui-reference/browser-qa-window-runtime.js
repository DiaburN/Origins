// Screenshot helper used only by the GitHub browser-QA artifact copy.
// `?qaWindow=<id>` opens exactly one reconstructed source window after the
// generated 65+15 manifest/catalog becomes available.
const params=new URLSearchParams(window.location.search);
const qaWindow=params.get('qaWindow');
if(qaWindow){
  const sleep=ms=>new Promise(resolve=>setTimeout(resolve,ms));
  (async()=>{
    for(let i=0;i<400;i++){
      const status=document.querySelector('#source-status')?.textContent||'';
      const button=document.querySelector(`.catalog-item[data-window-id="${CSS.escape(qaWindow)}"]`);
      if(/65 GameScene \+ 15 nested\/transient/.test(status)&&button){
        document.querySelector('[data-close-all]')?.click();
        button.click();
        document.documentElement.dataset.qaWindowReady=qaWindow;
        document.body.classList.add('qa-window-screenshot');
        return;
      }
      await sleep(25);
    }
    document.documentElement.dataset.qaWindowReady='missing';
  })();
}
