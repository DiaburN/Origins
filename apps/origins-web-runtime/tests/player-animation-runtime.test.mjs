import test from 'node:test';
import assert from 'node:assert/strict';
import {
  DIRECT_UNMAPPED_PLAYER_ACTIONS,
  PLAYER_ANIMATION_SOURCE,
  getPlayerFrameDefinition,
  getRenderedLocalFrameIndex,
  getTimelineFrameIndex,
  resolveAssassinArmourShift,
  resolveAttackAnimation,
  resolveMagicAnimation,
  resolvePlayerAnimation,
  resolvePlayerDrawFrame,
  resolvePlayerLayerFrames,
} from '../player-animation-runtime.js';

test('all 42 pinned FrameSet.Players animations are present', () => {
  assert.equal(PLAYER_ANIMATION_SOURCE.frameCount, 42);
  for (const name of [
    'Standing', 'Walking', 'Running', 'Pushed', 'Combat1', 'Combat15',
    'Struck', 'Die', 'Dead', 'HorseStanding', 'HorseWalking', 'HorseRunning',
    'FishingCast', 'FishingWait', 'FishingReel', 'TamingCast', 'TamingWait',
    'DragonRepulseStart', 'DragonRepulseMiddle', 'DragonRepulseEnd',
    'ChannellingStart', 'ChannellingMiddle', 'ChannellingEnd',
  ]) {
    assert.ok(getPlayerFrameDefinition(name), name);
  }
});

test('pinned core player frame definitions retain exact indices and timing', () => {
  assert.deepEqual(getPlayerFrameDefinition('Standing'), {
    startIndex: 0, frameCount: 4, offset: 10,
    delaysMs: [500, 500, 500, 500], reversed: false, staticSpeed: false,
  });
  assert.deepEqual(getPlayerFrameDefinition('Walking'), {
    startIndex: 80, frameCount: 6, offset: 10,
    delaysMs: [100, 100, 100, 100, 100, 100], reversed: false, staticSpeed: false,
  });
  assert.deepEqual(getPlayerFrameDefinition('Running'), {
    startIndex: 160, frameCount: 6, offset: 10,
    delaysMs: [100, 100, 100, 100, 100, 100], reversed: false, staticSpeed: false,
  });
});

test('Combat1 and Combat2 preserve Zircon custom per-frame delays', () => {
  assert.deepEqual(getPlayerFrameDefinition('Combat1').delaysMs, [100, 200, 100, 100, 100]);
  assert.deepEqual(getPlayerFrameDefinition('Combat2').delaysMs, [100, 100, 100, 200, 100]);
  assert.equal(getTimelineFrameIndex(getPlayerFrameDefinition('Combat1'), 99), 0);
  assert.equal(getTimelineFrameIndex(getPlayerFrameDefinition('Combat1'), 100), 1);
  assert.equal(getTimelineFrameIndex(getPlayerFrameDefinition('Combat1'), 299), 1);
  assert.equal(getTimelineFrameIndex(getPlayerFrameDefinition('Combat1'), 300), 2);
});

test('DrawFrame uses StartIndex + frame + OffSet * MirDirection', () => {
  // Standing, Down(4), local frame 0 => 0 + 0 + 10*4 = 40.
  assert.equal(resolvePlayerDrawFrame('Standing', 4, 0, { action: 'Standing' }), 40);
  // Walking, Right(2), local frame 3 => 80 + 3 + 10*2 = 103.
  assert.equal(resolvePlayerDrawFrame('Walking', 2, 3, { action: 'Moving' }), 103);
});

test('reversed Pushed timing and Player frame-zero override match MapObject', () => {
  const pushed = getPlayerFrameDefinition('Pushed');
  assert.equal(pushed.reversed, true);
  assert.equal(pushed.staticSpeed, true);
  assert.equal(getRenderedLocalFrameIndex(pushed, 0, { action: 'Pushed', isPlayer: false }), 5);
  assert.equal(getRenderedLocalFrameIndex(pushed, 0, { action: 'Pushed', isPlayer: true }), 0);
  assert.equal(resolvePlayerDrawFrame('Pushed', 0, 0, { action: 'Pushed', isPlayer: true }), 240);
});

test('StaticSpeed prevents Zircon queue double-speed from changing Pushed timing', () => {
  const pushed = getPlayerFrameDefinition('Pushed');
  assert.equal(getTimelineFrameIndex(pushed, 25, false), 0);
  assert.equal(getTimelineFrameIndex(pushed, 25, true), 0);
});

test('attack animation resolver preserves class, weapon and magic rules', () => {
  assert.equal(resolveAttackAnimation({ magicType: 'Slaying' }), 'Combat3');
  assert.equal(resolveAttackAnimation({ magicType: 'HalfMoon' }), 'Combat4');
  assert.equal(resolveAttackAnimation({ magicType: 'DragonRise' }), 'Combat5');
  assert.equal(resolveAttackAnimation({ magicType: 'BladeStorm' }), 'Combat6');
  assert.equal(resolveAttackAnimation({ playerClass: 'Assassin', weaponShape: 1200 }), 'Combat11');
  assert.equal(resolveAttackAnimation({ playerClass: 'Assassin', weaponShape: 1100 }), 'Combat4');
  assert.equal(resolveAttackAnimation({ magicType: 'FullBloom', weaponShape: 1200 }), 'Combat13');
  assert.equal(resolveAttackAnimation({ magicType: 'SweetBrier', weaponShape: 1200 }), 'Combat12');
  assert.equal(resolveAttackAnimation({ magicType: 'SweetBrier', weaponShape: 1100 }), 'Combat10');
});

