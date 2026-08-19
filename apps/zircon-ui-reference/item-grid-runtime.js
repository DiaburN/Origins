import { buildWindowLayout } from './layout-resolver-derived.js';

const stage=document.querySelector('#stage');
let sourceSpec=null;

function sourceInt(raw,fallback=null){
  const value=String(raw??'').trim();
  return /^-?\d+$/.test(value)?Number(value):fallback;
}
function sourceFloat(raw,fallback=null){
  const value=String(raw??'').trim().replace(/[fFdDmM]$/,'');
  return /^-?(?:\d+(?:\.\d*)?|\.\d+)$/.test(value)?Number(value):fallback;
}
function literalSize(raw){
  const match=String(raw??'').match(/new\s+Size\s*\(\s*(-?\d+)\s*,\s*(-?\d+)\s*\)/);
  return match?[Number(match[1]),Number(match[2])]:null;
}
function sourceItemForRoot(root){
  if(!sourceSpec||!root?.id?.startsWith('w-'))return null;
  const id=root.id.slice(2);
  return [...(sourceSpec.windows||[]),...(sourceSpec.nestedWindows||[])].find(item=>item.id===id)||null;
}

function drawGrid(root,node,element){
  const p=node.control?.properties||{};
  const grid=literalSize(p.GridSize);
  if(!grid||grid[0]<=0||grid[1]<=0){
    element.dataset.sourceGridRuntime='GridSize unresolved';
    return;
  }

  const padding=Math.max(0,sourceFloat(p.GridPadding,0)??0);
  const visibleHeight=Math.max(1,sourceInt(p.VisibleHeight,1000)??1000);
  const scrollValue=Math.max(0,sourceInt(p.ScrollValue,0)??0);
  const columns=grid[0],rows=grid[1],visibleRows=Math.min(rows,visibleHeight);
  const stepX=35+(padding*2),stepY=35+(padding*2);
  const expectedWidth=Math.trunc(columns*stepX+1);
  const expectedHeight=Math.trunc(visibleRows*stepY+1);

  element.replaceChildren();
  element.classList.add('dx-item-grid-source');
  element.classList.remove('generic-grid');
  element.style.display='block';
  element.style.padding='0';
  element.style.background='rgb(24,12,12)';
  element.style.border='1px solid #49391f';
  element.style.overflow='hidden';
  element.style.width=`${expectedWidth}px`;
  element.style.height=`${expectedHeight}px`;
  element.dataset.sourceGridSize=`${columns}x${rows}`;
  element.dataset.sourceGridPadding=String(padding);
  element.dataset.sourceVisibleHeight=String(visibleHeight);
  element.dataset.sourceScrollValue=String(scrollValue);
  element.dataset.sourceCellSize='36x36';
  element.dataset.sourceCellStep=`${stepX}x${stepY}`;
  element.dataset.sourceGridFormula='GridSize * (CellSize-1 + GridPadding*2) + 1';
  element.dataset.runtimeItems='ClientUserItem[]';

  for(let y=0;y<rows;y++){
    if(y<scrollValue||y>=scrollValue+visibleHeight)continue;
    for(let x=0;x<columns;x++){
      const cell=document.createElement('div');
      cell.className='dx-item-grid-cell-source';
      cell.style.position='absolute';
      cell.style.left=`${Math.trunc(x*stepX+padding)}px`;
      cell.style.top=`${Math.trunc((y-scrollValue)*stepY+padding)}px`;
      cell.style.width='36px';
      cell.style.height='36px';
      cell.style.background='transparent';
      cell.style.border='0';
      cell.style.pointerEvents='none';
      cell.dataset.slot=String(y*columns+x);
      element.append(cell);
    }
  }

  // DXItemGrid draws the shared grid lines itself. Cells do not each own a
  // permanent border, which is why adjacent slots overlap by one pixel.
  const lineColour='#49391f';
  for(let x=0;x<=columns;x++){
    const line=document.createElement('i');
    line.className='dx-item-grid-line';line.style.position='absolute';
    line.style.left=`${Math.trunc(stepX*x)}px`;line.style.top='0';line.style.width='1px';line.style.height='100%';line.style.background=lineColour;line.style.pointerEvents='none';
    element.append(line);
  }
  for(let y=0;y<=visibleRows;y++){
    const line=document.createElement('i');
    line.className='dx-item-grid-line';line.style.position='absolute';
    line.style.left='0';line.style.top=`${Math.trunc(stepY*y)}px`;line.style.width='100%';line.style.height='1px';line.style.background=lineColour;line.style.pointerEvents='none';
    element.append(line);
  }
}

function apply(root){
  const item=sourceItemForRoot(root);if(!item||!sourceSpec)return;
  const layout=buildWindowLayout(sourceSpec,item);
  for(let i=0;i<layout.nodes.length;i++){
    const node=layout.nodes[i];
    if(node.control?.type!=='DXItemGrid')continue;
    const element=root.querySelector(`[data-control-index="${i}"]`);
    if(element)drawGrid(root,node,element);
  }
}
function scan(node){
  if(!(node instanceof Element))return;
  if(node.matches?.('.window,.generic-window'))queueMicrotask(()=>apply(node));
  node.querySelectorAll?.('.window,.generic-window').forEach(root=>queueMicrotask(()=>apply(root)));
}
new MutationObserver(records=>records.forEach(record=>record.addedNodes.forEach(scan))).observe(stage,{childList:true,subtree:true});

fetch('ui-source-spec.json',{cache:'no-store'})
  .then(response=>{if(!response.ok)throw new Error(`ui-source-spec.json ${response.status}`);return response.json()})
  .then(spec=>{
    sourceSpec=spec;
    stage.querySelectorAll('.window,.generic-window').forEach(apply);
    console.info('ORIGINS source DXItemGrid 35px shared-line geometry runtime active');
  })
  .catch(error=>console.error('Unable to load Zircon item-grid source manifest',error));
