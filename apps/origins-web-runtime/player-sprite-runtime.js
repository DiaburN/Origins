export const PLAYER_ASSET_STATUS = Object.freeze({
  Ready: 'READY',
  Partial: 'PARTIAL_BASE_HUMANS',
  Missing: 'BLOCKED_MISSING_ZL',
  Invalid: 'INVALID_ASSET_MANIFEST',
});

export const BASE_HUMAN_LIBRARY_BY_GENDER = Object.freeze({
  Male: 'M_Hum',
  Female: 'WM_Hum',
});

export function resolveBaseHumanLibrary(gender) {
  const library = BASE_HUMAN_LIBRARY_BY_GENDER[gender];
  if (!library) throw new RangeError(`Unsupported Zircon gender for base human body: ${gender}`);
  return library;
}

export class ZirconPlayerSpriteStore {
  constructor({ rootUrl = './assets/player/' } = {}) {
    this.rootUrl = new URL(rootUrl, import.meta.url);
    this.status = PLAYER_ASSET_STATUS.Missing;
    this.master = null;
    this.libraries = new Map();
    this.libraryPromises = new Map();
    this.pages = new Map();
    this.pagePromises = new Map();
    this.frames = new Map();
    this.framePromises = new Map();
  }

  async load() {
    try {
      const masterUrl = new URL('player-assets.json', this.rootUrl);
      const response = await fetch(masterUrl, { cache: 'no-store' });
      if (!response.ok) {
        this.status = PLAYER_ASSET_STATUS.Missing;
        return this.status;
      }
      const master = await response.json();
      if (!master || master.schema !== 'origins.zircon.web-atlas.v1' || !Array.isArray(master.libraries)) {
        this.status = PLAYER_ASSET_STATUS.Invalid;
        return this.status;
      }
      this.master = master;
      this.status = PLAYER_ASSET_STATUS.Ready;
      return this.status;
    } catch {
      this.status = PLAYER_ASSET_STATUS.Missing;
      return this.status;
    }
  }

  hasLibrary(libraryFile) {
    return Boolean(this.master?.libraries?.some(row => row.libraryFile === libraryFile));
  }

  getBaseHumanPairStatus() {
    if (this.status !== PLAYER_ASSET_STATUS.Ready || !this.master) return this.status;
    const male = this.hasLibrary(BASE_HUMAN_LIBRARY_BY_GENDER.Male);
    const female = this.hasLibrary(BASE_HUMAN_LIBRARY_BY_GENDER.Female);
    if (male && female) return PLAYER_ASSET_STATUS.Ready;
    if (male || female) return PLAYER_ASSET_STATUS.Partial;
    return PLAYER_ASSET_STATUS.Missing;
  }

  async getLibrary(libraryFile) {
    if (this.status !== PLAYER_ASSET_STATUS.Ready || !this.master) return null;
    if (this.libraries.has(libraryFile)) return this.libraries.get(libraryFile);
    if (this.libraryPromises.has(libraryFile)) return this.libraryPromises.get(libraryFile);

    const entry = this.master.libraries.find(row => row.libraryFile === libraryFile);
    if (!entry) return null;

    const promise = (async () => {
      const manifestUrl = new URL(entry.manifest, this.rootUrl);
      const response = await fetch(manifestUrl, { cache: 'no-store' });
      if (!response.ok) return null;
      const manifest = await response.json();
      if (!manifest || manifest.libraryFile !== libraryFile || !Array.isArray(manifest.images)) return null;
      manifest.__url = manifestUrl;
      this.libraries.set(libraryFile, manifest);
      return manifest;
    })();

    this.libraryPromises.set(libraryFile, promise);
    try {
      return await promise;
    } finally {
      this.libraryPromises.delete(libraryFile);
    }
  }

  async getFrame(libraryFile, imageIndex) {
    const frameKey = `${libraryFile}:${imageIndex}`;
    if (this.frames.has(frameKey)) return this.frames.get(frameKey);

    const manifest = await this.getLibrary(libraryFile);
    if (!manifest || !Number.isInteger(imageIndex) || imageIndex < 0 || imageIndex >= manifest.images.length) return null;
    const frame = manifest.images[imageIndex];
    if (!frame) return null;

    const pageKey = `${libraryFile}:${frame.page}`;
    const page = await this.getPage(pageKey, new URL(frame.page, manifest.__url));
    if (!page) return null;

    const resolved = Object.freeze({ ...frame, image: page, libraryFile });
    this.frames.set(frameKey, resolved);
    return resolved;
  }

  async getPage(pageKey, pageUrl) {
    if (this.pages.has(pageKey)) return this.pages.get(pageKey);
    if (this.pagePromises.has(pageKey)) return this.pagePromises.get(pageKey);

    const promise = loadImage(pageUrl).then(image => {
      this.pages.set(pageKey, image);
      return image;
    });

    this.pagePromises.set(pageKey, promise);
    try {
      return await promise;
    } finally {
      this.pagePromises.delete(pageKey);
    }
  }

  peekFrame(libraryFile, imageIndex) {
    return this.frames.get(`${libraryFile}:${imageIndex}`) ?? null;
  }

  requestFrame(libraryFile, imageIndex) {
    const key = `${libraryFile}:${imageIndex}`;
    if (this.frames.has(key)) return Promise.resolve(this.frames.get(key));
    if (!this.framePromises.has(key)) {
      this.framePromises.set(key, this.getFrame(libraryFile, imageIndex).finally(() => {
        this.framePromises.delete(key);
      }));
    }
    return this.framePromises.get(key);
  }

  async getBaseHumanFrame(gender, imageIndex) {
    return this.getFrame(resolveBaseHumanLibrary(gender), imageIndex);
  }

  peekBaseHumanFrame(gender, imageIndex) {
    return this.peekFrame(resolveBaseHumanLibrary(gender), imageIndex);
  }

  requestBaseHumanFrame(gender, imageIndex) {
    return this.requestFrame(resolveBaseHumanLibrary(gender), imageIndex);
  }

  async drawFrame(ctx, libraryFile, imageIndex, anchorX, anchorY, options = {}) {
    const frame = await this.getFrame(libraryFile, imageIndex);
    if (!frame) return false;
    drawResolvedFrame(ctx, frame, anchorX, anchorY, options);
    return true;
  }

  async drawBaseHumanFrame(ctx, gender, imageIndex, anchorX, anchorY, options = {}) {
    return this.drawFrame(ctx, resolveBaseHumanLibrary(gender), imageIndex, anchorX, anchorY, options);
  }
}

export function drawResolvedFrame(ctx, frame, anchorX, anchorY, options = {}) {
  const opacity = Number.isFinite(options.opacity) ? options.opacity : 1;
  ctx.save();
  ctx.globalAlpha *= opacity;
  ctx.imageSmoothingEnabled = false;
  ctx.drawImage(
    frame.image,
    frame.x,
    frame.y,
    frame.width,
    frame.height,
    Math.round(anchorX + frame.offsetX),
    Math.round(anchorY + frame.offsetY),
    frame.width,
    frame.height,
  );
  ctx.restore();
}

function loadImage(url) {
  return new Promise((resolve, reject) => {
    const image = new Image();
    image.decoding = 'async';
    image.onload = () => resolve(image);
    image.onerror = () => reject(new Error(`Failed to load Zircon atlas page: ${url}`));
    image.src = url.href;
  });
}
