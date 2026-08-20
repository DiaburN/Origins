import {
  ZIRCON_MAGIC_ANIMATION_MAP,
  ZIRCON_PLAYER_ASSET_CONTRACT,
  ZIRCON_PLAYER_FRAMESET,
} from './generated/zircon-player-asset-contract.generated.js';

export const DIRECT_UNMAPPED_PLAYER_ACTIONS = Object.freeze(['Show', 'Hide', 'Mount', 'Idle']);

const ATTACK_COMBAT3 = new Set(['Slaying', 'Thrusting', 'FlamingSword', 'DefensiveBlow']);
const ATTACK_COMBAT4 = new Set(['HalfMoon', 'DestructiveSurge', 'OffensiveBlow']);
const LOTUS_ATTACKS = new Set(['FullBloom', 'WhiteLotus', 'RedLotus', 'DanceOfSwallow']);
const BRIER_ATTACKS = new Set(['SweetBrier', 'Karma']);

const ASSASSIN_ARMOUR_SHIFT = Object.freeze({
  Standing: 0,
  Walking: 1600,
  Running: 1600,
  CreepStanding: 240,
  CreepWalkSlow: 240,
  CreepWalkFast: 240,
  Pushed: 160,
  Combat1: -400,
  Combat3: 0,
  Combat4: 80,
  Combat5: 400,
  Combat6: 400,
  Combat7: 400,
  Combat8: 720,
  Combat9: -960,
  Combat10: -480,
  Combat11: -400,
  Combat12: -400,
  Combat13: -400,
  Combat14: 0,
  Harvest: 160,
  Stance: 160,
  Struck: -640,
  Die: -400,
  Dead: -400,
  HorseStanding: 80,
  HorseWalking: 80,
  HorseRunning: 80,
  HorseStruck: 80,
  DragonRepulseStart: 0,
  DragonRepulseMiddle: 0,
  DragonRepulseEnd: 0,
  FishingCast: 80,
  FishingWait: 80,
  FishingReel: 80,
  TamingCast: 0,
  TamingWait: 0,
});

export function getPlayerFrameDefinition(animation) {
  const frame = ZIRCON_PLAYER_FRAMESET[animation];
  if (!frame) throw new RangeError(`Zircon FrameSet.Players has no animation: ${animation}`);
  return frame;
}

export function getTimelineFrameIndex(frame, elapsedMs, doubleSpeed = false) {
  if (!frame || !Array.isArray(frame.delaysMs)) throw new TypeError('Invalid Zircon frame definition.');
  let remaining = Math.max(0, Number(elapsedMs) || 0);
  if (doubleSpeed && !frame.staticSpeed) remaining += remaining;

  for (let i = 0; i < frame.delaysMs.length; i += 1) {
    const delayIndex = frame.reversed ? frame.delaysMs.length - 1 - i : i;
    remaining -= frame.delaysMs[delayIndex];
    if (remaining >= 0) continue;
    return i;
  }
  return frame.frameCount;
}

export function getRenderedLocalFrameIndex(frame, timelineFrameIndex, { action = null, isPlayer = true } = {}) {
  if (!Number.isInteger(timelineFrameIndex)) throw new TypeError('timelineFrameIndex must be an integer.');
  if (timelineFrameIndex < 0 || timelineFrameIndex >= frame.frameCount) return null;

  let rendered = timelineFrameIndex;
  if (frame.reversed) rendered = frame.frameCount - rendered - 1;

  // Exact MapObject.UpdateFrame special case for Player + MirAction.Pushed.
  if (isPlayer && action === 'Pushed') rendered = ZIRCON_PLAYER_ASSET_CONTRACT.pushedPlayerFrameOverride;
  return rendered;
}

export function resolvePlayerDrawFrame(animation, direction, timelineFrameIndex, options = {}) {
  const frame = getPlayerFrameDefinition(animation);
  if (!Number.isInteger(direction) || direction < 0 || direction > 7) {
    throw new RangeError(`Invalid Zircon MirDirection: ${direction}`);
  }
  const localFrame = getRenderedLocalFrameIndex(frame, timelineFrameIndex, options);
  if (localFrame === null) return null;
  return localFrame + frame.startIndex + frame.offset * direction;
}

export function resolvePlayerFrameAtElapsed(animation, direction, elapsedMs, options = {}) {
  const frame = getPlayerFrameDefinition(animation);
  const timelineFrameIndex = getTimelineFrameIndex(frame, elapsedMs, Boolean(options.doubleSpeed));
  if (timelineFrameIndex >= frame.frameCount) {
    return { complete: true, timelineFrameIndex, localFrameIndex: null, drawFrame: null };
  }
  const localFrameIndex = getRenderedLocalFrameIndex(frame, timelineFrameIndex, options);
  return {
    complete: false,
    timelineFrameIndex,
    localFrameIndex,
    drawFrame: localFrameIndex + frame.startIndex + frame.offset * direction,
  };
}

export function resolveAttackAnimation({ playerClass = 'Warrior', weaponShape = 0, magicType = 'None' } = {}) {
  if (ATTACK_COMBAT3.has(magicType)) return 'Combat3';
  if (ATTACK_COMBAT4.has(magicType)) return 'Combat4';
  if (magicType === 'DragonRise') return 'Combat5';
  if (magicType === 'BladeStorm') return 'Combat6';

  if (LOTUS_ATTACKS.has(magicType)) {
    if (weaponShape >= 1200) return 'Combat13';
    if (weaponShape >= 1100) return 'Combat5';
    return 'Combat3';
  }

  if (BRIER_ATTACKS.has(magicType)) {
    if (weaponShape >= 1200) return 'Combat12';
    if (weaponShape >= 1100) return 'Combat10';
    return 'Combat3';
  }

  if (playerClass === 'Assassin') {
    if (weaponShape >= 1200) return 'Combat11';
    if (weaponShape >= 1100) return 'Combat4';
  }
  return 'Combat3';
}

