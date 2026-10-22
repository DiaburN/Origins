window.G = window.G || {};

G.Flow = (() => {
  const CLASS_ASSETS = Object.freeze({
    Warrior: { male: 'assets/ui/zircon/characters/warrior-male.webp', female: 'assets/ui/zircon/characters/warrior-female.webp' },
    Wizard: { male: 'assets/ui/zircon/characters/wizard-male.webp', female: 'assets/ui/zircon/characters/wizard-female.webp' },
    Taoist: { male: 'assets/ui/zircon/characters/taoist-male.webp', female: 'assets/ui/zircon/characters/taoist-female.webp' },
    Assassin: { male: 'assets/ui/zircon/characters/assassin-male.webp', female: 'assets/ui/zircon/characters/assassin-female.webp' }
  });
  const classImage = (className, gender) => CLASS_ASSETS[className][gender];

  let selectedClass = 'Warrior';
  let selectedGender = 'male';
  let selectedId = null;
  let toastTimer = 0;
  const el = id => document.getElementById(id);

  function init() {
    bindLogin();
    bindSelection();
    bindCreator();
    bindLocalInfo();
    addEventListener('resize', fitScenes);
    fitScenes();
    showScreen('login-screen');
    const remembered = G.Session.account?.username;
    if (remembered) el('login-user').value = remembered;
  }

  function fitScenes() {
    const scale = Math.min(innerWidth / 1920, innerHeight / 1080);
    for (const scene of document.querySelectorAll('[data-zircon-scene]')) scene.style.transform = `translate(-50%, -50%) scale(${scale})`;
  }

  function showScreen(id) {
    for (const screen of document.querySelectorAll('.origin-screen')) screen.classList.toggle('is-active', screen.id === id);
    requestAnimationFrame(fitScenes);
  }

  function setMessage(id, message = '', error = false) {
    const node = el(id);
    if (!node) return;
    node.textContent = message;
    node.classList.toggle('is-error', error);
  }

  function toast(message) {
    const node = el('local-toast');
    clearTimeout(toastTimer);
    node.textContent = message;
    node.hidden = false;
    toastTimer = setTimeout(() => { node.hidden = true; }, 2400);
  }

  function bindLocalInfo() {
    for (const button of document.querySelectorAll('[data-local-info]')) button.addEventListener('click', () => toast(button.dataset.localInfo));
  }

  function bindLogin() {
    el('login-form').addEventListener('submit', event => {
      event.preventDefault();
      try {
        G.Session.login(el('login-user').value, el('login-password').value);
        setMessage('login-message');
        renderCharacters();
        showScreen('select-screen');
      } catch (error) { setMessage('login-message', error.message, true); }
    });
    el('login-exit').addEventListener('click', () => toast('En navegador no se puede cerrar el juego automáticamente.'));
  }

  function bindSelection() {
    el('create-open').addEventListener('click', () => { resetCreator(); showScreen('create-screen'); });
    el('select-logout').addEventListener('click', () => { G.Session.logout(); selectedId = null; showScreen('login-screen'); });
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
    el('create-back').addEventListener('click', () => { renderCharacters(); showScreen('select-screen'); });
    for (const button of document.querySelectorAll('[data-class]')) button.addEventListener('click', () => { selectedClass = button.dataset.class; updateCreator(); });
    for (const button of document.querySelectorAll('[data-gender]')) button.addEventListener('click', () => { selectedGender = button.dataset.gender; updateCreator(); });
    el('create-form').addEventListener('submit', event => {
      event.preventDefault();
      try {
        const character = G.Session.createCharacter({ name: el('character-name').value, className: selectedClass, gender: selectedGender });
        selectedId = character.id;
        setMessage('create-message');
        renderCharacters();
        showScreen('select-screen');
      } catch (error) { setMessage('create-message', error.message, true); }
    });
  }

  function resetCreator() {
    selectedClass = 'Warrior'; selectedGender = 'male'; el('character-name').value = ''; setMessage('create-message'); updateCreator();
  }

  function updateCreator() {
    el('creator-preview').src = classImage(selectedClass, selectedGender);
    el('creator-class-name').textContent = selectedClass;
    for (const button of document.querySelectorAll('[data-class]')) button.classList.toggle('is-selected', button.dataset.class === selectedClass);
    for (const button of document.querySelectorAll('[data-gender]')) button.classList.toggle('is-selected', button.dataset.gender === selectedGender);
  }

  function renderCharacters() {
    const list = el('character-list');
    const characters = G.Session.characters.slice(0, 4);
    list.innerHTML = '';
    if (!characters.length) {
      selectedId = null;
      list.innerHTML = '<div class="empty-slot">No hay personajes.<br>Pulse CREAR.</div>';
      updateSelectedCharacter();
      return;
    }
    if (!selectedId || !characters.some(character => character.id === selectedId)) selectedId = G.Session.currentCharacter()?.id || characters[0].id;
    for (const character of characters) {
      const button = document.createElement('button');
      button.type = 'button';
      button.className = 'character-card';
      button.classList.toggle('is-selected', character.id === selectedId);
      button.innerHTML = `<img src="${classImage(character.className, character.gender)}" alt=""><span class="character-card-copy"><strong>${escapeHtml(character.name)}</strong><small>${character.className} · Nivel ${character.level}</small></span>`;
      button.addEventListener('click', () => { selectedId = character.id; G.Session.selectCharacter(character.id); renderCharacters(); });
      list.appendChild(button);
    }
    G.Session.selectCharacter(selectedId);
    updateSelectedCharacter();
  }

  function updateSelectedCharacter() {
    const character = G.Session.characters.find(item => item.id === selectedId) || null;
    el('play-character').disabled = !character;
    el('delete-character').disabled = !character;
    const preview = el('selected-preview');
    preview.src = character ? classImage(character.className, character.gender) : '';
    preview.classList.toggle('is-hidden', !character);
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

  function escapeHtml(value) { return String(value).replace(/[&<>'"]/g, char => ({ '&':'&amp;', '<':'&lt;', '>':'&gt;', "'":'&#39;', '"':'&quot;' })[char]); }
  return Object.freeze({ init });
})();

addEventListener('DOMContentLoaded', () => G.Flow.init(), { once: true });
