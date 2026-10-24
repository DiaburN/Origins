window.G = window.G || {};

G.CharacterAppearance = (() => {
  let imagePromise = null;

  function assets() {
    return G.CharacterPaperdollAssets || { ready: false, frames: {} };
  }

  function ready() {
    const a = assets();
    if (!a.ready || !a.sheet) return Promise.resolve(null);
    if (imagePromise) return imagePromise;
    imagePromise = new Promise((resolve, reject) => {
      const image = new Image();
      image.onload = () => resolve(image);
      image.onerror = reject;
      image.src = a.sheet;
    });
    return imagePromise;
  }

  function frame(index) {
    return assets().frames?.[String(index)] || null;
  }

  async function addProgUseLayer(origin, index, className) {
    const image = await ready();
    const f = frame(index);
    if (!origin || !image || !f) return null;

    const canvas = document.createElement('canvas');
    canvas.width = f.w;
    canvas.height = f.h;
    canvas.className = `character-appearance-layer ${className || ''}`.trim();
    canvas.style.position = 'absolute';
    canvas.style.left = `${f.ox}px`;
    canvas.style.top = `${f.oy}px`;
    canvas.style.width = `${f.w}px`;
    canvas.style.height = `${f.h}px`;
    canvas.style.imageRendering = 'pixelated';
    canvas.style.pointerEvents = 'none';

    const ctx = canvas.getContext('2d');
    ctx.imageSmoothingEnabled = false;
    ctx.drawImage(image, f.x, f.y, f.w, f.h, 0, 0, f.w, f.h);
    origin.appendChild(canvas);
    return canvas;
  }

  function hairIndex(character) {
    const a = assets();
    const hairType = Math.max(0, Number(character?.hairType ?? 0) || 0);
    if (!hairType) return null;

    const gender = String(character?.gender || 'male').toLowerCase();
    const className = String(character?.className || '').toLowerCase();
    const hair = a.hair || {};
    let base;
    if (className === 'assassin') {
      base = gender === 'female' ? hair.assassinFemaleBase : hair.assassinMaleBase;
    } else {
      base = gender === 'female' ? hair.standardFemaleBase : hair.standardMaleBase;
    }
    return Number.isFinite(base) ? base + hairType - 1 : null;
  }

  function needsAssassinFemalePreLayer(character, equipment) {
    const className = String(character?.className || '').toLowerCase();
    const gender = String(character?.gender || 'male').toLowerCase();
    const hairType = Number(character?.hairType ?? 0) || 0;
    const hasHelmet = Boolean(equipment?.helmet);
    const hasCostume = Boolean(equipment?.costume);
    return className === 'assassin' && gender === 'female' && hairType === 1 && !hasHelmet && !hasCostume;
  }

  async function render(origin, character, equipment = null) {
    if (!origin) return;
    origin.replaceChildren();

    const a = assets();
    if (!a.ready) {
      origin.dataset.paperdollState = 'missing-proguse';
      return;
    }

    origin.dataset.paperdollState = 'ready';
    const gender = String(character?.gender || 'male').toLowerCase();

    // Exact CharacterDialog order: Assassin female HairType 1 special ProgUse
    // layer is drawn before the base body when no helmet is equipped.
    if (needsAssassinFemalePreLayer(character, equipment)) {
      const special = a.hair?.assassinFemaleSpecial;
      if (special != null) await addProgUseLayer(origin, special, 'paperdoll-assassin-female-prelayer');
    }

    const hasCostume = Boolean(equipment?.costume);
    if (!hasCostume) {
      const baseIndex = gender === 'female' ? a.baseBody?.female : a.baseBody?.male;
      await addProgUseLayer(origin, baseIndex, 'paperdoll-base-body');
    }

    // Equipment layers are intentionally not faked. Zircon uses Equip.Zl image
    // indices from the actual equipped ClientUserItems. When that runtime is
    // available, armour/costume -> weapon -> shield -> helmet will be inserted
    // here in the verified CharacterDialog order.

    if (!hasCostume && !equipment?.helmet) {
      const hair = hairIndex(character);
      if (hair != null) await addProgUseLayer(origin, hair, 'paperdoll-hair');
    }
  }

  return Object.freeze({ ready, render, addProgUseLayer, hairIndex });
})();
