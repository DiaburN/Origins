import * as base from './layout-resolver-base.js';

export const getAssetSize = base.getAssetSize;

function meta(spec, library, index) {
  return spec?.assetMeta?.[library]?.[String(index)] ?? null;
}
function libraryFrom(raw) {
  return String(raw ?? '').match(/LibraryFile\.([A-Za-z0-9_]+)/)?.[1] ?? null;
}
function literalIndex(raw) {
  const value=String(raw ?? '').trim();
  return /^-?\d+$/.test(value) ? Number(value) : null;
}
function boolFrom(raw,fallback=false) {
  const value=String(raw ?? '').trim().toLowerCase();
  if(value==='true')return true;
  if(value==='false')return false;
  return fallback;
}

function computeHorseGeometry(spec, item) {
  const recipe = item?.derivedGeometry;
  if (!recipe || recipe.type !== 'HorseTameDialog') return null;
  let left = Infinity, top = Infinity, right = -Infinity, bottom = -Infinity;
  for (let index = recipe.animationStart; index <= recipe.animationEnd; index++) {
    const image = meta(spec, recipe.animationLibrary, index);
    if (!image) continue;
    left = Math.min(left, image.offsetX);
    top = Math.min(top, image.offsetY);
    right = Math.max(right, image.offsetX + image.width);
    bottom = Math.max(bottom, image.offsetY + image.height);
  }
  if (!Number.isFinite(left) || !Number.isFinite(top)) return null;
  const animationWidth = Math.max(0, right - left);
  const animationHeight = Math.max(0, bottom - top);
  const progress = meta(spec, recipe.progressLibrary, recipe.progressOutlineIndex);
  if (!progress) return null;
  const rootWidth = Math.max(animationWidth, progress.width);
  const rootHeight = animationHeight + 2 + progress.height;
  return {
    rootSize:[rootWidth,rootHeight],
    animationAnchor:[-left,-top],
    progressLocation:[Math.floor((rootWidth-progress.width)/2),rootHeight-progress.height],
  };
}

function assetTokenValue(spec, token) {
  const match = token.match(/^AssetSize\.([A-Za-z0-9_]+)\.(\d+)\.(Width|Height)$/);
  if (!match) return null;
  const size = base.getAssetSize(spec, match[1], Number(match[2]));
  if (!size) return null;
  return match[3] === 'Width' ? size[0] : size[1];
}
function safeNumber(expression) {
  const value = String(expression).trim();
  if (!/^[0-9+\-*/().\s]+$/.test(value)) return null;
  try {
    const result = Function(`"use strict";return (${value})`)();
    return Number.isFinite(result) ? result : null;
  } catch { return null; }
}
function resolveDerivedPoint(spec, layout, node) {
  const source = String(node?.control?.properties?.Location ?? '').trim();
  const match = source.match(/^new\s+Point\s*\((.*),(.*)\)$/);
  if (!match) return null;
  const evaluate = raw => {
    let expression = raw;
    expression = expression.replace(/AssetSize\.[A-Za-z0-9_]+\.\d+\.(?:Width|Height)/g, token => {
      const value = assetTokenValue(spec, token);
      return value === null ? token : String(value);
    });
    expression = expression
      .replace(/(?<!\.)\bSize\.Width\b/g, String(layout.rootSize[0]))
      .replace(/(?<!\.)\bSize\.Height\b/g, String(layout.rootSize[1]));
    return safeNumber(expression);
  };
  const x = evaluate(match[1]), y = evaluate(match[2]);
  return x === null || y === null ? null : [Math.round(x),Math.round(y)];
}

function sourceImageOffset(spec,node) {
  const properties=node?.control?.properties ?? {};
  if(!boolFrom(properties.UseOffSet,false)) return [0,0];
  const library=libraryFrom(properties.LibraryFile),index=literalIndex(properties.Index);
  if(!library || index===null || index<0) return [0,0];
  const image=meta(spec,library,index);
  if(!image) return [0,0];
  return [Number(image.offsetX||0),Number(image.offsetY||0)];
}
function applyUseOffSetDisplayAreas(spec,layout) {
  const root=layout.root ?? {x:0,y:0};
  const visiting=new Set(),done=new Set();
  let applied=0;
  const place=node=>{
    if(!node || node===root || done.has(node)) return;
    if(visiting.has(node)) return;
    visiting.add(node);
    const parent=node.parent ?? root;
    if(parent!==root) place(parent);
    const [offsetX,offsetY]=sourceImageOffset(spec,node);
    const oldX=node.x,oldY=node.y;
    node.sourceImageOffsetX=offsetX;node.sourceImageOffsetY=offsetY;
    node.sourceUseOffSet=offsetX!==0 || offsetY!==0 || boolFrom(node.control?.properties?.UseOffSet,false);
    node.x=(parent.x ?? 0)+(node.localX ?? 0)+offsetX;
    node.y=(parent.y ?? 0)+(node.localY ?? 0)+offsetY;
    if(node.sourceUseOffSet) applied++;
    if(node.tabButton && (oldX!==node.x || oldY!==node.y)) {
      node.tabButton.x += (node.x-oldX-offsetX);
      node.tabButton.y += (node.y-oldY-offsetY);
    }
    visiting.delete(node);done.add(node);
  };
  for(const node of layout.nodes) place(node);
  layout.sourceUseOffSetNodes=applied;
  layout.sourceUseOffSetPolicy='DXImageControl.UpdateDisplayArea: Location + Library.GetOffSet(Index) + Parent.DisplayArea.Location';
}

export function buildWindowLayout(spec, item) {
  const layout = base.buildWindowLayout(spec, item);

  for (const node of layout.nodes) {
    const source = String(node?.control?.properties?.Location ?? '');
    if (!source.includes('AssetSize.')) continue;
    const point = resolveDerivedPoint(spec, layout, node);
    if (!point) continue;
    node.localX = point[0];node.localY = point[1];
    const parent = node.parent ?? layout.root ?? {x:0,y:0};
    node.x = (parent.x ?? 0)+point[0];node.y = (parent.y ?? 0)+point[1];
  }

  const horse = computeHorseGeometry(spec, item);
  if (horse) {
    layout.rootSize = horse.rootSize;
    if (layout.root) {layout.root.width=horse.rootSize[0];layout.root.height=horse.rootSize[1]}
    for (const node of layout.nodes) {
      const source = String(node?.control?.properties?.Location ?? '').trim();
      let point = null;
      if (source === '_animationAnchor') point = horse.animationAnchor;
      if (source === 'progressLocation') point = horse.progressLocation;
      if (!point) continue;
      node.localX=point[0];node.localY=point[1];
      const parent=node.parent ?? {x:0,y:0};
      node.x=(parent.x ?? 0)+point[0];node.y=(parent.y ?? 0)+point[1];
    }
  }

  // DXImageControl.UseOffSet changes DisplayArea, not Location. Apply after all
  // derived local geometry so descendants inherit the shifted parent DisplayArea.
  applyUseOffSetDisplayAreas(spec,layout);
  return layout;
}
