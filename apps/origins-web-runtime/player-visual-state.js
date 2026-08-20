export const PLAYER_CLASSES = Object.freeze(['Warrior', 'Wizard', 'Taoist', 'Assassin']);
export const PLAYER_GENDERS = Object.freeze(['Male', 'Female']);

const PLAYER_CLASS_SET = new Set(PLAYER_CLASSES);
const PLAYER_GENDER_SET = new Set(PLAYER_GENDERS);

export function createPlayerVisualState(initial = {}) {
  return applyPlayerVisualState({
    playerClass: 'Warrior',
    gender: 'Male',
    armourShape: 0,
    costumeShape: -1,
    hairType: 0,
    helmetShape: 0,
    libraryWeaponShape: 0,
    weaponEquipped: false,
    shieldShape: -1,
    horseShape: 0,
    horseType: 0,
    hideHead: false,
  }, initial);
}

export function applyPlayerVisualState(current, patch = {}) {
  if (!current || typeof current !== 'object') throw new TypeError('current visual state must be an object');
  if (!patch || typeof patch !== 'object') throw new TypeError('visual state patch must be an object');

  const next = { ...current };

  if (has(patch, 'playerClass')) next.playerClass = normalizePlayerClass(patch.playerClass);
  if (has(patch, 'gender')) next.gender = normalizeGender(patch.gender);
  if (has(patch, 'armourShape')) next.armourShape = integer(patch.armourShape, 0, 999999, 'armourShape');
  if (has(patch, 'costumeShape')) next.costumeShape = sentinelInteger(patch.costumeShape, -1, 999999, 'costumeShape');
  if (has(patch, 'hairType')) next.hairType = integer(patch.hairType, 0, 999999, 'hairType');
  if (has(patch, 'helmetShape')) next.helmetShape = integer(patch.helmetShape, 0, 999999, 'helmetShape');

  if (has(patch, 'weaponShape')) {
    if (isAbsent(patch.weaponShape)) {
      next.weaponEquipped = false;
    } else {
      next.libraryWeaponShape = integer(patch.weaponShape, 0, 999999, 'weaponShape');
      next.weaponEquipped = true;
    }
  }
  if (has(patch, 'libraryWeaponShape')) {
    next.libraryWeaponShape = integer(patch.libraryWeaponShape, 0, 999999, 'libraryWeaponShape');
  }
  if (has(patch, 'weaponEquipped')) next.weaponEquipped = Boolean(patch.weaponEquipped);

  if (has(patch, 'shieldShape')) {
    next.shieldShape = isAbsent(patch.shieldShape) || Number(patch.shieldShape) === -1
      ? -1
      : integer(patch.shieldShape, 0, 999999, 'shieldShape');
  }

  if (has(patch, 'horseShape')) next.horseShape = integer(patch.horseShape, 0, 7, 'horseShape');
  if (has(patch, 'horseType')) next.horseType = integer(patch.horseType, 0, 255, 'horseType');
  if (has(patch, 'hideHead')) next.hideHead = Boolean(patch.hideHead);

  return Object.freeze(next);
}

export function fromZirconObjectPlayer(info = {}) {
  if (!info || typeof info !== 'object') throw new TypeError('Zircon ObjectPlayer snapshot must be an object');

  const read = (camel, pascal, fallback) => has(info, camel) ? info[camel] : has(info, pascal) ? info[pascal] : fallback;
  const weapon = read('weapon', 'Weapon', null);

  return createPlayerVisualState({
    playerClass: read('class', 'Class', 'Warrior'),
    gender: read('gender', 'Gender', 'Male'),
    armourShape: read('armour', 'Armour', 0),
    costumeShape: read('costume', 'Costume', -1),
    hairType: read('hairType', 'HairType', 0),
    helmetShape: read('helmet', 'Helmet', 0),
    weaponShape: isAbsent(weapon) || Number(weapon) < 0 ? null : weapon,
    shieldShape: read('shield', 'Shield', -1),
    horseShape: read('horseShape', 'HorseShape', 0),
    horseType: normalizeHorseType(read('horse', 'Horse', 0)),
    hideHead: read('hideHead', 'HideHead', false),
  });
}

export function toPlayerCompositionContext(state) {
  return Object.freeze({
    playerClass: state.playerClass,
    gender: state.gender,
    armourShape: state.armourShape,
    costumeShape: state.costumeShape,
    helmetShape: state.helmetShape,
    hairType: state.hairType,
    libraryWeaponShape: state.libraryWeaponShape,
    weaponEquipped: state.weaponEquipped,
    shieldShape: state.shieldShape,
    horseShape: state.horseShape,
    horseType: state.horseType,
    hideHead: state.hideHead,
  });
}

export function isMounted(state) {
  return Number(state?.horseType) > 0;
}

export function normalizePlayerClass(value) {
  const text = String(value ?? '');
  if (!PLAYER_CLASS_SET.has(text)) throw new RangeError(`Unsupported Zircon MirClass: ${value}`);
  return text;
}

export function normalizeGender(value) {
  const text = String(value ?? '');
  if (!PLAYER_GENDER_SET.has(text)) throw new RangeError(`Unsupported Zircon MirGender: ${value}`);
  return text;
}

function normalizeHorseType(value) {
  if (typeof value === 'string' && !/^\d+$/.test(value)) return value === 'None' ? 0 : 1;
  return integer(value, 0, 255, 'horseType');
}

function has(object, key) {
  return Object.prototype.hasOwnProperty.call(object, key);
}

function isAbsent(value) {
  return value === null || value === undefined || value === '';
}

function sentinelInteger(value, sentinel, max, label) {
  if (Number(value) === sentinel) return sentinel;
  return integer(value, 0, max, label);
}

function integer(value, min, max, label) {
  const parsed = Number(value);
  if (!Number.isInteger(parsed) || parsed < min || parsed > max) {
    throw new RangeError(`${label} must be an integer ${min}..${max}: ${value}`);
  }
  return parsed;
}
