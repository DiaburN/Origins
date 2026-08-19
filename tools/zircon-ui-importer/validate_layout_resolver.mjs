#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

const [,, specPathArg, resolverPathArg] = process.argv;
if (!specPathArg || !resolverPathArg) {
  console.error('usage: validate_layout_resolver.mjs <ui-source-spec.json> <layout-resolver.js>');
  process.exit(2);
}

const specPath = path.resolve(specPathArg);
const resolverPath = path.resolve(resolverPathArg);
const spec = JSON.parse(fs.readFileSync(specPath,'utf8'));
const { buildWindowLayout, getAssetSize } = await import(pathToFileURL(resolverPath).href);

function windowByField(field) {
  const item = spec.windows.find(window => window.field === field);
  if (!item) throw new Error(`missing window: ${field}`);
  return item;
}
function nodeByName(layout,name) {
  const node = layout.nodes.find(entry => entry.name === name);
  if (!node) throw new Error(`missing layout node: ${name}`);
  return node;
}
function assertEqual(actual,expected,message) {
  if (actual !== expected) throw new Error(`${message}: expected ${expected}, got ${actual}`);
}
function assertPair(node,x,y,message) {
  assertEqual(node.x,x,`${message} x`);
  assertEqual(node.y,y,`${message} y`);
}

const main = buildWindowLayout(spec,windowByField('MainPanel'));
const characterButton = nodeByName(main,'CharacterButton');
assertPair(characterButton,650,23,'MainPanel.CharacterButton');
const mailButton = nodeByName(main,'MailButton');
assertPair(mailButton,806,23,'MainPanel.MailButton');
const newMailIcon = nodeByName(main,'NewMailIcon');
assertPair(newMailIcon,808,25,'MainPanel.NewMailIcon parent offset');
const healthBar = nodeByName(main,'HealthBar');
assertPair(healthBar,35,22,'MainPanel.HealthBar');
if (healthBar.width <= 0 || healthBar.height <= 0) throw new Error('HealthBar asset-derived size was not resolved');

const menu = buildWindowLayout(spec,windowByField('MenuBox'));
const settings = nodeByName(menu,'SettingsButton');
assertPair(settings,26,40,'Menu.SettingsButton');
assertEqual(settings.width,100,'Menu.SettingsButton width');
if (settings.height <= 0) throw new Error('Menu.SettingsButton DefaultHeight was not resolved');

const chat = buildWindowLayout(spec,windowByField('ChatTextBox'));
const chatOptions = nodeByName(chat,'OptionsButton');
assertPair(chatOptions,429,8,'ChatTextBox.OptionsButton forward reference');

const fortune = buildWindowLayout(spec,windowByField('FortuneCheckerBox'));
const searchScrollBar = nodeByName(fortune,'SearchScrollBar');
assertPair(searchScrollBar,480,68,'FortuneChecker.SearchScrollBar ClientArea.Size');

const interface16 = getAssetSize(spec,'Interface',16);
if (!interface16 || interface16[0] <= 0 || interface16[1] <= 0) throw new Error('assetSizes missing Interface 16');
const gameInter82 = getAssetSize(spec,'GameInter',82);
if (!gameInter82 || gameInter82[0] <= 0 || gameInter82[1] <= 0) throw new Error('assetSizes missing GameInter 82');

let pointExpressions = 0;
let pointTruncated = 0;
let sizeExpressions = 0;
let sizeTruncated = 0;
let explicitLocations = 0;
const suspiciousLocationFallbacks = [];

for (const window of spec.windows) {
  const layout = buildWindowLayout(spec,window);
  for (let index=0; index < (window.controls || []).length; index++) {
    const control = window.controls[index];
    const properties = control.properties || {};
    const node = layout.nodes[index];

    if ('Location' in properties) {
      explicitLocations++;
      const source = String(properties.Location).trim();
      const explicitZero = /^(Point\.Empty|new Point\(\s*0\s*,\s*0\s*\))$/.test(source);
      if (node && node.localX === 0 && node.localY === 0 && !explicitZero) {
        suspiciousLocationFallbacks.push({
          window: window.field,
          control: control.name,
          type: control.type,
          source,
        });
      }
    }

    for (const value of Object.values(properties)) {
      const text = String(value);
      if (text.includes('new Point(')) {
        pointExpressions++;
        if (!text.includes(')')) pointTruncated++;
      }
      if (text.includes('new Size(')) {
        sizeExpressions++;
        if (!text.includes(')')) sizeTruncated++;
      }
    }
  }
}

if (pointTruncated || sizeTruncated) {
  throw new Error(`truncated geometry expressions: points=${pointTruncated}, sizes=${sizeTruncated}`);
}

// Current remaining fallbacks are constructor-local variables, runtime-selected
// branches or special composite areas. Keep a small allowance so a harmless
// upstream source change does not immediately break CI, but fail on regression.
const MAX_SUSPICIOUS_LOCATION_FALLBACKS = 55;
if (suspiciousLocationFallbacks.length > MAX_SUSPICIOUS_LOCATION_FALLBACKS) {
  console.error('first suspicious fallbacks:', suspiciousLocationFallbacks.slice(0,20));
  throw new Error(`source Location fallback regression: ${suspiciousLocationFallbacks.length} > ${MAX_SUSPICIOUS_LOCATION_FALLBACKS}`);
}

console.log('layout resolver validation passed');
console.log('MainPanel root size:', main.rootSize);
console.log('CharacterButton:', characterButton.x, characterButton.y, characterButton.width, characterButton.height);
console.log('NewMailIcon:', newMailIcon.x, newMailIcon.y, newMailIcon.width, newMailIcon.height);
console.log('HealthBar:', healthBar.x, healthBar.y, healthBar.width, healthBar.height);
console.log('Menu SettingsButton:', settings.x, settings.y, settings.width, settings.height);
console.log('Chat OptionsButton:', chatOptions.x, chatOptions.y);
console.log('Fortune SearchScrollBar:', searchScrollBar.x, searchScrollBar.y);
console.log('complete Point expressions:', pointExpressions);
console.log('complete Size expressions:', sizeExpressions);
console.log('explicit source Locations:', explicitLocations);
console.log('suspicious source Location fallbacks:', suspiciousLocationFallbacks.length);
