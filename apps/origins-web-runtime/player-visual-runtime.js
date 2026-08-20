import {
  resolveAssassinArmourShift,
  resolvePlayerDrawPlan,
  resolvePlayerLayerFrames,
  resolvePlayerLibrarySelection,
} from './player-animation-runtime.js';

export function resolvePlayerVisualComposition(context = {}) {
  const {
    drawFrame,
    direction,
    animation = 'Standing',
    playerClass = 'Warrior',
    gender = 'Male',
    armourShape = 0,
    costumeShape = -1,
    helmetShape = 0,
    hairType = 0,
    libraryWeaponShape = 0,
    weaponEquipped = false,
    shieldShape = -1,
    horseShape = 0,
    horseType = 0,
    drawWeapon = true,
    hideHead = false,
    previousArmourShift = 0,
  } = context;

  if (!Number.isInteger(drawFrame) || drawFrame < 0) {
    throw new RangeError(`drawFrame must be a non-negative integer: ${drawFrame}`);
  }
  if (!Number.isInteger(direction) || direction < 0 || direction > 7) {
    throw new RangeError(`MirDirection must be 0..7: ${direction}`);
  }

  const equipment = Object.freeze({
    weapon: Boolean(weaponEquipped),
    helmet: helmetShape > 0,
    shield: shieldShape >= 0,
    mounted: horseType > 0,
  });

  const libraries = resolvePlayerLibrarySelection({
    playerClass,
    gender,
    armourShape,
    costumeShape,
    helmetShape,
    libraryWeaponShape,
    shieldShape,
    horseShape,
  });

  const armourShift = playerClass === 'Assassin'
    ? resolveAssassinArmourShift(animation, previousArmourShift)
    : 0;

  const frames = resolvePlayerLayerFrames({
    drawFrame,
    playerClass,
    hairType,
    helmetShape,
    weaponShape: libraries.normalizedWeaponShape,
    shieldShape,
    armourShape: libraries.effectiveArmourShape,
    costumeShape,
    horseType,
    armourShift,
  });

  const plan = resolvePlayerDrawPlan({
    direction,
    animation,
    costumeShape,
    drawWeapon,
    hideHead,
    helmetShape,
    hairType,
    shieldShape,
    weapon1Available: equipment.weapon && Boolean(libraries.weapon1),
    weapon2Available: equipment.weapon && Boolean(libraries.weapon2),
    horseShape,
  });

  const layers = plan
    .map(step => resolveDrawStep(step, { libraries, frames, drawFrame, horseShape }))
    .filter(Boolean);

  return Object.freeze({
    playerClass,
    gender,
    direction,
    animation,
    armourShift,
    equipment,
    libraries,
    frames,
    layers: Object.freeze(layers),
  });
}

function resolveDrawStep(step, state) {
  const { libraries, frames, drawFrame, horseShape } = state;
  let libraryFile = null;
  let imageIndex = null;
  let tintRole = null;

  switch (step.layer) {
    case 'body':
      libraryFile = libraries.body;
      imageIndex = frames.body;
      tintRole = 'armour';
      break;
    case 'hair':
      libraryFile = libraries.hair;
      imageIndex = frames.hair;
      tintRole = 'hair';
      break;
    case 'helmet':
      libraryFile = libraries.helmet;
      imageIndex = frames.helmet;
      break;
    case 'weapon1':
      libraryFile = libraries.weapon1;
      imageIndex = frames.weapon;
      break;
    case 'weapon2':
      libraryFile = libraries.weapon2;
      imageIndex = frames.weapon;
      break;
    case 'shield':
      libraryFile = libraries.shield;
      imageIndex = frames.shield;
      break;
    case 'horse':
      if (horseShape === 0) libraryFile = libraries.horseBase;
      else libraryFile = libraries.horseShape;
      imageIndex = step.frameMode === 'drawFrame' ? drawFrame : frames.horse;
      break;
    case 'horseShapeEffect':
      libraryFile = libraries.horseShapeEffect;
      imageIndex = drawFrame;
      break;
    default:
      throw new RangeError(`Unsupported Zircon player draw layer: ${step.layer}`);
  }

  if (!libraryFile || imageIndex === null || imageIndex === undefined) return null;
  return Object.freeze({
    layer: step.layer,
    phase: step.phase,
    libraryFile,
    imageIndex,
    tintRole,
  });
}

export function collectPlayerVisualLibraryFiles(composition) {
  if (!composition?.layers) return Object.freeze([]);
  return Object.freeze([...new Set(composition.layers.map(layer => layer.libraryFile))]);
}

export function collectPlayerVisualFrameRequests(composition) {
  if (!composition?.layers) return Object.freeze([]);
  return Object.freeze(composition.layers.map(layer => Object.freeze({
    libraryFile: layer.libraryFile,
    imageIndex: layer.imageIndex,
  })));
}