test('magic casting animation comes from pinned Functions.GetMagicAnimation cases', () => {
  assert.equal(resolveMagicAnimation('FireBall'), 'Combat1');
  assert.equal(resolveMagicAnimation('MagicShield'), 'Combat2');
  assert.equal(resolveMagicAnimation('ElementalHurricane'), 'ChannellingStart');
  assert.equal(resolveMagicAnimation('DragonRepulse'), 'DragonRepulseStart');
  assert.equal(resolveMagicAnimation('ThunderKick'), 'Combat7');
  assert.equal(resolveMagicAnimation('Cloak'), 'Combat9');
  assert.throws(() => resolveMagicAnimation('__not_a_zircon_magic__'), /no mapping/);
});

test('PlayerObject action mapping keeps walking, running, horse, stealth and spell overrides', () => {
  assert.equal(resolvePlayerAnimation({ action: 'Standing' }).animation, 'Standing');
  assert.equal(resolvePlayerAnimation({ action: 'Moving', moveDistance: 1 }).animation, 'Walking');
  assert.equal(resolvePlayerAnimation({ action: 'Moving', moveDistance: 2 }).animation, 'Running');
  assert.equal(resolvePlayerAnimation({ action: 'Moving', moveDistance: 2, horse: true }).animation, 'HorseRunning');
  assert.equal(resolvePlayerAnimation({ action: 'Moving', cloak: true }).animation, 'CreepWalkSlow');
  assert.equal(resolvePlayerAnimation({ action: 'Moving', cloak: true, ghostWalk: true }).animation, 'CreepWalkFast');
  assert.equal(resolvePlayerAnimation({ action: 'Moving', magicType: 'ShoulderDash' }).animation, 'Combat8');
  assert.equal(resolvePlayerAnimation({ action: 'RangeAttack' }).animation, 'Combat1');
  assert.equal(resolvePlayerAnimation({ action: 'Spell', magicType: 'FireBall' }).animation, 'Combat1');
  assert.equal(resolvePlayerAnimation({ action: 'Struck', horse: true }).animation, 'HorseStruck');
});

test('fishing and taming preserve stateful Zircon transitions', () => {
  assert.equal(resolvePlayerAnimation({ action: 'Fishing', fishingState: 'Cast' }).animation, 'FishingCast');
  assert.equal(resolvePlayerAnimation({ action: 'Fishing', fishingState: 'Cast', currentAnimation: 'FishingCast' }).animation, 'FishingWait');
  assert.equal(resolvePlayerAnimation({ action: 'Fishing', fishingState: 'Cast', currentAnimation: 'FishingWait' }).animation, 'FishingWait');
  assert.equal(resolvePlayerAnimation({ action: 'Fishing', fishingState: 'Reel', currentAnimation: 'FishingWait' }).animation, 'FishingReel');
  assert.equal(resolvePlayerAnimation({ action: 'Taming' }).animation, 'TamingCast');
  assert.equal(resolvePlayerAnimation({ action: 'Taming', currentAnimation: 'TamingCast' }).animation, 'TamingWait');
});

test('Show, Hide, Mount and Idle are not fabricated as direct PlayerObject animations', () => {
  assert.deepEqual(DIRECT_UNMAPPED_PLAYER_ACTIONS, ['Show', 'Hide', 'Mount', 'Idle']);
  for (const action of DIRECT_UNMAPPED_PLAYER_ACTIONS) {
    assert.throws(() => resolvePlayerAnimation({ action }), /no direct action mapping/);
  }
});

test('Assassin ArmourShift preserves native special layout including Combat2 carry-over', () => {
  assert.equal(resolveAssassinArmourShift('Walking'), 1600);
  assert.equal(resolveAssassinArmourShift('Combat9'), -960);
  assert.equal(resolveAssassinArmourShift('Die'), -400);
  assert.equal(resolveAssassinArmourShift('Combat2', 123), 123);
});

test('body/hair/helmet/weapon/shield/horse frame composition keeps Zircon offsets', () => {
  assert.deepEqual(resolvePlayerLayerFrames({
    drawFrame: 100,
    playerClass: 'Warrior',
    hairType: 2,
    helmetShape: 3,
    weaponShape: 4,
    shieldShape: 2,
    armourShape: 5,
    horseType: 2,
  }), {
    body: 25100,
    hair: 5100,
    helmet: 10100,
    weapon: 20100,
    shield: 10100,
    horse: 5100,
  });

  assert.equal(resolvePlayerLayerFrames({
    drawFrame: 100,
    playerClass: 'Assassin',
    armourShape: 2,
    armourShift: 1600,
  }).body, 7700);
});