export function resolveMagicAnimation(magicType) {
  const animation = ZIRCON_MAGIC_ANIMATION_MAP[magicType];
  if (!animation) throw new RangeError(`Pinned Zircon GetMagicAnimation has no mapping for ${magicType}`);
  return animation;
}

export function resolveAssassinArmourShift(animation, previousShift = 0) {
  // Combat2 in pinned PlayerObject intentionally contains no assignment; preserve prior value.
  if (animation === 'Combat2') return previousShift;
  if (!(animation in ASSASSIN_ARMOUR_SHIFT)) {
    throw new RangeError(`Pinned Assassin ArmourShift has no direct mapping for ${animation}`);
  }
  return ASSASSIN_ARMOUR_SHIFT[animation];
}

export function resolvePlayerAnimation(context) {
  const {
    action,
    playerClass = 'Warrior',
    weaponShape = 0,
    magicType = 'None',
    moveDistance = 1,
    horse = false,
    stanceActive = false,
    cloak = false,
    ghostWalk = false,
    dragonRepulse = false,
    elementalHurricane = false,
    currentAnimation = null,
    fishingState = null,
  } = context ?? {};

  let animation;
  let drawWeapon = true;

  switch (action) {
    case 'Standing':
      animation = 'Standing';
      if (stanceActive) animation = 'Stance';
      if (cloak) animation = 'CreepStanding';
      if (horse) animation = 'HorseStanding';
      if (dragonRepulse) animation = 'DragonRepulseMiddle';
      else if (currentAnimation === 'DragonRepulseMiddle') animation = 'DragonRepulseEnd';
      if (elementalHurricane) animation = 'ChannellingMiddle';
      break;

    case 'Moving':
      animation = horse ? 'HorseWalking' : 'Walking';
      if (magicType === 'ShoulderDash' || magicType === 'Assault') {
        animation = 'Combat8';
      } else if (cloak) {
        animation = ghostWalk ? 'CreepWalkFast' : 'CreepWalkSlow';
      } else if (moveDistance >= 2) {
        animation = horse ? 'HorseRunning' : 'Running';
      }
      break;

    case 'Pushed':
      animation = 'Pushed';
      break;

    case 'Attack':
      animation = resolveAttackAnimation({ playerClass, weaponShape, magicType });
      break;

    case 'Mining':
      animation = resolveAttackAnimation({ playerClass, weaponShape, magicType: 'None' });
      break;

    case 'Fishing':
      if (fishingState === 'Cast') {
        animation = currentAnimation === 'FishingWait' || currentAnimation === 'FishingCast'
          ? 'FishingWait'
          : 'FishingCast';
      } else {
        animation = currentAnimation === 'FishingWait' ? 'FishingReel' : 'Standing';
      }
      break;

    case 'Taming':
      animation = currentAnimation === 'TamingCast' || currentAnimation === 'TamingWait'
        ? 'TamingWait'
        : 'TamingCast';
      break;

    case 'RangeAttack':
      animation = 'Combat1';
      break;

    case 'Spell':
      animation = resolveMagicAnimation(magicType);
      if (magicType === 'PoisonousCloud') drawWeapon = false;
      if (elementalHurricane) animation = 'ChannellingEnd';
      break;

    case 'Struck':
      animation = horse ? 'HorseStruck' : 'Struck';
      break;

    case 'Die':
      animation = 'Die';
      break;

    case 'Dead':
      animation = 'Dead';
      break;

    case 'Harvest':
      animation = 'Harvest';
      break;

    default:
      throw new RangeError(`Pinned PlayerObject.SetAnimation has no direct action mapping for ${action}`);
  }

  return Object.freeze({ animation, drawWeapon });
}

export function resolvePlayerLayerFrames({
  drawFrame,
  playerClass = 'Warrior',
  hairType = 0,
  helmetShape = 0,
  weaponShape = 0,
  shieldShape = -1,
  armourShape = 0,
  costumeShape = -1,
  horseType = 0,
  armourShift = 0,
} = {}) {
  const assassin = playerClass === 'Assassin';
  const armourShapeOffset = assassin ? 3000 : 5000;
  const weaponShapeOffset = 5000;
  const hairTypeOffset = 5000;

  return Object.freeze({
    body: drawFrame + (costumeShape >= 0 ? costumeShape % 10 : armourShape % 11) * armourShapeOffset + armourShift,
    hair: hairType > 0 ? drawFrame + (hairType - 1) * hairTypeOffset : null,
    helmet: helmetShape > 0 ? drawFrame + ((helmetShape - 1) % 10) * armourShapeOffset + armourShift : null,
    weapon: weaponShape >= 0 ? drawFrame + (weaponShape % 10) * weaponShapeOffset : null,
    shield: shieldShape >= 0 ? drawFrame + (shieldShape % 10) * armourShapeOffset + armourShift : null,
    horse: horseType > 0 ? drawFrame + (horseType - 1) * 5000 : null,
  });
}

export const PLAYER_ANIMATION_SOURCE = Object.freeze({
  commit: ZIRCON_PLAYER_ASSET_CONTRACT.zirconCommit,
  frameCount: Object.keys(ZIRCON_PLAYER_FRAMESET).length,
  libraryCount: ZIRCON_PLAYER_ASSET_CONTRACT.playerLibraries.length,
});
