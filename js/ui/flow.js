window.G = window.G || {};

G.Flow = (() => {
  const CLASS_IMAGES = {
    Warrior: { male: 'assets/ui/characters/warrior-male.webp', female: 'assets/ui/characters/warrior-female.webp' },
    Wizard: { male: 'assets/ui/characters/wizard-male.webp', female: 'assets/ui/characters/wizard-female.webp' },
    Taoist: { male: 'assets/ui/characters/taoist-male.webp', female: 'assets/ui/characters/taoist-female.webp' },
    Assassin: { male: 'assets/ui/characters/assassin-male.webp', female: 'assets/ui/characters/assassin-female.webp' }
  };

  let selectedClass = 'Warrior';
  let selectedGender = 'male';
  let selectedId = null;

  const el = id => document.getElementById(id);

  function init() {
    bindLogin();
    bindSelection();
    bindCreator();
    showScreen('login-screen');
    const remembered = G.Session.account?.username;
    if (remembered) el('login-user').value = remembered;
  }

  function showScreen(id) {
    for (const screen of document.querySelectorAll('.origin-screen')) {
      screen.classList.toggle('is-active', screen.id === id);
    }
  }

  function setMessage(id, message = '', error = false) {
    const node = el(id);
    node.textContent = message;
    node.classList.toggle('is-error', error);
  }

  function bindLogin() {
    el('login-form').addEventListener('submit', event => {
      event.preventDefault();
      try {
        G.Session.login(el('login-user').value, el('login-password').value);
        setMessage('login-message');
        renderCharacters();
        showScreen('select-screen');
      } catch (error) {
        setMessage('login-message', error.message, true);
      }
    });
  }

  function bindSelection() {
    el('create-open').addEventListener('click', () => {
      resetCreator();
      showScreen('create-screen');
    });

    el('select-logout').addEventListener('click', () => {
      G.Session.logout();
      selectedId = null;
      showScreen('login-screen');
    });

    el('play-character').addEventListener('click', enterGame);

    el('delete-character').addEventListener('click', () => {
      if (!selectedId) return;
      const character = G.Session.characters.find(item => item.id === selectedId);
      if (!character || !confirm(`¿Eliminar a ${character.name}?`)) return;
      G.Session.deleteCharacter(selectedId);
      selectedId = G.Session.currentCharacter()?.id || null;
      renderCharacters();
    });
  }

  function bindCreator() {
    el('create-back').addEventListener('click', () => {
      renderCharacters();
      showScreen('select-screen');
    });

    for (const button of document.querySelectorAll('[data-class]')) {
      button.addEventListener('click', () => {
        selectedClass = button.dataset.class;
        updateCreator();
      });
    }

    for (const button of document.querySelectorAll('[data-gender]')) {
      button.addEventListener('click', () => {
        selectedGender = button.dataset.gender;
        updateCreator();
      });
    }

    el('create-form').addEventListener('submit', event => {
      event.preventDefault();
      try {
        const character = G.Session.createCharacter({
          name: el('character-name').value,
          className: selectedClass,
          gender: selectedGender
        });
        selectedId = character.id;
        setMessage('create-message');
        renderCharacters();
        showScreen('select-screen');
      } catch (error) {
        setMessage('create-message', error.message, true);
      }
    });
  }

  function resetCreator() {
    selectedClass = 'Warrior';
    selectedGender = 'male';
    el('character-name').value = '';
    setMessage('create-message');
    updateCreator();
  }

  function updateCreator() {
    el('creator-preview').src = CLASS_IMAGES[selectedClass][selectedGender];
    el('creator-class-name').textContent = selectedClass;
    for (const button of document.querySelectorAll('[data-class]')) {
      button.classList.toggle('is-selected', button.dataset.class === selectedClass);
    }
    for (const button of document.querySelectorAll('[data-gender]')) {
      button.classList.toggle('is-selected', button.dataset.gender === selectedGender);
    }
  }

  function renderCharacters() {
    const list = el('character-list');
    const characters = G.Session.characters;
    list.innerHTML = '';

    if (!characters.length) {
      selectedId = null;
      list.innerHTML = '<div class="empty-slot">No tienes personajes todavía.</div>';
      updateSelectedCharacter();
      return;
    }

    if (!selectedId || !characters.some(character => character.id === selectedId)) {
      selectedId = G.Session.currentCharacter()?.id || characters[0].id;
    }

    for (const character of characters) {
      const button = document.createElement('button');
      button.type = 'button';
      button.className = 'character-card';
      button.classList.toggle('is-selected', character.id === selectedId);
      button.innerHTML = `
        <img src="${CLASS_IMAGES[character.className][character.gender]}" alt="">
        <span class="character-card-copy">
          <strong>${escapeHtml(character.name)}</strong>
          <small>${character.className} · Nivel ${character.level}</small>
        </span>`;
      button.addEventListener('click', () => {
        selectedId = character.id;
        G.Session.selectCharacter(character.id);
        renderCharacters();
      });
      list.appendChild(button);
    }

    G.Session.selectCharacter(selectedId);
    updateSelectedCharacter();
  }

  function updateSelectedCharacter() {
    const character = G.Session.characters.find(item => item.id === selectedId) || null;
    el('play-character').disabled = !character;
    el('delete-character').disabled = !character;
    el('selected-preview').src = character ? CLASS_IMAGES[character.className][character.gender] : '';
    el('selected-preview').classList.toggle('is-hidden', !character);
    el('selected-name').textContent = character?.name || 'Selecciona un personaje';
    el('selected-meta').textContent = character ? `${character.className} · Nivel ${character.level}` : '';
  }

  function enterGame() {
    const character = G.Session.selectCharacter(selectedId);
    if (!character) return;

    el('flow-shell').hidden = true;
    const canvas = el('game');
    canvas.hidden = false;
    el('game-character-name').textContent = character.name;
    el('game-character-class').textContent = `${character.className} · Nv. ${character.level}`;
    el('game-hud').hidden = false;
    G.Game.init();
  }

  function escapeHtml(value) {
    return String(value).replace(/[&<>'"]/g, char => ({
      '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;'
    })[char]);
  }

  return Object.freeze({ init });
})();

addEventListener('DOMContentLoaded', () => G.Flow.init(), { once: true });
