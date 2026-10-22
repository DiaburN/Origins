window.G = window.G || {};

G.Session = (() => {
  const STORAGE_KEY = 'origins-x:profile:v1';
  const state = load();

  function emptyState() {
    return { account: null, characters: [], selectedCharacterId: null };
  }

  function load() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) return emptyState();
      const parsed = JSON.parse(raw);
      return {
        account: parsed.account || null,
        characters: Array.isArray(parsed.characters) ? parsed.characters : [],
        selectedCharacterId: parsed.selectedCharacterId || null
      };
    } catch (error) {
      console.warn('Unable to load local ORIGINS profile', error);
      return emptyState();
    }
  }

  function save() {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  }

  function login(username, password) {
    const clean = String(username || '').trim();
    if (clean.length < 2) throw new Error('Escribe un usuario.');
    if (!String(password || '').trim()) throw new Error('Escribe una contraseña.');
    state.account = { username: clean };
    save();
    return state.account;
  }

  function logout() {
    state.account = null;
    state.selectedCharacterId = null;
    save();
  }

  function createCharacter({ name, className, gender }) {
    const cleanName = String(name || '').trim();
    const allowedClasses = ['Warrior', 'Wizard', 'Taoist', 'Assassin'];
    const allowedGenders = ['male', 'female'];

    if (cleanName.length < 3 || cleanName.length > 16) {
      throw new Error('El nombre debe tener entre 3 y 16 caracteres.');
    }
    if (!/^[A-Za-z0-9_]+$/.test(cleanName)) {
      throw new Error('Usa letras, números o _.');
    }
    if (state.characters.some(character => character.name.toLowerCase() === cleanName.toLowerCase())) {
      throw new Error('Ya tienes un personaje con ese nombre.');
    }
    if (!allowedClasses.includes(className)) throw new Error('Clase no válida.');
    if (!allowedGenders.includes(gender)) throw new Error('Sexo no válido.');

    const character = {
      id: `${Date.now()}-${Math.random().toString(16).slice(2)}`,
      name: cleanName,
      className,
      gender,
      level: 1,
      createdAt: new Date().toISOString()
    };

    state.characters.push(character);
    state.selectedCharacterId = character.id;
    save();
    return character;
  }

  function deleteCharacter(id) {
    const index = state.characters.findIndex(character => character.id === id);
    if (index < 0) return false;
    state.characters.splice(index, 1);
    if (state.selectedCharacterId === id) {
      state.selectedCharacterId = state.characters[0]?.id || null;
    }
    save();
    return true;
  }

  function selectCharacter(id) {
    if (!state.characters.some(character => character.id === id)) return null;
    state.selectedCharacterId = id;
    save();
    return currentCharacter();
  }

  function currentCharacter() {
    return state.characters.find(character => character.id === state.selectedCharacterId) || null;
  }

  return Object.freeze({
    login,
    logout,
    createCharacter,
    deleteCharacter,
    selectCharacter,
    currentCharacter,
    get account() { return state.account; },
    get characters() { return [...state.characters]; }
  });
})();
