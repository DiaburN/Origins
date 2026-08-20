export const PLAYER_ASSET_STATUS = Object.freeze({
  Ready: 'READY',
  Missing: 'BLOCKED_MISSING_ZL',
  Invalid: 'INVALID_ASSET_MANIFEST',
});

export class ZirconPlayerSpriteStore {
  constructor({ rootUrl = './assets/player/' } = {}) {
    this.rootUrl = new URL(rootUrl, import.meta.url);
    this.status = PLAYER_ASSET_STATUS.Missing;
    this.master = null;
    this.libraries = new Map();
    this.pages = new Map();
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

  async getLibrary(libraryFile) {
    if (this.status !== PLAYER_ASSET_STATUS.Ready || !this.master) return null;
    if (this.libraries.has(libraryFile)) return this.libraries.get(libraryFile);

    const entry = this.master.libraries.find(row => row.libraryFile === libraryFile);
    if (!entry) return null;
    const manifestUrl = new URL(entry.manifest, this.rootUrl);
    const response = await fetch(manifestUrl, { cache: 'no-store' });
    if (!response.ok) return null;
    const manifest = await response.json();
    if (!manifest || manifest.libraryFile !== libraryFile || !Array.isArray(manifest.images)) return null;
    manifest.__url = manifestUrl;
    this.libraries.set(libraryFile, manifest);
    return manifest;
  }

  async getFrame(libraryFile, imageIndex) {
    const manifest = await this.getLibrary(libraryFile);
    if (!manifest || !Number.isInteger(imageIndex) || imageIndex < 0 || imageIndex >= manifest.images.length) return null;
    const frame = manifest.images[imageIndex];
    if (!frame) return null;

    const pageKey = `${libraryFile}:${frame.page}`;
    let page = this.pages.get(pageKey);
    if (!page) {
      page = await loadImage(new URL(frame.page, manifest.__url));
      this.pages.set(pageKey, page);
    }
    return Object.freeze({ ...frame, image: page, libraryFile });
  }

  async drawFrame(ctx, libraryFile, imageIndex, anchorX, anchorY, options = {}) {
    const frame = await this.getFrame(libraryFile, imageIndex);
    if (!frame) return false;
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
    return true;
  }
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
